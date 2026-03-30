<script lang="ts">
  import { projectDir, cursorParagraph, selectedSource, rightPanel, editorGoToLine } from "$lib/stores/project";
  import { readProvenance } from "$lib/utils/ipc";
  import type { ProvenanceEntry } from "$lib/types";
  import { groupByTarget, availableSections } from "$lib/utils/provenanceUtils";
  import SectionPicker from "$lib/components/provenance/SectionPicker.svelte";
  import SwimlaneDiagram from "$lib/components/provenance/SwimlaneDiagram.svelte";
  import SwimlaneDrilldown from "$lib/components/provenance/SwimlaneDrilldown.svelte";
  import { parseLatexParagraphs } from "$lib/utils/latexParaMap";
  import { texContent } from "$lib/stores/project";

  let entries = $state<ProvenanceEntry[]>([]);
  let loading = $state(false);
  let error = $state("");
  let sectionFilter = $state<string | null>(null);
  let expandedTarget = $state<string | null>(null);
  let focusedRowIdx = $state(0);

  let groups = $derived(groupByTarget(entries));
  let sections = $derived(availableSections(groups));
  let filteredGroups = $derived(
    sectionFilter ? groups.filter((g) => g.section === sectionFilter) : groups
  );

  // Editor-driven highlight target
  let highlightTarget = $derived($cursorParagraph);

  async function loadEntries() {
    const dir = $projectDir;
    if (!dir) return;
    loading = true;
    error = "";
    try {
      const raw = await readProvenance(dir);
      entries = raw as unknown as ProvenanceEntry[];
    } catch (e) {
      entries = [];
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  // Load on mount and when project changes
  $effect(() => {
    const dir = $projectDir;
    if (dir) {
      loadEntries();
    } else {
      entries = [];
    }
  });

  // Auto-refresh every 10 seconds
  $effect(() => {
    const interval = setInterval(() => {
      if ($projectDir) loadEntries();
    }, 10000);
    return () => clearInterval(interval);
  });

  function handleRowClick(target: string) {
    if (expandedTarget === target) {
      expandedTarget = null;
    } else {
      expandedTarget = target;
    }
    // Timeline -> Editor: scroll to paragraph
    scrollEditorToTarget(target);
  }

  function scrollEditorToTarget(target: string) {
    const content = $texContent;
    if (!content) return;
    const paraMap = parseLatexParagraphs(content);
    const range = paraMap.get(target);
    if (range) {
      editorGoToLine.set(range.startLine);
    }
  }

  function handleSourceClick(key: string) {
    selectedSource.set(key);
    rightPanel.set("source");
  }

  function handleFeedbackClick(ref: string) {
    // Could open the feedback file in editor
    console.log("Open feedback:", ref);
  }

  // Keyboard navigation
  function handleKeydown(e: KeyboardEvent) {
    if (filteredGroups.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      focusedRowIdx = Math.min(focusedRowIdx + 1, filteredGroups.length - 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      focusedRowIdx = Math.max(focusedRowIdx - 1, 0);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const group = filteredGroups[focusedRowIdx];
      if (group) handleRowClick(group.target);
    } else if (e.key === "Escape") {
      expandedTarget = null;
    }
  }

  // Get expanded group events
  let expandedGroup = $derived(
    expandedTarget ? groups.find((g) => g.target === expandedTarget) : null
  );
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
  class="flex h-full flex-col bg-bg"
  tabindex="0"
  role="region"
  aria-label="Provenance timeline"
  onkeydown={handleKeydown}
>
  <!-- Section picker -->
  <div class="flex-shrink-0 border-b border-border bg-bg-secondary">
    <SectionPicker
      {sections}
      selected={sectionFilter}
      onselect={(s) => (sectionFilter = s)}
    />
  </div>

  <!-- Content -->
  {#if loading && entries.length === 0}
    <div class="flex flex-1 items-center justify-center">
      <span class="text-sm text-text-muted">Loading provenance...</span>
    </div>
  {:else if entries.length === 0}
    <div class="flex flex-1 items-center justify-center p-6">
      <div class="text-center">
        <p class="mb-1 text-sm text-text-muted">No provenance entries yet.</p>
        <p class="text-xs text-text-muted">Run the pipeline to generate activity logs.</p>
      </div>
    </div>
  {:else}
    <div class="flex-1 overflow-hidden">
      <SwimlaneDiagram
        {entries}
        {sectionFilter}
        {highlightTarget}
        onrowclick={handleRowClick}
      />
    </div>

    <!-- Drilldown panel (slides up from bottom when a row is expanded) -->
    {#if expandedGroup}
      <div class="max-h-[40%] flex-shrink-0 overflow-y-auto border-t border-border">
        <SwimlaneDrilldown
          target={expandedGroup.target}
          events={expandedGroup.events}
          onsourceclick={handleSourceClick}
          onfeedbackclick={handleFeedbackClick}
        />
      </div>
    {/if}
  {/if}
</div>
