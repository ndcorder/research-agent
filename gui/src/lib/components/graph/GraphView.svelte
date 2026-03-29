<script lang="ts">
  import { onMount } from "svelte";
  import * as d3 from "d3";
  import {
    sources,
    claims,
    selectedSource,
    rightPanel,
  } from "$lib/stores/project";
  import type { SourceMeta, ClaimMeta } from "$lib/types";

  type NodeDatum = d3.SimulationNodeDatum & {
    id: string;
    type: "source" | "claim";
    label: string;
    color: string;
    size: number;
    data: SourceMeta | ClaimMeta;
    matchesFilter: boolean;
  };

  type LinkDatum = d3.SimulationLinkDatum<NodeDatum> & {
    source: string | NodeDatum;
    target: string | NodeDatum;
  };

  let container: HTMLDivElement;
  let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  let simulation: d3.Simulation<NodeDatum, LinkDatum>;
  let tooltip = $state({ visible: false, x: 0, y: 0, text: "" });
  let width = $state(600);
  let height = $state(400);

  // --- Filter state ---
  let allTags = $state<{ tag: string; count: number }[]>([]);
  let activeTags = $state<Set<string>>(new Set());
  let activeStatuses = $state<Set<string>>(new Set());
  let groupByTag = $state(false);

  const STATUS_OPTIONS: { key: string; label: string; colorClass: string }[] = [
    { key: "verified", label: "Verified", colorClass: "success" },
    { key: "flagged", label: "Flagged", colorClass: "warning" },
    { key: "needs-replacement", label: "Needs Replace", colorClass: "danger" },
  ];

  let activeFilterCount = $derived(activeTags.size + activeStatuses.size);

  function collectTags(srcList: SourceMeta[]) {
    const tagCounts = new Map<string, number>();
    for (const s of srcList) {
      if (s.tags) {
        for (const t of s.tags) {
          tagCounts.set(t, (tagCounts.get(t) || 0) + 1);
        }
      }
    }
    allTags = Array.from(tagCounts.entries())
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count);
  }

  function toggleTag(tag: string) {
    const next = new Set(activeTags);
    if (next.has(tag)) {
      next.delete(tag);
    } else {
      next.add(tag);
    }
    activeTags = next;
    render($sources, $claims);
  }

  function toggleStatus(key: string) {
    const next = new Set(activeStatuses);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    activeStatuses = next;
    render($sources, $claims);
  }

  function clearFilters() {
    activeTags = new Set();
    activeStatuses = new Set();
    render($sources, $claims);
  }

  function toggleGroupByTag() {
    groupByTag = !groupByTag;
    render($sources, $claims);
  }

  /** Compute tag brightness: interpolate opacity from 0.5 to 1.0 based on frequency */
  function tagOpacity(count: number): number {
    if (allTags.length <= 1) return 1;
    const max = allTags[0]?.count ?? 1;
    return 0.5 + 0.5 * (count / max);
  }

  function sourceMatchesFilter(s: SourceMeta): boolean {
    const tagOk =
      activeTags.size === 0 ||
      (s.tags != null && s.tags.some((t) => activeTags.has(t)));
    const statusOk =
      activeStatuses.size === 0 ||
      activeStatuses.has(s.status ?? "");
    return tagOk && statusOk;
  }

  const sourceColor = (status: string | null): string => {
    switch (status) {
      case "verified":
        return "#7aa2f7";
      case "flagged":
        return "#e0af68";
      case "needs-replacement":
        return "#f7768e";
      default:
        return "#565f89";
    }
  };

  const claimColor = (confidence: string): string => {
    switch (confidence) {
      case "high":
        return "#9ece6a";
      case "medium":
        return "#e0af68";
      default:
        return "#565f89";
    }
  };

  function buildGraph(
    srcList: SourceMeta[],
    claimList: ClaimMeta[]
  ): { nodes: NodeDatum[]; links: LinkDatum[] } {
    const hasFilters = activeTags.size > 0 || activeStatuses.size > 0;
    const matchingSrcKeys = new Set<string>();
    const claimIds = new Set(claimList.map((c) => c.id));
    const nodes: NodeDatum[] = [];
    const links: LinkDatum[] = [];

    // Determine which sources match filters
    for (const s of srcList) {
      if (sourceMatchesFilter(s)) {
        matchingSrcKeys.add(s.key);
      }
    }

    // Determine which claims are connected to matching sources
    const connectedClaimIds = new Set<string>();
    for (const s of srcList) {
      if (matchingSrcKeys.has(s.key) && s.evidence_for) {
        for (const cid of s.evidence_for) {
          if (claimIds.has(cid)) {
            connectedClaimIds.add(cid);
          }
        }
      }
    }

    for (const s of srcList) {
      const evidenceCount = s.evidence_for?.length ?? 0;
      const matches = !hasFilters || matchingSrcKeys.has(s.key);
      nodes.push({
        id: s.key,
        type: "source",
        label: s.title ?? s.key,
        color: sourceColor(s.status),
        size: Math.max(6, Math.min(20, 6 + evidenceCount * 2)),
        data: s,
        matchesFilter: matches,
      });

      if (s.evidence_for) {
        for (const claimId of s.evidence_for) {
          if (claimIds.has(claimId)) {
            links.push({ source: s.key, target: claimId });
          }
        }
      }
    }

    for (const c of claimList) {
      const matches = !hasFilters || connectedClaimIds.has(c.id);
      nodes.push({
        id: c.id,
        type: "claim",
        label: c.statement,
        color: claimColor(c.confidence),
        size: Math.max(8, Math.min(18, 6 + c.evidence_density * 3)),
        data: c,
        matchesFilter: matches,
      });
    }

    return { nodes, links };
  }

  /** Build a tag -> cluster center map for groupByTag force */
  function getTagCenters(srcList: SourceMeta[]): Map<string, { x: number; y: number }> {
    const tagSet = new Set<string>();
    for (const s of srcList) {
      if (s.tags) {
        for (const t of s.tags) tagSet.add(t);
      }
    }
    const tags = Array.from(tagSet);
    const centers = new Map<string, { x: number; y: number }>();
    const cols = Math.ceil(Math.sqrt(tags.length));
    for (let i = 0; i < tags.length; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      centers.set(tags[i], {
        x: (width / (cols + 1)) * (col + 1),
        y: (height / (Math.ceil(tags.length / cols) + 1)) * (row + 1),
      });
    }
    return centers;
  }

  function render(srcList: SourceMeta[], claimList: ClaimMeta[]) {
    if (!svg) return;

    collectTags(srcList);
    const { nodes, links } = buildGraph(srcList, claimList);

    // Clear previous content
    svg.select("g.graph-content").remove();
    const g = svg.append("g").attr("class", "graph-content");

    // Stop previous simulation
    if (simulation) simulation.stop();

    // Build tag centers for clustering force
    const tagCenters = groupByTag ? getTagCenters(srcList) : null;

    simulation = d3
      .forceSimulation<NodeDatum>(nodes)
      .force(
        "link",
        d3
          .forceLink<NodeDatum, LinkDatum>(links)
          .id((d) => d.id)
          .distance(80)
      )
      .force("charge", d3.forceManyBody().strength(-120))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<NodeDatum>().radius((d) => d.size + 4));

    // Group-by-tag clustering force
    if (tagCenters && tagCenters.size > 0) {
      const clusterStrength = 0.15;
      simulation.force("cluster", d3.forceX<NodeDatum>((d) => {
        if (d.type === "source") {
          const src = d.data as SourceMeta;
          if (src.tags && src.tags.length > 0) {
            const center = tagCenters.get(src.tags[0]);
            if (center) return center.x;
          }
        }
        return width / 2;
      }).strength(clusterStrength));
      simulation.force("clusterY", d3.forceY<NodeDatum>((d) => {
        if (d.type === "source") {
          const src = d.data as SourceMeta;
          if (src.tags && src.tags.length > 0) {
            const center = tagCenters.get(src.tags[0]);
            if (center) return center.y;
          }
        }
        return height / 2;
      }).strength(clusterStrength));
    }

    // Links
    const link = g
      .selectAll<SVGLineElement, LinkDatum>("line")
      .data(links)
      .join("line")
      .attr("stroke", "#3b3f5c")
      .attr("stroke-width", 1)
      .attr("stroke-opacity", (d) => {
        // Fade links connected to non-matching nodes
        const src = typeof d.source === "string" ? nodes.find(n => n.id === d.source) : d.source as NodeDatum;
        const tgt = typeof d.target === "string" ? nodes.find(n => n.id === d.target) : d.target as NodeDatum;
        if (src && !src.matchesFilter) return 0.1;
        if (tgt && !tgt.matchesFilter) return 0.1;
        return 0.6;
      });

    // Nodes group
    const node = g
      .selectAll<SVGGElement, NodeDatum>("g.node")
      .data(nodes)
      .join("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .style("opacity", (d) => (d.matchesFilter ? 1 : 0.15))
      .call(
        d3
          .drag<SVGGElement, NodeDatum>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Source nodes: circles
    node
      .filter((d) => d.type === "source")
      .append("circle")
      .attr("r", (d) => d.size)
      .attr("fill", (d) => d.color)
      .attr("fill-opacity", 0.85)
      .attr("stroke", (d) => d.color)
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.4);

    // Claim nodes: rotated squares (diamonds)
    node
      .filter((d) => d.type === "claim")
      .append("rect")
      .attr("width", (d) => d.size * 1.4)
      .attr("height", (d) => d.size * 1.4)
      .attr("x", (d) => (-d.size * 1.4) / 2)
      .attr("y", (d) => (-d.size * 1.4) / 2)
      .attr("transform", "rotate(45)")
      .attr("fill", (d) => d.color)
      .attr("fill-opacity", 0.85)
      .attr("stroke", (d) => d.color)
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.4);

    // Hover / click events
    node
      .on("mouseenter", (event: MouseEvent, d: NodeDatum) => {
        const truncated =
          d.label.length > 80 ? d.label.slice(0, 77) + "..." : d.label;
        tooltip = {
          visible: true,
          x: event.clientX,
          y: event.clientY,
          text: truncated,
        };
      })
      .on("mousemove", (event: MouseEvent) => {
        tooltip.x = event.clientX;
        tooltip.y = event.clientY;
      })
      .on("mouseleave", () => {
        tooltip.visible = false;
      })
      .on("click", (_event: MouseEvent, d: NodeDatum) => {
        if (d.type === "source") {
          selectedSource.set(d.id);
          rightPanel.set("source");
        }
      });

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as NodeDatum).x!)
        .attr("y1", (d) => (d.source as NodeDatum).y!)
        .attr("x2", (d) => (d.target as NodeDatum).x!)
        .attr("y2", (d) => (d.target as NodeDatum).y!);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });
  }

  onMount(() => {
    const rect = container.getBoundingClientRect();
    width = rect.width || 600;
    height = rect.height || 400;

    svg = d3
      .select(container)
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", `0 0 ${width} ${height}`);

    // Zoom
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 5])
      .on("zoom", (event) => {
        svg.select("g.graph-content").attr("transform", event.transform);
      });

    svg.call(zoom);

    // Resize observer
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        width = entry.contentRect.width;
        height = entry.contentRect.height;
        svg.attr("viewBox", `0 0 ${width} ${height}`);
        if (simulation) {
          simulation
            .force("center", d3.forceCenter(width / 2, height / 2))
            .alpha(0.3)
            .restart();
        }
      }
    });
    observer.observe(container);

    // Subscribe to stores
    const unsubSources = sources.subscribe(() => {
      render($sources, $claims);
    });
    const unsubClaims = claims.subscribe(() => {
      render($sources, $claims);
    });

    // Initial render
    render($sources, $claims);

    return () => {
      observer.disconnect();
      unsubSources();
      unsubClaims();
      if (simulation) simulation.stop();
      svg?.remove();
    };
  });
