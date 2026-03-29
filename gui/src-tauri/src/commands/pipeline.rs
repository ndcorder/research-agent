use notify::{Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::{AppHandle, Emitter, Manager};

use super::terminal::{spawn_terminal_inner, write_terminal_inner, TerminalState};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum PipelineAction {
    TargetedResearch,
    BatchResolve,
}

#[derive(Debug, Deserialize)]
pub struct PipelineActionArgs {
    pub claim_ids: Vec<String>,
    pub context: Option<String>,
}

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct EvidenceUpdatedEvent {
    pub changed_paths: Vec<String>,
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

pub struct EvidenceWatcherState {
    watcher: Mutex<Option<RecommendedWatcher>>,
}

impl Default for EvidenceWatcherState {
    fn default() -> Self {
        Self {
            watcher: Mutex::new(None),
        }
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn build_slash_command(action: &PipelineAction, args: &PipelineActionArgs) -> String {
    let ids = args.claim_ids.join(",");
    match action {
        PipelineAction::TargetedResearch => {
            let mut cmd = format!(
                "claude --dangerously-skip-permissions \"/targeted-research --claims '{}'",
                ids
            );
            if let Some(ctx) = &args.context {
                let escaped = ctx.replace('\'', "'\\''");
                cmd.push_str(&format!(" --context '{}'", escaped));
            }
            cmd.push_str("\"\n");
            cmd
        }
        PipelineAction::BatchResolve => {
            let mut cmd = format!(
                "claude --dangerously-skip-permissions \"/targeted-research --claims '{}' --batch",
                ids
            );
            if let Some(ctx) = &args.context {
                let escaped = ctx.replace('\'', "'\\''");
                cmd.push_str(&format!(" --context '{}'", escaped));
            }
            cmd.push_str("\"\n");
            cmd
        }
    }
}

/// Returns true if the path is one we care about for evidence updates.
fn is_evidence_path(path: &Path) -> bool {
    let s = path.to_string_lossy();
    if s.ends_with(".paper-state.json") {
        return true;
    }
    if s.contains("/research/sources/") || s.contains("\\research\\sources\\") {
        return true;
    }
    if s.contains("claims_matrix") {
        return true;
    }
    false
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

#[tauri::command]
pub fn run_pipeline_action(
    app: AppHandle,
    project_dir: String,
    action: PipelineAction,
    args: PipelineActionArgs,
) -> Result<u32, String> {
    let terminal_state = app.state::<TerminalState>();
    let evidence_state = app.state::<EvidenceWatcherState>();

    // 1. Spawn a terminal in the project directory
    let id = spawn_terminal_inner(&app, &terminal_state, &project_dir)?;

    // 2. Build and send the slash command
    let cmd = build_slash_command(&action, &args);
    write_terminal_inner(&terminal_state, id, &cmd)?;

    // 3. Set up debounced evidence file watcher
    start_evidence_watcher(&app, &evidence_state, &project_dir)?;

    Ok(id)
}

fn start_evidence_watcher(
    app: &AppHandle,
    state: &EvidenceWatcherState,
    project_dir: &str,
) -> Result<(), String> {
    // Stop any existing watcher first
    {
        let mut guard = state.watcher.lock().unwrap();
        *guard = None;
    }

    let app_clone = app.clone();
    let last_emit = Arc::new(Mutex::new(Instant::now()));
    let pending_paths: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(Vec::new()));

    let last_emit_c = Arc::clone(&last_emit);
    let pending_c = Arc::clone(&pending_paths);
    let trailing_scheduled = Arc::new(AtomicBool::new(false));
    let trailing_scheduled_c = Arc::clone(&trailing_scheduled);

    let watcher = notify::recommended_watcher(move |res: Result<Event, notify::Error>| {
        if let Ok(event) = res {
            // Only care about create/modify events
            match event.kind {
                EventKind::Create(_) | EventKind::Modify(_) => {}
                _ => return,
            }

            let mut dominated = false;
            {
                let mut paths = pending_c.lock().unwrap();
                for p in &event.paths {
                    if is_evidence_path(p) {
                        let s = p.to_string_lossy().to_string();
                        if !paths.contains(&s) {
                            paths.push(s);
                        }
                        dominated = true;
                    }
                }
            }

            if !dominated {
                return;
            }

            // Debounce: only emit if 2+ seconds since last emit
            let mut last = last_emit_c.lock().unwrap();
            if last.elapsed() >= Duration::from_secs(2) {
                *last = Instant::now();
                let mut paths = pending_c.lock().unwrap();
                if !paths.is_empty() {
                    let changed: Vec<String> = paths.drain(..).collect();
                    let _ = app_clone.emit(
                        "evidence-updated",
                        EvidenceUpdatedEvent {
                            changed_paths: changed,
                        },
                    );
                }
            } else if !trailing_scheduled_c.swap(true, Ordering::SeqCst) {
                // Schedule exactly one trailing-edge flush
                let app_trail = app_clone.clone();
                let pending_trail = Arc::clone(&pending_c);
                let last_trail = Arc::clone(&last_emit_c);
                let flag = Arc::clone(&trailing_scheduled_c);
                let delay = Duration::from_secs(2) - last.elapsed();
                std::thread::spawn(move || {
                    std::thread::sleep(delay);
                    flag.store(false, Ordering::SeqCst);
                    let mut last = last_trail.lock().unwrap();
                    if last.elapsed() >= Duration::from_secs(2) {
                        *last = Instant::now();
                        let mut paths = pending_trail.lock().unwrap();
                        if !paths.is_empty() {
                            let changed: Vec<String> = paths.drain(..).collect();
                            let _ = app_trail.emit(
                                "evidence-updated",
                                EvidenceUpdatedEvent {
                                    changed_paths: changed,
                                },
                            );
                        }
                    }
                });
            }
        }
    })
    .map_err(|e| format!("Failed to create evidence watcher: {}", e))?;

    let mut guard = state.watcher.lock().unwrap();
    *guard = Some(watcher);

    if let Some(ref mut w) = *guard {
        w.watch(Path::new(project_dir), RecursiveMode::Recursive)
            .map_err(|e| format!("Failed to watch project dir: {}", e))?;
    }

    Ok(())
}

#[tauri::command]
pub fn stop_evidence_watcher(app: AppHandle) -> Result<(), String> {
    let state = app.state::<EvidenceWatcherState>();
    let mut guard = state.watcher.lock().unwrap();
    *guard = None;
    Ok(())
}
