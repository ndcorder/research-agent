use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Serialize, Deserialize)]
pub struct FileEntry {
    pub name: String,
    pub path: String,
    pub is_dir: bool,
    pub size: u64,
}

#[derive(Serialize, Deserialize)]
pub struct SourceMeta {
    pub key: String,
    pub path: String,
    pub title: Option<String>,
    pub authors: Option<Vec<String>>,
    pub year: Option<u32>,
    pub status: Option<String>,
    pub tags: Option<Vec<String>>,
    pub evidence_for: Option<Vec<String>>,
    pub url: Option<String>,
    pub doi: Option<String>,
    pub access_level: Option<String>,
    pub source_type: Option<String>,
}

#[tauri::command]
pub fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path).map_err(|e| format!("Failed to read {}: {}", path, e))
}

#[tauri::command]
pub fn write_file(path: String, content: String) -> Result<(), String> {
    fs::write(&path, &content).map_err(|e| format!("Failed to write {}: {}", path, e))
}

#[tauri::command]
pub fn list_directory(path: String) -> Result<Vec<FileEntry>, String> {
    let entries = fs::read_dir(&path).map_err(|e| format!("Failed to read dir {}: {}", path, e))?;

    let mut result = Vec::new();
    for entry in entries.flatten() {
        let metadata = entry.metadata().unwrap_or_else(|_| {
            fs::metadata(entry.path()).expect("failed to get metadata")
        });
        let name = entry.file_name().to_string_lossy().to_string();
        if name.starts_with('.') {
            continue;
        }
        result.push(FileEntry {
            name,
            path: entry.path().to_string_lossy().to_string(),
            is_dir: metadata.is_dir(),
            size: metadata.len(),
        });
    }
    result.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(result)
}

#[tauri::command]
pub fn list_sources(project_dir: String) -> Result<Vec<SourceMeta>, String> {
    let sources_dir = Path::new(&project_dir).join("research").join("sources");
    if !sources_dir.exists() {
        return Ok(Vec::new());
    }

    let mut sources = Vec::new();
    let entries =
        fs::read_dir(&sources_dir).map_err(|e| format!("Failed to read sources: {}", e))?;

    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().map_or(true, |ext| ext != "md") {
            continue;
        }

        let key = path
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();
        let content = fs::read_to_string(&path).unwrap_or_default();
        let meta = parse_source_frontmatter(&content);

        sources.push(SourceMeta {
            key,
            path: path.to_string_lossy().to_string(),
            title: meta.title,
            authors: meta.authors,
            year: meta.year,
            status: meta.status,
            tags: meta.tags,
            evidence_for: meta.evidence_for,
            url: meta.url,
            doi: meta.doi,
            access_level: meta.access_level,
            source_type: meta.source_type,
        });
    }

    sources.sort_by(|a, b| a.key.cmp(&b.key));
    Ok(sources)
}

