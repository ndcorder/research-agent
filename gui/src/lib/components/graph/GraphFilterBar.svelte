<script lang="ts">
  import type { SourceMeta, ClaimMeta } from "$lib/types";
  import { collectTags } from "./graphUtils";

  export type LayoutMode = "section" | "force" | "table";

  export interface FilterState {
    activeTags: Set<string>;
    activeStatuses: Set<string>;
    groupByTag: boolean;
    showGaps: boolean;
    densityThreshold: number | null;
  }

  interface Props {
    sources: SourceMeta[];
    claims: ClaimMeta[];
    onFilterChange: (filter: FilterState) => void;
    layoutMode: LayoutMode;
    onLayoutChange: (mode: LayoutMode) => void;
    onResearchGaps: (claimIds: string[]) => void;
  }

  let { sources, claims, onFilterChange, layoutMode, onLayoutChange, onResearchGaps }: Props = $props();

  const STATUS_OPTIONS: { key: string; label: string; colorClass: string }[] = [
    { key: "verified", label: "Verified", colorClass: "success" },
    { key: "flagged", label: "Flagged", colorClass: "warning" },
    { key: "needs-replacement", label: "Needs Replace", colorClass: "danger" },
  ];

  const LAYOUT_OPTIONS: { key: LayoutMode; label: string }[] = [
    { key: "section", label: "Section" },
    { key: "force", label: "Force" },
    { key: "table", label: "Table" },
  ];

  let activeTags = $state<Set<string>>(new Set());
  let activeStatuses = $state<Set<string>>(new Set());
  let groupByTag = $state(false);
  let showGaps = $state(false);
  let densityThreshold = $state<number | null>(null);

  let weakClaimIds = $derived.by(() => {
    if (densityThreshold === null) return [];
    return claims
      .filter((c) => c.evidence_density <= densityThreshold!)
      .map((c) => c.id);
  });

  let allTags = $derived.by(() => {
    const tagCounts = collectTags(sources);
    return Array.from(tagCounts.entries())
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count);
  });

  let activeFilterCount = $derived(activeTags.size + activeStatuses.size);

  function emitFilter() {
    onFilterChange({
      activeTags: new Set(activeTags),
      activeStatuses: new Set(activeStatuses),
      groupByTag,
      showGaps,
      densityThreshold,
    });
  }

  function toggleGaps() {
    showGaps = !showGaps;
    emitFilter();
  }

  function toggleTag(tag: string) {
    const next = new Set(activeTags);
    if (next.has(tag)) {
      next.delete(tag);
    } else {
      next.add(tag);
    }
    activeTags = next;
    emitFilter();
  }

  function toggleStatus(key: string) {
    const next = new Set(activeStatuses);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    activeStatuses = next;
    emitFilter();
  }

  function clearFilters() {
    activeTags = new Set();
    activeStatuses = new Set();
    emitFilter();
  }

  function toggleGroupByTag() {
    groupByTag = !groupByTag;
    emitFilter();
  }

  /** Compute tag brightness: interpolate opacity from 0.5 to 1.0 based on frequency */
  function tagOpacity(count: number): number {
    if (allTags.length <= 1) return 1;
    const max = allTags[0]?.count ?? 1;
    return 0.5 + 0.5 * (count / max);
  }
</script>

<div
  class="absolute left-0 right-0 top-0 z-20 flex h-6 items-center gap-1.5 border-b border-border bg-bg-secondary px-2"
