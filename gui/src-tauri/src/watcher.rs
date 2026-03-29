use notify::{Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use serde::Serialize;
use std::path::Path;
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager};

pub struct WatcherState {
    watcher: Mutex<Option<RecommendedWatcher>>,
}

impl Default for WatcherState {
    fn default() -> Self {
        Self {
            watcher: Mutex::new(None),
        }
    }
}

#[derive(Serialize, Clone)]
pub struct FileChangeEvent {
    pub path: String,
    pub kind: String,
}

fn event_kind_to_string(kind: &EventKind) -> &'static str {
    match kind {
        EventKind::Create(_) => "created",
        EventKind::Modify(_) => "modified",
        EventKind::Remove(_) => "removed",
        _ => "other",
    }
}

#[tauri::command]
pub fn start_watching(app: AppHandle, path: String) -> Result<(), String> {
    let state = app.state::<WatcherState>();
    let app_clone = app.clone();

    let watcher = notify::recommended_watcher(move |res: Result<Event, notify::Error>| {
        if let Ok(event) = res {
            let kind = event_kind_to_string(&event.kind);
            for path in &event.paths {
                let path_str = path.to_string_lossy().to_string();
                // Skip hidden files and common temp files
                if path_str.contains("/.") || path_str.ends_with("~") || path_str.ends_with(".swp")
                {
                    continue;
                }
                let _ = app_clone.emit(
                    "file-change",
                    FileChangeEvent {
                        path: path_str,
                        kind: kind.to_string(),
                    },
                );
            }
        }
    })
    .map_err(|e| format!("Failed to create watcher: {}", e))?;

    let mut guard = state.watcher.lock().unwrap();
    *guard = Some(watcher);

    if let Some(ref mut w) = *guard {
        w.watch(Path::new(&path), RecursiveMode::Recursive)
            .map_err(|e| format!("Failed to watch path: {}", e))?;
    }

    Ok(())
}

#[tauri::command]
pub fn stop_watching(app: AppHandle) -> Result<(), String> {
    let state = app.state::<WatcherState>();
    let mut guard = state.watcher.lock().unwrap();
    *guard = None;
    Ok(())
}
