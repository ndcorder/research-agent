import type {
  SourceMeta,
  FileEntry,
  PaperState,
  CompileResult,
} from "$lib/types";

// Auto-detect Tauri vs browser dev mode
const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

let _invoke: <T>(cmd: string, args?: Record<string, unknown>) => Promise<T>;

if (isTauri) {
  // Dynamic import so the Tauri module is never loaded in browser mode
  const mod = await import("@tauri-apps/api/core");
  _invoke = mod.invoke;
} else {
  const mod = await import("$lib/dev/browser-invoke");
  _invoke = mod.invoke;
}

export async function readFile(path: string): Promise<string> {
  return _invoke("read_file", { path });
}

export async function writeFile(path: string, content: string): Promise<void> {
  return _invoke("write_file", { path, content });
}

export async function listDirectory(path: string): Promise<FileEntry[]> {
  return _invoke("list_directory", { path });
}

export async function listSources(projectDir: string): Promise<SourceMeta[]> {
  return _invoke("list_sources", { projectDir });
}

export async function listClaims(projectDir: string): Promise<unknown[]> {
  return _invoke("list_claims", { projectDir });
}

export async function readPaperState(
  projectDir: string
): Promise<PaperState> {
  return _invoke("read_paper_state", { projectDir });
}

export async function updateSourceStatus(
  path: string,
  status: string
): Promise<void> {
  return _invoke("update_source_status", { path, status });
}

export async function appendHumanNotes(
  path: string,
  note: string
): Promise<void> {
  return _invoke("append_human_notes", { path, note });
}

export async function compileLatex(
  projectDir: string
): Promise<CompileResult> {
  return _invoke("compile_latex", { projectDir });
}

export async function spawnTerminal(cwd: string): Promise<number> {
  return _invoke("spawn_terminal", { cwd });
}

export async function writeTerminal(
  id: number,
  data: string
): Promise<void> {
  return _invoke("write_terminal", { id, data });
}

export async function resizeTerminal(
  id: number,
  rows: number,
  cols: number
): Promise<void> {
  return _invoke("resize_terminal", { id, rows, cols });
}

export async function killTerminal(id: number): Promise<void> {
  return _invoke("kill_terminal", { id });
}

export async function startWatching(path: string): Promise<void> {
  return _invoke("start_watching", { path });
}

export async function stopWatching(): Promise<void> {
  return _invoke("stop_watching");
}

export interface ProjectInfo {
  path: string;
  config: { topic: string | null; venue: string | null; depth: string | null };
  has_state: boolean;
  source_count: number;
  has_tex: boolean;
}

export async function validatePaperProject(
  path: string
): Promise<ProjectInfo> {
  return _invoke("validate_paper_project", { path });
}

export async function readPaperConfig(
  projectDir: string
): Promise<{ topic: string | null; venue: string | null; depth: string | null }> {
  return _invoke("read_paper_config", { projectDir });
}

export async function getRecentProjects(): Promise<string[]> {
  return _invoke("get_recent_projects");
}

export async function addRecentProject(path: string): Promise<void> {
  return _invoke("add_recent_project", { path });
}

export interface SearchResult {
  source_key: string;
  source_title: string | null;
  line_number: number;
  line_content: string;
  match_start: number;
  match_end: number;
}

export async function searchSources(
  projectDir: string,
  query: string
): Promise<SearchResult[]> {
  return _invoke("search_sources", { projectDir, query });
}

export interface FigureInfo {
  name: string;
  path: string;
  size: number;
  referenced: boolean;
}

export async function listFigures(
  projectDir: string
): Promise<FigureInfo[]> {
  return _invoke("list_figures", { projectDir });
}

export async function readProvenance(
  projectDir: string
): Promise<Record<string, unknown>[]> {
  return _invoke("read_provenance", { projectDir });
}
