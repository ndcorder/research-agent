<script lang="ts">
  import { onMount } from "svelte";
  import * as d3 from "d3";
  import type { ProvenanceEntry } from "$lib/types";
  import {
    groupByTarget,
    stageColumns,
    actionDotColor,
    type TargetGroup,
  } from "$lib/utils/provenanceUtils";

  interface Props {
    entries: ProvenanceEntry[];
    sectionFilter: string | null;
    highlightTarget: string | null;
    onrowclick: (target: string) => void;
  }

  let { entries, sectionFilter, highlightTarget, onrowclick }: Props = $props();

  let svgEl = $state<SVGSVGElement | null>(null);
  let containerEl = $state<HTMLDivElement | null>(null);
  let expandedRow = $state<string | null>(null);
  let tooltipData = $state<{
    x: number;
    y: number;
    entry: ProvenanceEntry;
  } | null>(null);

  // Layout constants
  const ROW_HEIGHT = 32;
  const HEADER_HEIGHT = 40;
  const LABEL_WIDTH = 140;
  const COL_WIDTH = 48;
  const DOT_MIN = 4;
  const DOT_MAX = 10;
  const DIVIDER_WIDTH = 12;
  const PADDING = { top: 8, right: 16, bottom: 8 };

  let groups = $derived(groupByTarget(entries));
  let columns = $derived(stageColumns(entries));

  let filteredGroups = $derived<TargetGroup[]>(
    sectionFilter
      ? groups.filter((g) => g.section === sectionFilter)
      : groups
  );

  let totalWidth = $derived(
    LABEL_WIDTH +
      columns.pipeline.length * COL_WIDTH +
      DIVIDER_WIDTH +
      columns.auto.length * COL_WIDTH +
      PADDING.right
  );

  let totalHeight = $derived(
    HEADER_HEIGHT + filteredGroups.length * ROW_HEIGHT + PADDING.top + PADDING.bottom
  );

  /** Map a stage to its x position */
  function stageX(stage: string): number {
    const pipeIdx = columns.pipeline.indexOf(stage);
    if (pipeIdx >= 0) {
      return LABEL_WIDTH + pipeIdx * COL_WIDTH + COL_WIDTH / 2;
    }
    const autoIdx = columns.auto.indexOf(stage);
    if (autoIdx >= 0) {
      return (
        LABEL_WIDTH +
        columns.pipeline.length * COL_WIDTH +
        DIVIDER_WIDTH +
        autoIdx * COL_WIDTH +
        COL_WIDTH / 2
      );
    }
    return LABEL_WIDTH + COL_WIDTH / 2;
  }

  /** Count events at a specific stage for a group */
  function eventsAtStage(group: TargetGroup, stage: string): ProvenanceEntry[] {
    return group.events.filter((e) => e.stage === stage);
  }

  /** Dominant action at a stage (most frequent) */
  function dominantAction(events: ProvenanceEntry[]): string {
    if (events.length === 0) return "unknown";
    const counts = new Map<string, number>();
    for (const e of events) {
      const a = e.action || "unknown";
      counts.set(a, (counts.get(a) || 0) + 1);
    }
    let best = "";
    let bestCount = 0;
    for (const [action, count] of counts) {
      if (count > bestCount) {
        best = action;
        bestCount = count;
      }
    }
    return best;
  }

  /** Dot radius scaled by event count */
  function dotRadius(count: number): number {
    if (count <= 1) return DOT_MIN;
    return Math.min(DOT_MIN + (count - 1) * 2, DOT_MAX);
  }

  function handleDotHover(
    event: MouseEvent,
    entry: ProvenanceEntry
  ) {
    const rect = containerEl?.getBoundingClientRect();
    if (!rect) return;
    tooltipData = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      entry,
    };
  }

  function handleDotLeave() {
    tooltipData = null;
  }

  function handleRowClick(target: string) {
    if (expandedRow === target) {
      expandedRow = null;
    } else {
      expandedRow = target;
    }
    onrowclick(target);
  }

  function formatTime(timestamp?: string): string {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return timestamp;
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  /** All distinct stages that have events */
  let allStages = $derived([...columns.pipeline, ...columns.auto]);
</script>

<div class="relative h-full overflow-auto bg-bg" bind:this={containerEl}>
  {#if filteredGroups.length === 0}
    <div class="flex h-full items-center justify-center p-6">
      <p class="text-sm text-text-muted">
        {#if entries.length === 0}
          No provenance entries yet.
        {:else}
          No entries match this filter.
        {/if}
      </p>
    </div>
  {:else}
    <svg
      bind:this={svgEl}
      width={totalWidth}
      height={totalHeight}
      class="select-none"
    >
      <!-- Header row with stage labels -->
      <g class="header" transform="translate(0, {PADDING.top})">
        <!-- "Target" label -->
        <text
          x={LABEL_WIDTH / 2}
          y={HEADER_HEIGHT / 2}
          text-anchor="middle"
          dominant-baseline="central"
          class="fill-text-muted text-[10px] font-semibold uppercase tracking-wider"
        >
          Target
        </text>

        <!-- Pipeline stage headers -->
        {#each columns.pipeline as stage, i}
          <text
            x={LABEL_WIDTH + i * COL_WIDTH + COL_WIDTH / 2}
            y={HEADER_HEIGHT / 2}
            text-anchor="middle"
            dominant-baseline="central"
            class="fill-text-muted text-[10px]"
          >
            {stage}
          </text>
        {/each}

        <!-- Divider -->
        {#if columns.auto.length > 0}
          <line
            x1={LABEL_WIDTH + columns.pipeline.length * COL_WIDTH + DIVIDER_WIDTH / 2}
            y1={4}
            x2={LABEL_WIDTH + columns.pipeline.length * COL_WIDTH + DIVIDER_WIDTH / 2}
            y2={HEADER_HEIGHT - 4}
            class="stroke-border"
            stroke-width="1"
            stroke-dasharray="2,2"
          />
        {/if}

        <!-- Auto iteration headers -->
        {#each columns.auto as stage, i}
          <text
            x={LABEL_WIDTH +
              columns.pipeline.length * COL_WIDTH +
              DIVIDER_WIDTH +
              i * COL_WIDTH +
              COL_WIDTH / 2}
            y={HEADER_HEIGHT / 2}
            text-anchor="middle"
            dominant-baseline="central"
            class="fill-text-muted text-[10px]"
          >
            {stage.replace("auto-", "A")}
          </text>
        {/each}

        <!-- Header bottom line -->
        <line
          x1={0}
          y1={HEADER_HEIGHT}
          x2={totalWidth}
          y2={HEADER_HEIGHT}
          class="stroke-border"
          stroke-width="1"
        />
      </g>

      <!-- Swimlane rows -->
      {#each filteredGroups as group, rowIdx}
        {@const y = PADDING.top + HEADER_HEIGHT + rowIdx * ROW_HEIGHT}
        {@const isHighlighted = highlightTarget === group.target}
        {@const isExpanded = expandedRow === group.target}

        <!-- Row background -->
        <rect
          x={0}
          {y}
          width={totalWidth}
          height={ROW_HEIGHT}
          class={isHighlighted
            ? "fill-accent/10"
            : rowIdx % 2 === 0
              ? "fill-bg"
              : "fill-bg-secondary/50"}
          rx={0}
        />

        <!-- Highlight border for editor-linked row -->
        {#if isHighlighted}
          <rect
            x={0}
            {y}
            width={3}
            height={ROW_HEIGHT}
            class="fill-accent"
          />
        {/if}

        <!-- Target label (clickable) -->
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <text
          x={8}
          y={y + ROW_HEIGHT / 2}
          dominant-baseline="central"
          class="cursor-pointer text-[11px] {isExpanded
            ? 'fill-accent font-semibold'
            : 'fill-text-bright'} hover:fill-accent"
          onclick={() => handleRowClick(group.target)}
        >
          {group.target.length > 18
            ? group.target.slice(0, 17) + "\u2026"
            : group.target}
        </text>

        <!-- Dots for each stage -->
        {#each allStages as stage}
          {@const events = eventsAtStage(group, stage)}
          {#if events.length > 0}
            {@const cx = stageX(stage)}
            {@const cy = y + ROW_HEIGHT / 2}
            {@const r = dotRadius(events.length)}
            {@const color = actionDotColor(dominantAction(events))}

            <circle
              {cx}
              {cy}
              {r}
              fill={color}
              class="cursor-pointer transition-transform hover:scale-125"
              opacity={isHighlighted ? 1 : 0.85}
              onmouseenter={(e) => handleDotHover(e, events[0])}
              onmouseleave={handleDotLeave}
              onclick={() => handleRowClick(group.target)}
            />

            <!-- Event count badge for multi-event dots -->
            {#if events.length > 1}
              <text
                x={cx}
                y={cy}
                text-anchor="middle"
                dominant-baseline="central"
                class="pointer-events-none fill-bg text-[8px] font-bold"
              >
                {events.length}
              </text>
            {/if}
          {/if}
        {/each}

        <!-- Row bottom border -->
        <line
          x1={0}
          y1={y + ROW_HEIGHT}
          x2={totalWidth}
          y2={y + ROW_HEIGHT}
          class="stroke-border/30"
          stroke-width="0.5"
        />
      {/each}

      <!-- Vertical divider between pipeline and auto -->
      {#if columns.auto.length > 0}
        <line
          x1={LABEL_WIDTH + columns.pipeline.length * COL_WIDTH + DIVIDER_WIDTH / 2}
          y1={PADDING.top + HEADER_HEIGHT}
          x2={LABEL_WIDTH + columns.pipeline.length * COL_WIDTH + DIVIDER_WIDTH / 2}
          y2={totalHeight}
          class="stroke-border"
          stroke-width="1"
          stroke-dasharray="3,3"
        />
      {/if}
    </svg>

    <!-- Tooltip -->
    {#if tooltipData}
      <div
        class="pointer-events-none absolute z-50 rounded border border-border bg-bg-secondary px-2.5 py-1.5 shadow-lg"
        style="left: {tooltipData.x + 12}px; top: {tooltipData.y - 8}px;"
      >
        <div class="flex items-center gap-2">
          <span
            class="inline-block h-2 w-2 rounded-full"
            style="background: {actionDotColor(tooltipData.entry.action)}"
          ></span>
          <span class="text-xs font-medium text-text-bright">
            {tooltipData.entry.action}
          </span>
        </div>
        {#if tooltipData.entry.agent}
          <p class="mt-0.5 text-[10px] text-text-muted">
            Agent: {tooltipData.entry.agent}
          </p>
        {/if}
        {#if tooltipData.entry.timestamp}
          <p class="text-[10px] text-text-muted">
            {formatTime(tooltipData.entry.timestamp)}
          </p>
        {/if}
      </div>
    {/if}
  {/if}
</div>
