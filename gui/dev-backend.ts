/**
 * Vite plugin that provides a Node.js backend for browser dev mode.
 * Reimplements the Tauri Rust commands as HTTP endpoints so the GUI
 * can be tested without the Tauri shell.
 *
 * All commands are routed through POST /__dev/invoke with JSON body:
 *   { "cmd": "command_name", "args": { ... } }
 */

import type { Plugin } from "vite";
import * as fs from "node:fs";
import * as path from "node:path";
import * as child_process from "node:child_process";

// --- Frontmatter parsing (mirrors Rust backend) ---

function extractFrontmatter(content: string): string | null {
  const trimmed = content.trimStart();
  if (!trimmed.startsWith("---")) return null;
  const after = trimmed.slice(3);
  const end = after.indexOf("\n---");
  if (end === -1) return null;
  return after.slice(0, end).trim();
}

function parseBoldValue(line: string, key: string): string | null {
  // Strip optional list prefix ("- ", "* ")
  const stripped = line.replace(/^[-*]\s+/, "");
  const p1 = `**${key}**:`;
  const p2 = `**${key}** :`;
  if (stripped.startsWith(p1)) return stripped.slice(p1.length).trim();
  if (stripped.startsWith(p2)) return stripped.slice(p2.length).trim();
  return null;
}

