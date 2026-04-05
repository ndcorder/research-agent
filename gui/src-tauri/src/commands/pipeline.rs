use notify::{Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use serde::{Deserialize, Serialize};
use std::fs;
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
    WritePaper,
    Auto,
    Score,
}

#[derive(Debug, Deserialize)]
pub struct PipelineActionArgs {
    pub claim_ids: Vec<String>,
    pub context: Option<String>,
    pub auto_iterations: Option<u32>,
    pub topic: Option<String>,
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

fn shell_single_quote(value: &str) -> String {
    format!("'{}'", value.replace('\'', "'\\''"))
}

fn project_runtime(project_dir: &str) -> String {
    let config_path = Path::new(project_dir).join(".paper.json");
    let Ok(content) = fs::read_to_string(config_path) else {
        return "claude".to_string();
    };
    let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) else {
        return "claude".to_string();
    };
    json.get("runtime")
        .and_then(|value| value.as_str())
        .unwrap_or("claude")
        .to_string()
}

fn build_runtime_command(
    project_dir: &str,
    action: &PipelineAction,
    args: &PipelineActionArgs,
) -> String {
    let ids = args.claim_ids.join(",");
    let runtime = project_runtime(project_dir);

    if runtime == "codex" {
        return match action {
            PipelineAction::TargetedResearch | PipelineAction::BatchResolve => {
                let mut cmd = format!(
                    "scripts/run-paper-command targeted-research --claims {}",
                    shell_single_quote(&ids)
                );
                if let Some(ctx) = &args.context {
                    cmd.push_str(&format!(" --context {}", shell_single_quote(ctx)));
                }
                if matches!(action, PipelineAction::BatchResolve) {
                    cmd.push_str(" --batch");
                }
                cmd.push('\n');
                cmd
            }
            PipelineAction::WritePaper => {
                "scripts/run-paper-command write-paper\n".to_string()
            }
            PipelineAction::Auto => {
                let n = args.auto_iterations.unwrap_or(3);
                format!("scripts/run-paper-command auto {n}\n")
            }
            PipelineAction::Score => {
                "python scripts/quality.py score --format json --project .\n".to_string()
            }
        };
    }

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
        PipelineAction::WritePaper => {
            "claude --dangerously-skip-permissions \"/write-paper\"\n".to_string()
        }
        PipelineAction::Auto => {
            let n = args.auto_iterations.unwrap_or(3);
            format!("claude --dangerously-skip-permissions \"/auto {n}\"\n")
        }
        PipelineAction::Score => {
            "python scripts/quality.py score --format json --project .\n".to_string()
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
    let cmd = build_runtime_command(&project_dir, &action, &args);
    write_terminal_inner(&terminal_state, id, &cmd)?;

    // 3. Set up debounced evidence file watcher
    start_evidence_watcher(&app, &evidence_state, &project_dir)?;

    Ok(id)
}

#[cfg(test)]
mod tests {
    use super::{build_runtime_command, PipelineAction, PipelineActionArgs};
    use std::fs;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_project_dir(runtime: &str) -> PathBuf {
        let mut dir = std::env::temp_dir();
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        dir.push(format!("research-agent-runtime-test-{stamp}"));
        fs::create_dir_all(&dir).unwrap();
        fs::write(
            dir.join(".paper.json"),
            format!(r#"{{"runtime":"{runtime}"}}"#),
        )
        .unwrap();
        dir
    }

    #[test]
    fn builds_claude_targeted_research_command() {
        let dir = temp_project_dir("claude");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::TargetedResearch,
            &PipelineActionArgs {
                claim_ids: vec!["C1".into(), "C2".into()],
                context: Some("extra context".into()),
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("claude --dangerously-skip-permissions"));
        assert!(cmd.contains("/targeted-research --claims 'C1,C2'"));
        assert!(cmd.contains("--context 'extra context'"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_claude_batch_resolve_command() {
        let dir = temp_project_dir("claude");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::BatchResolve,
            &PipelineActionArgs {
                claim_ids: vec!["C9".into()],
                context: None,
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("claude --dangerously-skip-permissions"));
        assert!(cmd.contains("/targeted-research --claims 'C9' --batch"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_codex_targeted_research_command() {
        let dir = temp_project_dir("codex");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::BatchResolve,
            &PipelineActionArgs {
                claim_ids: vec!["C7".into()],
                context: Some("review unresolved claim".into()),
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("scripts/run-paper-command targeted-research"));
        assert!(cmd.contains("--claims 'C7'"));
        assert!(cmd.contains("--context 'review unresolved claim'"));
        assert!(cmd.contains("--batch"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_codex_targeted_research_non_batch_command() {
        let dir = temp_project_dir("codex");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::TargetedResearch,
            &PipelineActionArgs {
                claim_ids: vec!["C3".into(), "C4".into()],
                context: None,
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("scripts/run-paper-command targeted-research"));
        assert!(cmd.contains("--claims 'C3,C4'"));
        assert!(!cmd.contains("--batch"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_claude_write_paper_command() {
        let dir = temp_project_dir("claude");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::WritePaper,
            &PipelineActionArgs {
                claim_ids: vec![],
                context: None,
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("claude --dangerously-skip-permissions"));
        assert!(cmd.contains("/write-paper"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_claude_auto_command() {
        let dir = temp_project_dir("claude");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::Auto,
            &PipelineActionArgs {
                claim_ids: vec![],
                context: None,
                auto_iterations: Some(5),
                topic: None,
            },
        );
        assert!(cmd.contains("claude --dangerously-skip-permissions"));
        assert!(cmd.contains("/auto 5"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_codex_write_paper_command() {
        let dir = temp_project_dir("codex");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::WritePaper,
            &PipelineActionArgs {
                claim_ids: vec![],
                context: None,
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("scripts/run-paper-command write-paper"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_codex_auto_command() {
        let dir = temp_project_dir("codex");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::Auto,
            &PipelineActionArgs {
                claim_ids: vec![],
                context: None,
                auto_iterations: Some(3),
                topic: None,
            },
        );
        assert!(cmd.contains("scripts/run-paper-command auto 3"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn builds_score_command() {
        let dir = temp_project_dir("claude");
        let cmd = build_runtime_command(
            dir.to_str().unwrap(),
            &PipelineAction::Score,
            &PipelineActionArgs {
                claim_ids: vec![],
                context: None,
                auto_iterations: None,
                topic: None,
            },
        );
        assert!(cmd.contains("python scripts/quality.py score"));
        assert!(cmd.contains("--format json"));
        fs::remove_dir_all(dir).unwrap();
    }
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
