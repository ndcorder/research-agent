import { writable, derived } from "svelte/store";
import type { PaperConfig, PaperState, SourceMeta, ClaimMeta } from "$lib/types";
import type { TexSection } from "$lib/utils/latex";

export const projectDir = writable<string | null>(null);
export const paperConfig = writable<PaperConfig | null>(null);
export const paperState = writable<PaperState>({
  current_stage: 0,
  stages: {},
});

export const sources = writable<SourceMeta[]>([]);
export const claims = writable<ClaimMeta[]>([]);

export const selectedSource = writable<string | null>(null);
export const selectedClaim = writable<string | null>(null);

export const texSections = writable<TexSection[]>([]);
export const texContent = writable<string>("");
export const wordCount = writable<number>(0);
export const compileOutput = writable<string>("");
export const isCompiling = writable<boolean>(false);
export const editorGoToLine = writable<number | null>(null);

export const activePage = writable<"workspace" | "terminal">("workspace");
export const openFileRequest = writable<{ name: string; path: string } | null>(null);
export const closeActiveTabRequest = writable<boolean>(false);
export const saveActiveTabRequest = writable<boolean>(false);
export const cycleTabRequest = writable<1 | -1 | 0>(0);
export const showCommandPalette = writable<boolean>(false);
export const showSettings = writable<boolean>(false);
export const showSnippetMenu = writable<boolean>(false);
export const rightPanel = writable<
  "graph" | "source" | "pdf" | "claim" | "timeline" | "figures" | "dashboard" | "bib"
>("graph");

export const isProjectLoaded = derived(projectDir, ($dir) => $dir !== null);

export const sourcesByStatus = derived(sources, ($sources) => {
  const groups: Record<string, SourceMeta[]> = {
    verified: [],
    flagged: [],
    "needs-replacement": [],
    "human-added": [],
    unknown: [],
  };
  for (const s of $sources) {
    const status = s.status || "unknown";
    if (status in groups) {
      groups[status].push(s);
    } else {
      groups["unknown"].push(s);
    }
  }
  return groups;
});

export const stageList = derived(paperState, ($state) => {
  return Object.entries($state.stages)
    .map(([key, stage]) => ({
      key,
      ...stage,
    }))
    .sort((a, b) => {
      const numA = parseInt(a.key.split("-")[0]) || 0;
      const numB = parseInt(b.key.split("-")[0]) || 0;
      return numA - numB;
    });
});