function parseSourceFrontmatter(content: string) {
  const meta: Record<string, unknown> = {};
  const fm = extractFrontmatter(content);

  if (fm) {
    for (const line of fm.split("\n")) {
      const t = line.trim();
      const kv = t.match(/^(\w[\w_]*)\s*:\s*(.*)$/);
      if (!kv) continue;
      const [, key, raw] = kv;
      let val: unknown = raw.trim().replace(/^["']|["']$/g, "");
      if (raw.trim().startsWith("[") && raw.trim().endsWith("]")) {
        val = raw
          .trim()
          .slice(1, -1)
          .split(",")
          .map((s) => s.trim().replace(/^["']|["']$/g, ""))
          .filter(Boolean);
      }
      if (typeof val === "string" && /^\d+$/.test(val)) val = parseInt(val, 10);
      meta[key] = val;
    }
    return meta;
  }

  // Markdown **Key**: Value format
  for (const line of content.split("\n")) {
    const t = line.trim();
    if (t.startsWith("# ") && !meta.title) {
      meta.title = t.slice(2).replace(/^Source Extract:\s*/, "");
    }
    for (const key of [
      "Title",
      "Authors",
      "Year",
      "URL",
      "DOI",
      "DOI/URL",
      "Access Level",
      "Source Type",
      "status",
      "Tags",
    ]) {
      const v = parseBoldValue(t, key);
      if (v == null) continue;
      const normKey = key.toLowerCase().replace(/[/ ]/g, "_");
      if (key === "Authors" || key === "Tags") {
        meta[normKey] = v
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      } else if (key === "Year") {
        const m = v.match(/\d{4}/);
        if (m) meta.year = parseInt(m[0], 10);
      } else if (key === "DOI/URL") {
        if (v.includes("doi.org/"))
          meta.doi = v.split("doi.org/").pop() ?? "";
        else if (v.startsWith("10.")) meta.doi = v;
        else meta.url = v;
      } else {
        meta[normKey] = v;
      }
    }
    if (t.startsWith("## ")) break;
  }
  return meta;
}

// --- Command handlers ---

type Handler = (args: Record<string, unknown>) => unknown;

const commands: Record<string, Handler> = {
  validate_paper_project({ path: p }) {
    const dir = p as string;
    const configPath = path.join(dir, ".paper.json");
    if (!fs.existsSync(configPath))
      throw new Error("Not a paper project: .paper.json not found");
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    const hasState = fs.existsSync(path.join(dir, ".paper-state.json"));
    const hasTex = fs.existsSync(path.join(dir, "main.tex"));
    const sourcesDir = path.join(dir, "research", "sources");
    let sourceCount = 0;
    if (fs.existsSync(sourcesDir)) {
      sourceCount = fs
        .readdirSync(sourcesDir)
        .filter((f) => f.endsWith(".md")).length;
    }
    return {
      path: dir,
      config: {
        topic: config.topic ?? null,
        venue: config.venue ?? null,
        depth: config.depth ?? null,
      },
      has_state: hasState,
      source_count: sourceCount,
      has_tex: hasTex,
    };
  },

  read_paper_config({ projectDir }) {
    const configPath = path.join(projectDir as string, ".paper.json");
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    return {
      topic: config.topic ?? null,
      venue: config.venue ?? null,
      depth: config.depth ?? null,
    };
  },

  read_paper_state({ projectDir }) {
    const statePath = path.join(projectDir as string, ".paper-state.json");
    if (!fs.existsSync(statePath))
      return { current_stage: 0, stages: {} };
    return JSON.parse(fs.readFileSync(statePath, "utf-8"));
  },

  list_sources({ projectDir }) {
    const sourcesDir = path.join(
      projectDir as string,
      "research",
      "sources"
    );
    if (!fs.existsSync(sourcesDir)) return [];
    return fs
      .readdirSync(sourcesDir)
      .filter((f) => f.endsWith(".md"))
      .sort()
      .map((f) => {
        const filePath = path.join(sourcesDir, f);
        const content = fs.readFileSync(filePath, "utf-8");
        const meta = parseSourceFrontmatter(content);
        return {
          key: f.replace(/\.md$/, ""),
          path: filePath,
          title: meta.title ?? null,
          authors: meta.authors ?? null,
          year: meta.year ?? null,
          status: meta.status ?? null,
          tags: meta.tags ?? null,
          evidence_for: meta.evidence_for ?? null,
          url: meta.url ?? null,
          doi: meta.doi ?? null,
          access_level: meta.access_level ?? null,
          source_type: meta.source_type ?? null,
        };
      });
  },

  list_claims({ projectDir }) {
    const dir = projectDir as string;
    // Try individual claim files first
    const claimsDir = path.join(dir, "research", "claims");
    if (fs.existsSync(claimsDir)) {
      const claims: unknown[] = [];
      for (const f of fs.readdirSync(claimsDir)) {
        if (!f.endsWith(".md")) continue;
        const content = fs.readFileSync(path.join(claimsDir, f), "utf-8");
        const fm = extractFrontmatter(content);
        if (fm) {
          try {
            const obj: Record<string, unknown> = {};
            for (const line of fm.split("\n")) {
              const m = line.match(/^(\w[\w_]*)\s*:\s*(.*)$/);
              if (m) obj[m[1]] = m[2].trim().replace(/^["']|["']$/g, "");
            }
            claims.push(obj);
          } catch { /* skip */ }
        }
      }
      if (claims.length > 0) return claims;
    }

    // Fall back to claims_matrix.md
    const matrixPath = path.join(dir, "research", "claims_matrix.md");
    if (!fs.existsSync(matrixPath)) return [];
    const content = fs.readFileSync(matrixPath, "utf-8");
    const claims: unknown[] = [];
    for (const line of content.split("\n")) {
      const t = line.trim();
      if (!t.startsWith("|") || t.startsWith("| #") || t.startsWith("|-"))
        continue;
      const cols = t.split("|");
      if (cols.length < 12) continue;
      const id = cols[1]?.trim();
      if (!id || !id.startsWith("C")) continue;
      const strengthMap: Record<string, string> = {
        STRONG: "high",
        MODERATE: "medium",
        WEAK: "low",
        CRITICAL: "critical",
      };
      const strength = cols[9]?.trim() ?? "";
      claims.push({
        id,
        statement: cols[3]?.trim(),
        type: cols[2]?.trim(),
        confidence: strengthMap[strength] ?? "unknown",
        evidence_density: (cols[4]?.trim() ?? "").split(",").length,
        section: cols[10]?.trim(),
        score: parseFloat(cols[8]?.trim() ?? "0") || 0,
        strength,
        status: cols[11]?.trim() ?? "",
        evidence_sources: cols[4]?.trim(),
      });
    }
    return claims;
  },

  read_file({ path: p }) {
    return fs.readFileSync(p as string, "utf-8");
  },

  write_file({ path: p, content }) {
    fs.writeFileSync(p as string, content as string);
  },

  list_directory({ path: p }) {
    const entries = fs.readdirSync(p as string, { withFileTypes: true });
    return entries
      .filter((e) => !e.name.startsWith("."))
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((e) => {
        const fullPath = path.join(p as string, e.name);
        const stat = fs.statSync(fullPath);
        return {
          name: e.name,
          path: fullPath,
          is_dir: e.isDirectory(),
          size: stat.size,
        };
      });
  },

  search_sources({ projectDir, query }) {
    const q = (query as string).toLowerCase();
    if (!q) return [];
    const sourcesDir = path.join(projectDir as string, "research", "sources");
    if (!fs.existsSync(sourcesDir)) return [];
    const results: unknown[] = [];
    for (const f of fs.readdirSync(sourcesDir)) {
      if (!f.endsWith(".md")) continue;
      const filePath = path.join(sourcesDir, f);
      const content = fs.readFileSync(filePath, "utf-8");
      const meta = parseSourceFrontmatter(content);
      for (const [i, line] of content.split("\n").entries()) {
        const pos = line.toLowerCase().indexOf(q);
        if (pos !== -1) {
          results.push({
            source_key: f.replace(/\.md$/, ""),
            source_title: meta.title ?? null,
            line_number: i + 1,
            line_content: line,
            match_start: pos,
            match_end: pos + q.length,
          });
          if (results.length >= 100) return results;
        }
      }
    }
    return results;
  },

  list_figures({ projectDir }) {
    const dir = projectDir as string;
    const texContent = fs.existsSync(path.join(dir, "main.tex"))
      ? fs.readFileSync(path.join(dir, "main.tex"), "utf-8")
      : "";
    const imgExts = new Set(["png", "jpg", "jpeg", "pdf", "eps", "svg", "tikz"]);
    const figures: { name: string; path: string; size: number; referenced: boolean }[] = [];
    const seen = new Set<string>();
    for (const sub of ["figures", "images", "fig", "img", "."]) {
      const searchDir = path.join(dir, sub);
      if (!fs.existsSync(searchDir)) continue;
      for (const f of fs.readdirSync(searchDir)) {
        const ext = path.extname(f).slice(1).toLowerCase();
        if (!imgExts.has(ext)) continue;
        const fullPath = path.join(searchDir, f);
        if (seen.has(fullPath)) continue;
        seen.add(fullPath);
        const stem = path.basename(f, path.extname(f));
        const stat = fs.statSync(fullPath);
        figures.push({
          name: f,
          path: fullPath,
          size: stat.size,
          referenced: texContent.includes(stem),
        });
      }
    }
    figures.sort((a, b) => a.name.localeCompare(b.name));
    return figures;
  },

  read_provenance({ projectDir }) {
    const provPath = path.join(
      projectDir as string,
      "research",
      "provenance.jsonl"
    );
    if (!fs.existsSync(provPath)) return [];
    const lines = fs
      .readFileSync(provPath, "utf-8")
      .split("\n")
      .filter((l) => l.trim());
    const entries = lines
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
    return entries.slice(-200);
  },

  update_source_status({ path: p, status }) {
    const content = fs.readFileSync(p as string, "utf-8");
    const updated = updateFrontmatterField(content, "status", status as string);
    fs.writeFileSync(p as string, updated);
  },

  append_human_notes({ path: p, note }) {
    let content = fs.readFileSync(p as string, "utf-8");
    if (content.includes("## Human Notes")) {
      const parts = content.split("## Human Notes");
      content = `${parts[0]}## Human Notes\n${note}\n${(parts[1] ?? "").replace(/^\n+/, "")}`;
    } else {
      content += `\n\n## Human Notes\n\n${note}\n`;
    }
    fs.writeFileSync(p as string, content);
  },

  compile_latex({ projectDir }) {
    const dir = projectDir as string;
    try {
      const result = child_process.execSync(
        "latexmk -pdf -interaction=nonstopmode main.tex",
        { cwd: dir, timeout: 60000, encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }
      );
      return {
        success: true,
        output: result,
        pdf_path: path.join(dir, "main.pdf"),
      };
    } catch (e: any) {
      return {
        success: false,
        output: e.stderr || e.stdout || e.message || "Compilation failed",
        pdf_path: null,
      };
    }
  },

  get_recent_projects() {
    return [];
  },

  add_recent_project() {
    // no-op in dev mode
  },

  start_watching() {
    // no-op — no file watcher in browser dev mode
  },

  stop_watching() {
    // no-op
  },

  // Terminal commands — not supported in browser mode
  spawn_terminal() {
    throw new Error("Terminal not available in browser dev mode");
  },
  write_terminal() {
    throw new Error("Terminal not available in browser dev mode");
  },
  resize_terminal() {
    // no-op
  },
  kill_terminal() {
    // no-op
  },
};

function updateFrontmatterField(
  content: string,
  field: string,
  value: string
): string {
  const trimmed = content.trimStart();
  if (!trimmed.startsWith("---")) return content;
  const after = trimmed.slice(3);
  const endPos = after.indexOf("\n---");
  if (endPos === -1) return content;
  const fm = after.slice(0, endPos);
  const rest = after.slice(endPos + 4);
  let found = false;
  const newFm = fm
    .split("\n")
    .map((line) => {
      if (line.trim().startsWith(`${field}:`)) {
        found = true;
        return `${field}: ${value}`;
      }
      return line;
    })
    .join("\n");
  const finalFm = found ? newFm : `${newFm}\n${field}: ${value}`;
  return `---\n${finalFm.trim()}\n---${rest}`;
}

// --- Vite plugin ---

export default function devBackend(): Plugin {
  return {
    name: "research-agent-dev-backend",
    configureServer(server) {
      server.middlewares.use("/__dev/invoke", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end("Method not allowed");
          return;
        }

        let body = "";
        req.on("data", (chunk: Buffer) => (body += chunk.toString()));
        req.on("end", () => {
          try {
            const { cmd, args } = JSON.parse(body);
            const handler = commands[cmd];
            if (!handler) {
              res.statusCode = 404;
              res.end(JSON.stringify({ error: `Unknown command: ${cmd}` }));
              return;
            }
            const result = handler(args ?? {});
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ ok: true, data: result ?? null }));
          } catch (e: any) {
            res.statusCode = 400;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ ok: false, error: e.message }));
          }
        });
      });
    },
  };
}
