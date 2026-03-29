use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Serialize, Deserialize)]
pub struct PaperConfig {
    pub topic: Option<String>,
    pub venue: Option<String>,
    pub depth: Option<String>,
}

#[derive(Serialize)]
pub struct ProjectInfo {
    pub path: String,
    pub config: PaperConfig,
    pub has_state: bool,
    pub source_count: usize,
    pub has_tex: bool,
}

#[tauri::command]
pub fn read_paper_state(project_dir: String) -> Result<serde_json::Value, String> {
    let state_path = Path::new(&project_dir).join(".paper-state.json");
    if !state_path.exists() {
        return Ok(serde_json::json!({"current_stage": 0, "stages": {}}));
    }

    let content =
        fs::read_to_string(&state_path).map_err(|e| format!("Failed to read state: {}", e))?;

    serde_json::from_str(&content).map_err(|e| format!("Failed to parse state: {}", e))
}

#[tauri::command]
pub fn validate_paper_project(path: String) -> Result<ProjectInfo, String> {
    let dir = Path::new(&path);
    let config_path = dir.join(".paper.json");

    if !config_path.exists() {
        return Err("Not a paper project: .paper.json not found".to_string());
    }

    let config_str =
        fs::read_to_string(&config_path).map_err(|e| format!("Failed to read config: {}", e))?;
    let config: PaperConfig =
        serde_json::from_str(&config_str).map_err(|e| format!("Failed to parse config: {}", e))?;

    let has_state = dir.join(".paper-state.json").exists();
    let has_tex = dir.join("main.tex").exists();

    let source_count = dir
        .join("research")
        .join("sources")
        .read_dir()
        .map(|entries| {
            entries
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .extension()
                        .map_or(false, |ext| ext == "md")
                })
                .count()
        })
        .unwrap_or(0);

    Ok(ProjectInfo {
        path: path.clone(),
        config,
        has_state,
        source_count,
        has_tex,
    })
}

#[tauri::command]
pub fn read_paper_config(project_dir: String) -> Result<PaperConfig, String> {
    let config_path = Path::new(&project_dir).join(".paper.json");
    let content =
        fs::read_to_string(&config_path).map_err(|e| format!("Failed to read config: {}", e))?;
    serde_json::from_str(&content).map_err(|e| format!("Failed to parse config: {}", e))
}

#[tauri::command]
pub fn get_recent_projects() -> Result<Vec<String>, String> {
    let config_dir = dirs_config_path();
    let recent_path = config_dir.join("recent_projects.json");
    if !recent_path.exists() {
        return Ok(Vec::new());
    }
    let content = fs::read_to_string(&recent_path).map_err(|e| e.to_string())?;
    serde_json::from_str(&content).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn add_recent_project(path: String) -> Result<(), String> {
    let config_dir = dirs_config_path();
    fs::create_dir_all(&config_dir).map_err(|e| e.to_string())?;

    let recent_path = config_dir.join("recent_projects.json");
    let mut projects: Vec<String> = if recent_path.exists() {
        let content = fs::read_to_string(&recent_path).unwrap_or_else(|_| "[]".to_string());
        serde_json::from_str(&content).unwrap_or_default()
    } else {
        Vec::new()
    };

    // Remove if already exists, then prepend
    projects.retain(|p| p != &path);
    projects.insert(0, path);
    projects.truncate(10); // Keep last 10

    let content = serde_json::to_string_pretty(&projects).map_err(|e| e.to_string())?;
    fs::write(&recent_path, content).map_err(|e| e.to_string())
}

fn dirs_config_path() -> std::path::PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join("research-agent-gui")
}
