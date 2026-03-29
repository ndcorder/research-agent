<script lang="ts">
  import { rightPanel } from "$lib/stores/project";
  import GraphView from "../graph/GraphView.svelte";
  import SourceDetail from "../sources/SourceDetail.svelte";
  import PdfPreview from "../pdf/PdfPreview.svelte";
  import ClaimDetail from "../claims/ClaimDetail.svelte";
  import ProvenanceTimeline from "../sources/ProvenanceTimeline.svelte";
  import FigureManager from "../sources/FigureManager.svelte";
  import BibManager from "../sources/BibManager.svelte";
  import ResearchDashboard from "../sources/ResearchDashboard.svelte";

  const panels = [
    { id: "dashboard" as const, label: "Dashboard" },
    { id: "graph" as const, label: "Graph" },
    { id: "source" as const, label: "Source" },
    { id: "claim" as const, label: "Claim" },
    { id: "pdf" as const, label: "PDF" },
    { id: "figures" as const, label: "Figs" },
    { id: "bib" as const, label: "Refs" },
    { id: "timeline" as const, label: "Timeline" },
  ];
</script>

<div class="flex h-full flex-col">
  <!-- Panel tabs -->
  <div class="flex border-b border-border bg-bg-secondary px-2">
    {#each panels as panel}
      <button
        class="px-2 py-1 text-xs transition-colors {$rightPanel === panel.id
          ? 'border-b-2 border-accent text-text-bright'
          : 'text-text-muted hover:text-text'}"
        onclick={() => rightPanel.set(panel.id)}
      >
        {panel.label}
      </button>
    {/each}
  </div>

  <!-- Panel content -->
  <div class="flex-1 overflow-hidden">
    {#if $rightPanel === "dashboard"}
      <ResearchDashboard />
    {:else if $rightPanel === "graph"}
      <GraphView />
    {:else if $rightPanel === "source"}
      <SourceDetail />
    {:else if $rightPanel === "claim"}
      <ClaimDetail />
    {:else if $rightPanel === "pdf"}
      <PdfPreview />
    {:else if $rightPanel === "figures"}
      <FigureManager />
    {:else if $rightPanel === "bib"}
      <BibManager />
    {:else if $rightPanel === "timeline"}
      <ProvenanceTimeline />
    {:else}
      <div class="flex h-full items-center justify-center text-xs text-text-muted">
        Select a view
      </div>
    {/if}
  </div>
</div>
