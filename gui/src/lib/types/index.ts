export interface SourceMeta {
  key: string;
  path: string;
  title: string | null;
  authors: string[] | null;
  year: number | null;
  status: string | null;
  tags: string[] | null;
  evidence_for: string[] | null;
  url: string | null;
  doi: string | null;
  access_level: string | null;
  source_type: string | null;
}

export interface ClaimMeta {
  id: string;
  statement: string;
  type: string;
  confidence: string;
  evidence_density: number;
  section: string;
  score?: number;
  strength?: string;
  status?: string;
  evidence_sources?: string;
  warrant?: string;
  qualifier?: string;
  rebuttal?: string;
}

export interface ClaimUpdate {
  statement?: string;
  confidence?: string;
  warrant?: string;
  qualifier?: string;
  rebuttal?: string;
  status?: string;
  evidence_sources?: string;
}

export interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
}

export interface PipelineStage {
  status: "pending" | "in_progress" | "completed" | "failed";
  [key: string]: unknown;
}

export interface ActiveAgent {
  name: string;
  model: string;
  task: string;
}

export interface PaperState {
  current_stage: number;
  stages: Record<string, PipelineStage>;
  active_agents?: ActiveAgent[];
  started_at?: string;
  sections?: Record<string, unknown>;
}

export interface PaperConfig {
  topic: string;
  venue: string;
  depth: string;
}

export interface CompileResult {
  success: boolean;
  output: string;
  pdf_path: string | null;
}

export interface FileChangeEvent {
  path: string;
  kind: "created" | "modified" | "removed" | "other";
}

export type SourceStatus =
  | "verified"
  | "flagged"
  | "needs-replacement"
  | "human-added";

export type RightPanel = "graph" | "source" | "pdf" | "claim" | "timeline" | "figures" | "bib" | "dashboard";

export interface ProvenanceEntry {
  action: string;
  target: string;
  details?: string;
  timestamp?: string;
  agent?: string;
  stage?: string;
  iteration?: number;
  sources?: string[];
  reasoning?: string;
  diff_summary?: string;
  feedback_ref?: string;
}