#[tauri::command]
pub fn list_claims(project_dir: String) -> Result<Vec<serde_json::Value>, String> {
    // First try individual claim files in research/claims/
    let claims_dir = Path::new(&project_dir).join("research").join("claims");
    if claims_dir.exists() {
        let mut claims = Vec::new();
        if let Ok(entries) = fs::read_dir(&claims_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().map_or(true, |ext| ext != "md") {
                    continue;
                }
                let content = fs::read_to_string(&path).unwrap_or_default();
                if let Some(fm) = extract_frontmatter(&content) {
                    if let Ok(value) =
                        serde_json::from_str::<serde_json::Value>(&yaml_to_json(&fm))
                    {
                        claims.push(value);
                    }
                }
            }
        }
        if !claims.is_empty() {
            return Ok(claims);
        }
    }

    // Fall back to parsing claims_matrix.md table
    let matrix_path = Path::new(&project_dir)
        .join("research")
        .join("claims_matrix.md");
    if !matrix_path.exists() {
        return Ok(Vec::new());
    }

    let content =
        fs::read_to_string(&matrix_path).map_err(|e| format!("Failed to read claims: {}", e))?;

    let mut claims = Vec::new();
    for line in content.lines() {
        let trimmed = line.trim();
        // Skip non-table lines, header, and separator
        if !trimmed.starts_with('|') || trimmed.starts_with("| #") || trimmed.starts_with("|-") {
            continue;
        }

        let cols: Vec<&str> = trimmed.split('|').collect();
        // Expect at least 12 columns (including empty first/last from split)
        if cols.len() < 12 {
            continue;
        }

        let id = cols[1].trim().to_string();
        if id.is_empty() || !id.starts_with('C') {
            continue;
        }

        let tier = cols[2].trim().to_string();
        let statement = cols[3].trim().to_string();
        let evidence_str = cols[4].trim().to_string();
        let score: f64 = cols[8].trim().parse().unwrap_or(0.0);
        let strength = cols[9].trim().to_string();
        let section = cols[10].trim().to_string();
        let status = cols.get(11).map(|s| s.trim().to_string()).unwrap_or_default();

        // Count evidence sources
        let evidence_count = evidence_str.split(',').count();

        // Map strength to confidence
        let confidence = match strength.as_str() {
            "STRONG" => "high",
            "MODERATE" => "medium",
            "WEAK" => "low",
            "CRITICAL" => "critical",
            _ => "unknown",
        };

        let warrant = cols.get(5).map(|s| s.trim().to_string()).unwrap_or_default();
        let qualifier = cols.get(6).map(|s| s.trim().to_string()).unwrap_or_default();
        let rebuttal = cols.get(7).map(|s| s.trim().to_string()).unwrap_or_default();

        claims.push(serde_json::json!({
            "id": id,
            "statement": statement,
            "type": tier,
            "confidence": confidence,
            "evidence_density": evidence_count,
            "section": section,
            "score": score,
            "strength": strength,
            "status": status,
            "evidence_sources": evidence_str,
            "warrant": warrant,
            "qualifier": qualifier,
            "rebuttal": rebuttal,
        }));
    }

    Ok(claims)
}

#[tauri::command]
pub fn update_source_status(path: String, status: String) -> Result<(), String> {
    let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let updated = update_frontmatter_field(&content, "status", &status);
    fs::write(&path, updated).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn append_human_notes(path: String, note: String) -> Result<(), String> {
    let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;

    let updated = if content.contains("## Human Notes") {
        let parts: Vec<&str> = content.splitn(2, "## Human Notes").collect();
        if parts.len() == 2 {
            format!("{}## Human Notes\n{}\n{}", parts[0], note, parts[1].trim_start_matches('\n'))
        } else {
            format!("{}\n\n## Human Notes\n\n{}\n", content, note)
        }
    } else {
        format!("{}\n\n## Human Notes\n\n{}\n", content, note)
    };

    fs::write(&path, updated).map_err(|e| e.to_string())
}

#[derive(Serialize)]
pub struct SearchResult {
    pub source_key: String,
    pub source_title: Option<String>,
    pub line_number: usize,
    pub line_content: String,
    pub match_start: usize,
    pub match_end: usize,
}

#[tauri::command]
pub fn search_sources(project_dir: String, query: String) -> Result<Vec<SearchResult>, String> {
    let sources_dir = Path::new(&project_dir).join("research").join("sources");
    if !sources_dir.exists() || query.is_empty() {
        return Ok(Vec::new());
    }

    let query_lower = query.to_lowercase();
    let mut results = Vec::new();

    let entries =
        fs::read_dir(&sources_dir).map_err(|e| format!("Failed to read sources: {}", e))?;

    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().map_or(true, |ext| ext != "md") {
            continue;
        }

        let key = path
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();
        let content = match fs::read_to_string(&path) {
            Ok(c) => c,
            Err(_) => continue,
        };

        let meta = parse_source_frontmatter(&content);

        for (i, line) in content.lines().enumerate() {
            let line_lower = line.to_lowercase();
            if let Some(pos) = line_lower.find(&query_lower) {
                results.push(SearchResult {
                    source_key: key.clone(),
                    source_title: meta.title.clone(),
                    line_number: i + 1,
                    line_content: line.to_string(),
                    match_start: pos,
                    match_end: pos + query.len(),
                });
                if results.len() >= 100 {
                    return Ok(results);
                }
            }
        }
    }

    Ok(results)
}

