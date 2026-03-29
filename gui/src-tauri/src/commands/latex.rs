use serde::Serialize;
use std::process::Command;

#[derive(Serialize)]
pub struct CompileResult {
    pub success: bool,
    pub output: String,
    pub pdf_path: Option<String>,
}

#[tauri::command]
pub fn compile_latex(project_dir: String) -> Result<CompileResult, String> {
    let output = Command::new("latexmk")
        .args(["-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"])
        .current_dir(&project_dir)
        .output()
        .map_err(|e| format!("Failed to run latexmk: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = format!("{}\n{}", stdout, stderr);

    let pdf_path = if output.status.success() {
        let pdf = std::path::Path::new(&project_dir).join("main.pdf");
        if pdf.exists() {
            Some(pdf.to_string_lossy().to_string())
        } else {
            None
        }
    } else {
        None
    };

    Ok(CompileResult {
        success: output.status.success(),
        output: combined,
        pdf_path,
    })
}