>
  <!-- Layout mode buttons -->
  {#each LAYOUT_OPTIONS as opt}
    <button
      class="flex-shrink-0 rounded px-1.5 text-xs leading-4 transition-colors
        {layoutMode === opt.key
          ? 'bg-accent/20 text-accent'
          : 'bg-bg-tertiary text-text-muted hover:text-text'}"
      onclick={() => onLayoutChange(opt.key)}
    >
      {opt.label}
    </button>
  {/each}

  <span class="h-3 w-px flex-shrink-0 bg-border"></span>

  <!-- All / Reset button -->
  <button
    class="flex-shrink-0 rounded px-1.5 text-xs leading-4 transition-colors
      {activeFilterCount === 0
        ? 'bg-accent/20 text-accent'
        : 'bg-bg-tertiary text-text-muted hover:text-text'}"
    onclick={clearFilters}
  >
    All{#if activeFilterCount > 0}&nbsp;({activeFilterCount}){/if}
  </button>

  <span class="h-3 w-px flex-shrink-0 bg-border"></span>

  <!-- Status filters -->
  {#each STATUS_OPTIONS as opt}
    <button
      class="flex-shrink-0 rounded px-1.5 text-xs leading-4 transition-colors
        {activeStatuses.has(opt.key)
          ? opt.colorClass === 'success'
            ? 'bg-success/20 text-success'
            : opt.colorClass === 'warning'
              ? 'bg-warning/20 text-warning'
              : 'bg-danger/20 text-danger'
          : 'bg-bg-tertiary text-text-muted hover:text-text'}"
      onclick={() => toggleStatus(opt.key)}
    >
      {opt.label}
    </button>
  {/each}

  <span class="h-3 w-px flex-shrink-0 bg-border"></span>

  <!-- Group by tag toggle -->
  <button
    class="flex-shrink-0 rounded px-1.5 text-xs leading-4 transition-colors
      {groupByTag
        ? 'bg-accent/20 text-accent'
        : 'bg-bg-tertiary text-text-muted hover:text-text'}"
    onclick={toggleGroupByTag}
  >
    Group
  </button>

  <!-- Gaps overlay toggle -->
  <button
    class="flex-shrink-0 rounded px-1.5 text-xs leading-4 transition-colors
      {showGaps
        ? 'bg-warning/20 text-warning'
        : 'bg-bg-tertiary text-text-muted hover:text-text'}"
    onclick={toggleGaps}
  >
    Gaps
  </button>

  <!-- Density filter toggle + slider -->
  <button
    class="flex-shrink-0 rounded px-1.5 text-xs leading-4 transition-colors
      {densityThreshold !== null
        ? 'bg-danger/20 text-danger'
        : 'bg-bg-tertiary text-text-muted hover:text-text'}"
    onclick={() => {
      densityThreshold = densityThreshold === null ? 2 : null;
      emitFilter();
    }}
  >
    Density
  </button>

  {#if densityThreshold !== null}
    <input
      type="range"
      min="0"
      max="8"
      step="1"
      bind:value={densityThreshold}
      oninput={() => emitFilter()}
      class="h-1 w-16 flex-shrink-0 cursor-pointer accent-danger"
    />
    <span class="flex-shrink-0 text-xs text-danger">&le;{densityThreshold}</span>
    {#if weakClaimIds.length > 0}
      <button
        class="flex-shrink-0 rounded bg-danger/20 px-1.5 text-xs leading-4 text-danger transition-colors hover:bg-danger/30"
        onclick={() => onResearchGaps(weakClaimIds)}
      >
        Research gaps ({weakClaimIds.length})
      </button>
    {/if}
  {/if}

  <span class="h-3 w-px flex-shrink-0 bg-border"></span>

  <!-- Tag pills (scrollable) -->
  <div class="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
    {#each allTags as { tag, count }}
      <button
        class="flex-shrink-0 whitespace-nowrap rounded px-1.5 text-xs leading-4 transition-colors
          {activeTags.has(tag)
            ? 'bg-accent/20 text-accent'
            : 'bg-bg-tertiary text-text-muted hover:text-text'}"
        style="opacity: {activeTags.has(tag) ? 1 : tagOpacity(count)}"
        onclick={() => toggleTag(tag)}
      >
        {tag}
      </button>
    {/each}
  </div>
</div>