#[tauri::command]
pub fn read_provenance(project_dir: String) -> Result<Vec<serde_json::Value>, String> {
    let prov_path = Path::new(&project_dir)
        .join("research")
        .join("provenance.jsonl");
    if !prov_path.exists() {
        return Ok(Vec::new());
    }

    let content =
        fs::read_to_string(&prov_path).map_err(|e| format!("Failed to read provenance: {}", e))?;

    let entries: Vec<serde_json::Value> = content
        .lines()
        .filter(|line| !line.trim().is_empty())
        .filter_map(|line| serde_json::from_str(line).ok())
        .collect();

    // Return last 200 entries (most recent)
    let start = if entries.len() > 200 {
        entries.len() - 200
    } else {
        0
    };
    Ok(entries[start..].to_vec())
}

#[derive(Serialize)]
pub struct FigureInfo {
    pub name: String,
    pub path: String,
    pub size: u64,
    pub referenced: bool,
}

#[tauri::command]
pub fn list_figures(project_dir: String) -> Result<Vec<FigureInfo>, String> {
    let dir = Path::new(&project_dir);
    let tex_content = fs::read_to_string(dir.join("main.tex")).unwrap_or_default();

    let mut figures = Vec::new();
    let img_extensions = ["png", "jpg", "jpeg", "pdf", "eps", "svg", "tikz"];

    // Search in figures/, images/, and root for image files
    let search_dirs = ["figures", "images", "fig", "img", "."];
    for search_dir in &search_dirs {
        let search_path = dir.join(search_dir);
        if !search_path.is_dir() {
            continue;
        }
        if let Ok(entries) = fs::read_dir(&search_path) {
            for entry in entries.flatten() {
                let path = entry.path();
                let ext = path
                    .extension()
                    .map(|e| e.to_string_lossy().to_lowercase())
                    .unwrap_or_default();
                if !img_extensions.contains(&ext.as_str()) {
                    continue;
                }
                let name = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                let stem = path.file_stem().unwrap_or_default().to_string_lossy().to_string();
                let size = entry.metadata().map(|m| m.len()).unwrap_or(0);
                let referenced = tex_content.contains(&stem);

                figures.push(FigureInfo {
                    name: name.clone(),
                    path: path.to_string_lossy().to_string(),
                    size,
                    referenced,
                });
            }
        }
    }

    figures.sort_by(|a, b| a.name.cmp(&b.name));
    figures.dedup_by(|a, b| a.path == b.path);
    Ok(figures)
}

// --- Frontmatter parsing helpers ---

struct ParsedFrontmatter {
    title: Option<String>,
    authors: Option<Vec<String>>,
    year: Option<u32>,
    status: Option<String>,
    tags: Option<Vec<String>>,
    evidence_for: Option<Vec<String>>,
    url: Option<String>,
    doi: Option<String>,
    access_level: Option<String>,
    source_type: Option<String>,
}

fn extract_frontmatter(content: &str) -> Option<String> {
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return None;
    }
    let after_first = &trimmed[3..];
    if let Some(end) = after_first.find("\n---") {
        Some(after_first[..end].trim().to_string())
    } else {
        None
    }
}

fn parse_source_frontmatter(content: &str) -> ParsedFrontmatter {
    // Try YAML frontmatter first
    if let Some(fm) = extract_frontmatter(content) {
        return parse_yaml_frontmatter(&fm);
    }

    // Fall back to **Key**: Value markdown format (pipeline output format)
    parse_markdown_metadata(content)
}