</script>

<div class="relative h-full w-full overflow-hidden bg-bg" bind:this={container}>
  <!-- Filter bar -->
  {#if $sources.length > 0 || $claims.length > 0}
    <div
      class="absolute left-0 right-0 top-0 z-20 flex h-6 items-center gap-1.5 border-b border-border bg-bg-secondary px-2"
    >
      <!-- All / Reset button -->
      <button
        class="flex-shrink-0 rounded px-1.5 text-[10px] leading-4 transition-colors
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
          class="flex-shrink-0 rounded px-1.5 text-[10px] leading-4 transition-colors
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
        class="flex-shrink-0 rounded px-1.5 text-[10px] leading-4 transition-colors
          {groupByTag
            ? 'bg-accent/20 text-accent'
            : 'bg-bg-tertiary text-text-muted hover:text-text'}"
        onclick={toggleGroupByTag}
      >
        Group
      </button>

      <span class="h-3 w-px flex-shrink-0 bg-border"></span>

      <!-- Tag pills (scrollable) -->
      <div class="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
        {#each allTags as { tag, count }}
          <button
            class="flex-shrink-0 whitespace-nowrap rounded px-1.5 text-[10px] leading-4 transition-colors
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
  {/if}

  {#if $sources.length === 0 && $claims.length === 0}
    <div
      class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 text-text-muted"
    >
      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <circle cx="6" cy="6" r="3" />
        <circle cx="18" cy="6" r="3" />
        <circle cx="12" cy="18" r="3" />
        <line x1="8.5" y1="7.5" x2="10" y2="16" />
        <line x1="15.5" y1="7.5" x2="14" y2="16" />
        <line x1="9" y1="6" x2="15" y2="6" />
      </svg>
      <span class="text-xs">No sources or claims yet</span>
    </div>
  {/if}

  {#if tooltip.visible}
    <div
      class="pointer-events-none fixed z-50 max-w-64 rounded border border-border bg-bg-secondary px-2 py-1 text-xs text-text shadow-lg"
      style="left: {tooltip.x + 12}px; top: {tooltip.y - 8}px;"
    >
      {tooltip.text}
    </div>
  {/if}
</div>
