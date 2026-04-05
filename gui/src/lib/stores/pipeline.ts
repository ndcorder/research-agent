import { writable, derived } from "svelte/store";

export interface StageStatus {
  done: boolean;
  [key: string]: unknown;
}

export interface PipelineState {
  running: boolean;
  currentStage: string;
  stages: Record<string, StageStatus>;
  terminalId: number | null;
}

export const pipelineState = writable<PipelineState>({
  running: false,
  currentStage: "",
  stages: {},
  terminalId: null,
});

export const pipelineStageList = [
  { key: "research", label: "Research", number: "1" },
  { key: "snowballing", label: "Snowballing", number: "1b" },
  { key: "cocitation", label: "Co-citation", number: "1b2" },
  { key: "codex_cross_check", label: "Codex Cross-check", number: "1c" },
  { key: "source_acquisition", label: "Source Acquisition", number: "1d" },
  { key: "deep_read", label: "Deep Read", number: "1e" },
  { key: "literature_synthesis", label: "Synthesis", number: "1f" },
  { key: "outline", label: "Planning", number: "2" },
  { key: "codex_thesis", label: "Thesis Stress-test", number: "2b" },
  { key: "targeted_research", label: "Targeted Research", number: "2c" },
  { key: "novelty_check", label: "Novelty Check", number: "2d" },
  { key: "assumptions", label: "Assumptions", number: "2e" },
  { key: "writing", label: "Writing", number: "3" },
  { key: "coherence", label: "Coherence", number: "3b" },
  { key: "reference_integrity", label: "References", number: "3c" },
  { key: "figures", label: "Figures", number: "4" },
  { key: "qa", label: "QA Loop", number: "5" },
  { key: "post_qa", label: "Post-QA Audits", number: "5b" },
  { key: "finalization", label: "Finalization", number: "6" },
] as const;

export const completedStages = derived(pipelineState, ($ps) =>
  pipelineStageList.filter((s) => $ps.stages[s.key]?.done).length
);

export const totalStages = pipelineStageList.length;