fn parse_yaml_frontmatter(fm: &str) -> ParsedFrontmatter {
    let mut result = empty_frontmatter();

    for line in fm.lines() {
        let line = line.trim();
        if let Some(val) = line.strip_prefix("title:") {
            result.title = Some(val.trim().trim_matches('"').to_string());
        } else if let Some(val) = line.strip_prefix("year:") {
            result.year = val.trim().parse().ok();
        } else if let Some(val) = line.strip_prefix("status:") {
            result.status = Some(val.trim().to_string());
        } else if let Some(val) = line.strip_prefix("authors:") {
            result.authors = Some(parse_yaml_array(val));
        } else if let Some(val) = line.strip_prefix("tags:") {
            result.tags = Some(parse_yaml_array(val));
        } else if let Some(val) = line.strip_prefix("evidence_for:") {
            result.evidence_for = Some(parse_yaml_array(val));
        } else if let Some(val) = line.strip_prefix("url:") {
            result.url = Some(val.trim().trim_matches('"').to_string());
        } else if let Some(val) = line.strip_prefix("doi:") {
            result.doi = Some(val.trim().trim_matches('"').to_string());
        } else if let Some(val) = line.strip_prefix("access_level:") {
            result.access_level = Some(val.trim().to_string());
        } else if let Some(val) = line.strip_prefix("source_type:") {
            result.source_type = Some(val.trim().to_string());
        }
    }

    result
}

fn parse_markdown_metadata(content: &str) -> ParsedFrontmatter {
    let mut result = empty_frontmatter();

    // Extract title from # heading
    for line in content.lines() {
        let trimmed = line.trim();
        if let Some(heading) = trimmed.strip_prefix("# ") {
            // Remove "Source Extract: " prefix if present
            let title = heading
                .strip_prefix("Source Extract: ")
                .unwrap_or(heading)
                .to_string();
            if result.title.is_none() {
                result.title = Some(title);
            }
            break;
        }
    }

    // Parse **Key**: Value pairs
    for line in content.lines() {
        let trimmed = line.trim();

        if let Some(val) = extract_bold_value(trimmed, "Title") {
            result.title = Some(val);
        } else if let Some(val) = extract_bold_value(trimmed, "Authors") {
            result.authors = Some(
                val.split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect(),
            );
        } else if let Some(val) = extract_bold_value(trimmed, "Year") {
            // Extract just the 4-digit year from potentially complex strings like "2025 (released...)"
            if let Some(year_str) = val.split_whitespace().next() {
                result.year = year_str.trim_matches(|c: char| !c.is_ascii_digit()).parse().ok();
            }
        } else if let Some(val) = extract_bold_value(trimmed, "URL") {
            result.url = Some(val);
        } else if let Some(val) = extract_bold_value(trimmed, "DOI/URL") {
            if val.starts_with("http") {
                result.url = Some(val.clone());
            }
            // Extract DOI from URL or raw DOI
            if val.contains("doi.org/") {
                result.doi = Some(val.split("doi.org/").last().unwrap_or("").to_string());
            } else if val.starts_with("10.") {
                result.doi = Some(val);
            } else {
                result.url = Some(val);
            }
        } else if let Some(val) = extract_bold_value(trimmed, "DOI") {
            result.doi = Some(val);
        } else if let Some(val) = extract_bold_value(trimmed, "Access Level") {
            result.access_level = Some(val);
        } else if let Some(val) = extract_bold_value(trimmed, "Source Type") {
            result.source_type = Some(val);
        } else if let Some(val) = extract_bold_value(trimmed, "status") {
            result.status = Some(val);
        } else if let Some(val) = extract_bold_value(trimmed, "Tags") {
            result.tags = Some(
                val.split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect(),
            );
        }

        // Stop parsing metadata after first ## heading (content section starts)
        if trimmed.starts_with("## ") {
            break;
        }
    }

    result
}

fn extract_bold_value(line: &str, key: &str) -> Option<String> {
    // Strip optional list prefix ("- ", "* ")
    let stripped = line
        .strip_prefix("- ")
        .or_else(|| line.strip_prefix("* "))
        .unwrap_or(line);

    // Match **Key**: Value or **Key** : Value
    let pattern1 = format!("**{}**:", key);
    let pattern2 = format!("**{}** :", key);

    if let Some(rest) = stripped.strip_prefix(&pattern1) {
        Some(rest.trim().to_string())
    } else if let Some(rest) = stripped.strip_prefix(&pattern2) {
        Some(rest.trim().to_string())
    } else {
        None
    }
}

fn empty_frontmatter() -> ParsedFrontmatter {
    ParsedFrontmatter {
        title: None,
        authors: None,
        year: None,
        status: None,
        tags: None,
        evidence_for: None,
        url: None,
        doi: None,
        access_level: None,
        source_type: None,
    }
}

