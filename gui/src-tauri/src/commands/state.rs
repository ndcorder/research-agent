use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::process::Command;

#[derive(Serialize, Deserialize)]
pub struct PaperConfig {
    pub topic: Option<String>,
    pub venue: Option<String>,
    pub depth: Option<String>,
    pub runtime: Option<String>,
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

#[derive(Serialize)]
pub struct VenueInfo {
    pub id: String,
    pub name: String,
}

#[tauri::command]
pub fn list_venues(research_agent_dir: String) -> Result<Vec<VenueInfo>, String> {
    let venues_dir = Path::new(&research_agent_dir)
        .join("template")
        .join("venues");

    if !venues_dir.exists() {
        return Err(format!("Venues directory not found: {}", venues_dir.display()));
    }

    let mut venues = Vec::new();
    let entries = fs::read_dir(&venues_dir).map_err(|e| format!("Failed to read venues: {}", e))?;

    for entry in entries {
        let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let path = entry.path();
        if path.extension().map_or(false, |ext| ext == "json") {
            let id = path
                .file_stem()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string();
            // Capitalize the first letter for display name
            let name = {
                let mut chars = id.chars();
                match chars.next() {
                    None => String::new(),
                    Some(c) => c.to_uppercase().collect::<String>() + chars.as_str(),
                }
            };
            venues.push(VenueInfo { id, name });
        }
    }

    venues.sort_by(|a, b| a.id.cmp(&b.id));
    Ok(venues)
}

#[tauri::command]
pub fn create_paper(
    research_agent_dir: String,
    directory: String,
    topic: String,
    venue: String,
    deep: bool,
    runtime: String,
) -> Result<String, String> {
    let script_path = Path::new(&research_agent_dir).join("create-paper");

    if !script_path.exists() {
        return Err(format!(
            "create-paper script not found at {}",
            script_path.display()
        ));
    }

    let mut cmd = Command::new(&script_path);
    cmd.arg(&directory);

    if !topic.is_empty() {
        cmd.arg(&topic);
    }

    cmd.arg("--venue").arg(&venue);
    cmd.arg("--runtime").arg(&runtime);

    if deep {
        cmd.arg("--deep");
    }

    let output = cmd
        .output()
        .map_err(|e| format!("Failed to run create-paper: {}", e))?;

    if output.status.success() {
        // Resolve the absolute path of the created directory
        let created = Path::new(&directory);
        let abs_path = if created.is_absolute() {
            created.to_path_buf()
        } else {
            std::env::current_dir()
                .map_err(|e| format!("Failed to get cwd: {}", e))?
                .join(created)
        };
        let canonical = fs::canonicalize(&abs_path)
            .unwrap_or(abs_path);
        Ok(canonical.to_string_lossy().to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        Err(format!(
            "create-paper failed:\n{}{}",
            stderr,
            if stdout.is_empty() {
                String::new()
            } else {
                format!("\n{}", stdout)
            }
        ))
    }
}

#[tauri::command]
pub fn get_research_agent_dir() -> Result<String, String> {
    // Walk up from the current executable looking for a directory that contains create-paper
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("Failed to get current exe: {}", e))?;

    let mut dir = exe_path.parent();
    while let Some(d) = dir {
        if d.join("create-paper").exists() {
            return Ok(d.to_string_lossy().to_string());
        }
        dir = d.parent();
    }

    Err("Could not find research-agent directory (no ancestor contains create-paper)".to_string())
}
