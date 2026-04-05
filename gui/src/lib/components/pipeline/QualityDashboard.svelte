<script lang="ts">
  import { projectDir } from "$lib/stores/project";
  import { readFile } from "$lib/utils/ipc";
  import { onMount } from "svelte";

  interface QualityScores {
    evidence: number;
    writing: number;
    structure: number;
    research: number;
    provenance: number;
    overall: number;
  }

  interface ClaimHeatmapEntry {
    id: string;
    claim: string;
    score: number;
    strength: string;
    warrant: string;
  }

  let scores = $state<QualityScores | null>(null);
  let heatmap = $state<ClaimHeatmapEntry[]>([]);

  async function loadScores() {
    if (!$projectDir) return;
    try {
      const raw = await readFile(`${$projectDir}/.paper-quality.json`);
      scores = JSON.parse(raw);
    } catch {
      scores = null;
    }
  }

  async function loadHeatmap() {
    if (!$projectDir) return;
    try {
      const raw = await readFile(`${$projectDir}/research/evidence_heatmap.md`);
      const lines = raw.split("\n").filter((l: string) => l.startsWith("|") && !l.startsWith("|-"));
      heatmap = lines.slice(1).map((line: string) => {
        const cols = line.split("|").map((c: string) => c.trim()).filter(Boolean);
        return {
          id: cols[0] || "",
          claim: cols[1] || "",
          score: parseFloat(cols[2]) || 0,
          strength: cols[3] || "",
          warrant: cols[4] || "",
        };
      });
    } catch {
      heatmap = [];
    }
  }

  function scoreColor(val: number): string {
    if (val >= 80) return "var(--color-success, #22c55e)";
    if (val >= 60) return "var(--color-warning, #eab308)";
    return "var(--color-error, #ef4444)";
  }

  function strengthColor(s: string): string {
    if (s === "STRONG") return "#22c55e";
    if (s === "MODERATE") return "#eab308";
    if (s === "WEAK") return "#f97316";
    return "#ef4444";
  }

  onMount(() => {
    loadScores();
    loadHeatmap();

    let unlisten: (() => void) | undefined;
    if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
      import("@tauri-apps/api/event").then(({ listen }) => {
        listen("evidence-updated", () => {
          loadScores();
          loadHeatmap();
        }).then((fn) => {
          unlisten = fn;
        });
      });
    }

    return () => {
      unlisten?.();
    };
  });
</script>

<div class="p-3">
  {#if scores}
    <div class="mb-3 grid grid-cols-3 gap-2">
      {#each Object.entries(scores).filter(([k]) => k !== "overall") as [dim, val]}
        <div class="rounded bg-surface p-2 text-center">
          <div class="text-2xl font-bold" style="color: {scoreColor(val)}">{val}</div>
          <div class="text-xs capitalize text-text-muted">{dim}</div>
        </div>
      {/each}
      <div class="col-span-3 rounded bg-surface p-2 text-center text-lg">
        <div class="text-3xl font-bold" style="color: {scoreColor(scores.overall)}">{scores.overall}</div>
        <div class="text-xs capitalize text-text-muted">Overall</div>
      </div>
    </div>
  {:else}
    <p class="text-sm text-text-muted">Run <code>/score</code> to generate quality scores.</p>
  {/if}

  {#if heatmap.length > 0}
    <h3 class="mb-1 text-sm font-semibold text-text">Evidence Heatmap</h3>
    <div class="flex flex-col gap-0.5">
      {#each heatmap as entry}
        <div class="flex items-center gap-2 rounded px-1.5 py-0.5 text-xs">
          <span class="w-8 font-mono">{entry.id}</span>
          <span class="flex-1 truncate" title={entry.claim}>{entry.claim}</span>
          <span class="w-10 text-right font-mono">{entry.score}</span>
          <span class="w-20 font-semibold" style="color: {strengthColor(entry.strength)}">
            {entry.strength}
          </span>
        </div>
      {/each}
    </div>
  {/if}
</div>