fn parse_yaml_array(val: &str) -> Vec<String> {
    let trimmed = val.trim();
    let inner = if trimmed.starts_with('[') && trimmed.ends_with(']') {
        &trimmed[1..trimmed.len() - 1]
    } else {
        trimmed
    };
    inner
        .split(',')
        .map(|s| s.trim().trim_matches('"').trim_matches('\'').to_string())
        .filter(|s| !s.is_empty())
        .collect()
}

fn yaml_to_json(yaml_str: &str) -> String {
    // Simple YAML-to-JSON for frontmatter - handles flat key: value pairs
    let mut pairs = Vec::new();
    for line in yaml_str.lines() {
        let line = line.trim();
        if let Some(colon_pos) = line.find(':') {
            let key = line[..colon_pos].trim();
            let val = line[colon_pos + 1..].trim();
            if val.starts_with('[') {
                pairs.push(format!("\"{}\":{}", key, val));
            } else if val.starts_with('"') {
                pairs.push(format!("\"{}\":{}", key, val));
            } else if val.parse::<f64>().is_ok() {
                pairs.push(format!("\"{}\":{}", key, val));
            } else if val == "true" || val == "false" {
                pairs.push(format!("\"{}\":{}", key, val));
            } else {
                pairs.push(format!("\"{}\":\"{}\"", key, val));
            }
        }
    }
    format!("{{{}}}", pairs.join(","))
}

#[derive(Deserialize)]
pub struct ClaimUpdate {
    pub statement: Option<String>,
    pub confidence: Option<String>,
    pub warrant: Option<String>,
    pub qualifier: Option<String>,
    pub rebuttal: Option<String>,
    pub status: Option<String>,
    pub evidence_sources: Option<String>,
}

#[tauri::command]
pub fn update_claim(
    project_dir: String,
    claim_id: String,
    updates: ClaimUpdate,
) -> Result<(), String> {
    let matrix_path = Path::new(&project_dir)
        .join("research")
        .join("claims_matrix.md");
    if !matrix_path.exists() {
        return Err("claims_matrix.md not found".to_string());
    }

    let content =
        fs::read_to_string(&matrix_path).map_err(|e| format!("Failed to read claims: {}", e))?;

    let mut lines: Vec<String> = content.lines().map(|l| l.to_string()).collect();
    let mut found = false;
    let mut changes: Vec<(String, String, String)> = Vec::new(); // (field, old, new)

    for line in &mut lines {
        let trimmed = line.trim();
        if !trimmed.starts_with('|') || trimmed.starts_with("| #") || trimmed.starts_with("|-") {
            continue;
        }

        let cols: Vec<&str> = trimmed.split('|').collect();
        if cols.len() < 12 {
            continue;
        }

        let id = cols[1].trim();
        if id != claim_id {
            continue;
        }

        found = true;
        let mut new_cols: Vec<String> = cols.iter().map(|c| c.to_string()).collect();

        // Map confidence back to strength for storage
        if let Some(ref conf) = updates.confidence {
            let old_strength = new_cols[9].trim().to_string();
            let new_strength = match conf.as_str() {
                "high" => "STRONG",
                "medium" => "MODERATE",
                "low" => "WEAK",
                "critical" => "CRITICAL",
                _ => conf.as_str(),
            };
            new_cols[9] = format!(" {} ", new_strength);
            changes.push(("strength".to_string(), old_strength, new_strength.to_string()));
        }

        if let Some(ref stmt) = updates.statement {
            let old = new_cols[3].trim().to_string();
            new_cols[3] = format!(" {} ", stmt);
            changes.push(("statement".to_string(), old, stmt.clone()));
        }

        if let Some(ref ev) = updates.evidence_sources {
            let old = new_cols[4].trim().to_string();
            new_cols[4] = format!(" {} ", ev);
            // Recalculate score from evidence notation
            let total_score: f64 = ev
                .split(',')
                .filter_map(|entry| {
                    entry.rsplit('=').next().and_then(|s| s.trim().parse::<f64>().ok())
                })
                .sum();
            let old_score = new_cols[8].trim().to_string();
            new_cols[8] = format!(" {:.1} ", total_score);
            // Recalculate strength
            let new_strength = if total_score >= 6.0 {
                "STRONG"
            } else if total_score >= 3.0 {
                "MODERATE"
            } else if total_score >= 1.0 {
                "WEAK"
            } else {
                "CRITICAL"
            };
            new_cols[9] = format!(" {} ", new_strength);
            changes.push(("evidence_sources".to_string(), old, ev.clone()));
            changes.push(("score".to_string(), old_score, format!("{:.1}", total_score)));
        }

        if let Some(ref w) = updates.warrant {
            let old = new_cols.get(5).map(|s| s.trim().to_string()).unwrap_or_default();
            if new_cols.len() > 5 {
                new_cols[5] = format!(" {} ", w);
            }
            changes.push(("warrant".to_string(), old, w.clone()));
        }

        if let Some(ref q) = updates.qualifier {
            let old = new_cols.get(6).map(|s| s.trim().to_string()).unwrap_or_default();
            if new_cols.len() > 6 {
                new_cols[6] = format!(" {} ", q);
            }
            changes.push(("qualifier".to_string(), old, q.clone()));
        }

        if let Some(ref r) = updates.rebuttal {
            let old = new_cols.get(7).map(|s| s.trim().to_string()).unwrap_or_default();
            if new_cols.len() > 7 {
                new_cols[7] = format!(" {} ", r);
            }
            changes.push(("rebuttal".to_string(), old, r.clone()));
        }

        if let Some(ref s) = updates.status {
            let old = new_cols.get(11).map(|s| s.trim().to_string()).unwrap_or_default();
            if new_cols.len() > 11 {
                new_cols[11] = format!(" {} ", s);
            }
            changes.push(("status".to_string(), old, s.clone()));
        }

        *line = new_cols.join("|");
        break;
    }

    if !found {
        return Err(format!("Claim {} not found in claims_matrix.md", claim_id));
    }

    // Write updated matrix
    let mut output = lines.join("\n");
    if content.ends_with('\n') {
        output.push('\n');
    }
    fs::write(&matrix_path, output).map_err(|e| format!("Failed to write claims: {}", e))?;

    // Append to provenance.jsonl
    if !changes.is_empty() {
        let prov_path = Path::new(&project_dir)
            .join("research")
            .join("provenance.jsonl");
        let changes_json: Vec<serde_json::Value> = changes
            .iter()
            .map(|(field, old, new)| {
                serde_json::json!({ "field": field, "old": old, "new": new })
            })
            .collect();
        let entry = serde_json::json!({
            "timestamp": chrono::Utc::now().to_rfc3339(),
            "action": "claim_edit",
            "claim_id": claim_id,
            "changes": changes_json,
            "source": "gui",
        });
        let mut prov_line = serde_json::to_string(&entry).unwrap_or_default();
        prov_line.push('\n');
        // Append (create if doesn't exist)
        use std::io::Write;
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&prov_path)
            .map_err(|e| format!("Failed to open provenance: {}", e))?;
        file.write_all(prov_line.as_bytes())
            .map_err(|e| format!("Failed to write provenance: {}", e))?;
    }

    Ok(())
}

fn update_frontmatter_field(content: &str, field: &str, value: &str) -> String {
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return content.to_string();
    }

    let after_first = &trimmed[3..];
    if let Some(end_pos) = after_first.find("\n---") {
        let fm = &after_first[..end_pos];
        let rest = &after_first[end_pos + 4..];

        let field_prefix = format!("{}:", field);
        let mut found = false;
        let new_fm: String = fm
            .lines()
            .map(|line| {
                if line.trim().starts_with(&field_prefix) {
                    found = true;
                    format!("{}: {}", field, value)
                } else {
                    line.to_string()
                }
            })
            .collect::<Vec<_>>()
            .join("\n");

        let final_fm = if found {
            new_fm
        } else {
            format!("{}\n{}: {}", new_fm, field, value)
        };

        format!("---\n{}\n---{}", final_fm.trim(), rest)
    } else {
        content.to_string()
    }
}
