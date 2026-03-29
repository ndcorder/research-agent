<script lang="ts">
  import { onMount } from "svelte";
  import { select } from "d3-selection";
  import type { Selection } from "d3-selection";
  import { zoom as d3zoom } from "d3-zoom";
  import { drag as d3drag } from "d3-drag";
  import { scalePoint } from "d3-scale";
  import type { Simulation, ForceLink } from "d3-force";
  import "d3-transition";
  import {
    sources,
    claims,
    selectedSource,
    selectedClaim,
    rightPanel,
    projectDir,
  } from "$lib/stores/project";
  import { readFile, updateSourceStatus } from "$lib/utils/ipc";
  import type { SourceMeta, ClaimMeta } from "$lib/types";
  import type { NodeDatum, LinkDatum } from "./graphUtils";
  import {
    buildGraph,
    getTagCenters,
    parseTexCoCitations,
    computeSectionPositions,
    SECTION_ORDER,
    edgeColor,
    edgeWidth,
    claimFill,
    detectGaps,
    forceSimulation,
    forceLink,
    forceManyBody,
    forceCenter,
    forceCollide,
    forceX,
    forceY,
  } from "./graphUtils";
  import type { GapReport } from "./graphUtils";
  import GraphTooltip from "./GraphTooltip.svelte";
  import GraphFilterBar from "./GraphFilterBar.svelte";
  import GraphTable from "./GraphTable.svelte";
  import ContextMenu from "$lib/components/ui/ContextMenu.svelte";
  import type { ContextMenuItem } from "$lib/components/ui/ContextMenu.svelte";
  import ImpactOverlay from "./ImpactOverlay.svelte";
  import SelectionBar from "./SelectionBar.svelte";
  import type { FilterState, LayoutMode } from "./GraphFilterBar.svelte";

  let container: HTMLDivElement;
  let svg: Selection<SVGSVGElement, unknown, null, undefined>;
  let simulation: Simulation<NodeDatum, LinkDatum>;
  let g: Selection<SVGGElement, unknown, null, undefined>;
  let renderError = $state(false);
  let tooltip = $state({ visible: false, x: 0, y: 0, text: "" });
  let width = $state(600);
  let height = $state(400);

  // Filter state (received from GraphFilterBar)
  let activeTags = $state<Set<string>>(new Set());
  let activeStatuses = $state<Set<string>>(new Set());
  let groupByTag = $state(false);
  let layoutMode = $state<LayoutMode>("force");

  // Context menu state
  let contextMenu = $state({
    visible: false,
    x: 0,
    y: 0,
    items: [] as ContextMenuItem[],
  });

  // Impact overlay state
  let impactOverlay = $state({ visible: false, sourceKey: "" });

  // Multi-select state
  let selectedNodes = $state<Set<string>>(new Set());

  // Hidden nodes (from "hide" action)
  let hiddenNodes = $state<Set<string>>(new Set());

  // Cache for LaTeX co-citation data
  let texCoCitations = $state<string[][]>([]);

  // Evidence gap state (always-on detection)
  let gapReport = $state<GapReport>({
    underSupportedClaims: [],
    orphanSources: [],
    fragileSections: [],
  });
  let showGaps = $state(false);

  // Keyboard navigation state
  let focusedNodeIndex = $state<number>(-1);
  let currentNodes = $state<NodeDatum[]>([]);
  let currentLinks = $state<LinkDatum[]>([]);

  // Debounce timer for ResizeObserver
  let resizeTimer: ReturnType<typeof setTimeout> | undefined;

  async function loadTexCoCitations() {
    const dir = $projectDir;
    if (!dir) return;
    try {
      const tex = await readFile(`${dir}/main.tex`);
      texCoCitations = parseTexCoCitations(tex);
    } catch {
      texCoCitations = [];
    }
  }

  function onFilterChange(filter: FilterState) {
    activeTags = filter.activeTags;
    activeStatuses = filter.activeStatuses;
    groupByTag = filter.groupByTag;
    showGaps = filter.showGaps;
    render($sources, $claims);
  }

  function onLayoutChange(mode: LayoutMode) {
    layoutMode = mode;
    if (mode !== "table") {
      render($sources, $claims);
    }
  }

  function closeContextMenu() {
    contextMenu.visible = false;
  }

  function buildContextMenuItems(
    nodeId: string,
    nodeType: "source" | "claim",
  ): ContextMenuItem[] {
    const items: ContextMenuItem[] = [];

    if (nodeType === "source") {
      items.push({
        label: "View details",
        action: () => {
          selectedSource.set(nodeId);
          rightPanel.set("source");
        },
      });
      items.push({
        label: "Impact analysis",
        action: () => {
          impactOverlay = { visible: true, sourceKey: nodeId };
        },
      });
      items.push({
        label: selectedNodes.has(nodeId) ? "Deselect" : "Select",
        separator: true,
        action: () => {
          toggleNodeSelection(nodeId);
        },
      });
    } else {
      items.push({
        label: "View claim",
        action: () => {
          selectedClaim.set(nodeId);
          rightPanel.set("claim");
        },
      });
    }

    return items;
  }

  function toggleNodeSelection(nodeId: string) {
    const next = new Set(selectedNodes);
    if (next.has(nodeId)) {
      next.delete(nodeId);
    } else {
      next.add(nodeId);
    }
    selectedNodes = next;
  }

  async function onSelectionAction(action: string, nodeIds: string[]) {
    if (action === "flag") {
      const dir = $projectDir;
      if (!dir) return;
      for (const key of nodeIds) {
        try {
          await updateSourceStatus(`${dir}/research/sources/${key}.md`, "flagged");
        } catch (e) {
          console.error(`Failed to flag source ${key}:`, e);
        }
      }
    } else if (action === "hide") {
      const next = new Set(hiddenNodes);
      for (const key of nodeIds) next.add(key);
      hiddenNodes = next;
      selectedNodes = new Set();
      render($sources, $claims);
    } else if (action.startsWith("tag:")) {
      console.log("Tag action not yet implemented:", action, nodeIds);
    }
  }

  function clearSelection() {
    selectedNodes = new Set();
  }

  function linkKeyFn(d: LinkDatum): string {
    const sId = typeof d.source === "string" ? d.source : d.source.id;
    const tId = typeof d.target === "string" ? d.target : d.target.id;
    return `${sId}->${tId}`;
  }

  function baseLinkOpacity(d: LinkDatum, nodeMap: Map<string, NodeDatum>): number {
    const src =
      typeof d.source === "string"
        ? nodeMap.get(d.source as string)
        : (d.source as NodeDatum);
    const tgt =
      typeof d.target === "string"
        ? nodeMap.get(d.target as string)
        : (d.target as NodeDatum);
    if (src && !src.matchesFilter) return 0.05;
    if (tgt && !tgt.matchesFilter) return 0.05;
    return 0.2;
  }

  function render(srcList: SourceMeta[], claimList: ClaimMeta[]) {
    if (!svg || !g || layoutMode === "table") return;

    try {
    renderError = false;

    // Filter out hidden nodes
    const visibleSrcList = hiddenNodes.size > 0
      ? srcList.filter((s) => !hiddenNodes.has(s.key))
      : srcList;

    const { nodes, links } = buildGraph(
      visibleSrcList,
      claimList,
      activeTags,
      activeStatuses,
      texCoCitations,
    );

    // Build node lookup map for O(1) access in link opacity
    const nodeMap = new Map<string, NodeDatum>(nodes.map((n) => [n.id, n]));

    // Update defs for clipPath (half-fill for abstract-only sources)
    svg.select("defs.graph-defs").remove();
    svg.select("g.section-labels").remove();

    const defs = svg.append("defs").attr("class", "graph-defs");
    for (const n of nodes) {
      if (n.type === "source") {
        const src = n.data as SourceMeta;
        if (src.access_level === "ABSTRACT-ONLY") {
          defs
            .append("clipPath")
            .attr("id", `half-${n.id}`)
            .append("rect")
            .attr("x", -n.size)
            .attr("y", 0)
            .attr("width", n.size * 2)
            .attr("height", n.size);
        }
      }
    }

    // Build tag centers for clustering force
    const tagCenters = groupByTag
      ? getTagCenters(visibleSrcList, width, height)
      : null;

    if (!simulation) {
      // First render: create simulation
      simulation = forceSimulation<NodeDatum>(nodes)
        .force(
          "link",
          forceLink<NodeDatum, LinkDatum>(links)
            .id((d) => d.id)
            .distance((d) => (d.kind === "cocitation" ? 50 : 80)),
        )
        .force("charge", forceManyBody().strength(-80))
        .force(
          "collision",
          forceCollide<NodeDatum>().radius((d) => d.size + 4),
        );
    } else {
      // Subsequent renders: update simulation in-place (no recreate)
      simulation.nodes(nodes);
      (
        simulation.force("link") as ForceLink<NodeDatum, LinkDatum>
      )?.links(links);
      simulation.alpha(0.5).restart();
    }

    if (layoutMode === "section") {
      const sectionPositions = computeSectionPositions(
        nodes,
        links,
        width,
        height,
      );
      simulation.force(
        "sectionX",
        forceX<NodeDatum>(
          (d) => sectionPositions.get(d.id)?.targetX ?? width / 2,
        ).strength(0.8),
      );
      simulation.force(
        "sectionY",
        forceY<NodeDatum>(
          (d) => sectionPositions.get(d.id)?.targetY ?? height / 2,
        ).strength(0.3),
      );
      simulation.force("center", null);
      simulation.force("cluster", null);
      simulation.force("clusterY", null);

      const xScale = scalePoint<string>()
        .domain(SECTION_ORDER as unknown as string[])
        .range([60, width - 60]);

      const labelGroup = svg
        .append("g")
        .attr("class", "section-labels");
      for (const sec of SECTION_ORDER) {
        const x = xScale(sec) ?? width / 2;
        labelGroup
          .append("text")
          .attr("x", x)
          .attr("y", height - 12)
          .attr("fill", "var(--color-text-muted)")
          .attr("font-size", "10px")
          .attr("text-anchor", "middle")
          .text(sec.replace("_", " "));
      }
    } else {
      simulation.force("center", forceCenter(width / 2, height / 2));
      simulation.force("sectionX", null);
      simulation.force("sectionY", null);

      if (tagCenters && tagCenters.size > 0) {
        const clusterStrength = 0.15;
        simulation.force(
          "cluster",
          forceX<NodeDatum>((d) => {
            if (d.type === "source") {
              const src = d.data as SourceMeta;
              if (src.tags && src.tags.length > 0) {
                const center = tagCenters.get(src.tags[0]);
                if (center) return center.x;
              }
            }
            return width / 2;
          }).strength(clusterStrength),
        );
        simulation.force(
          "clusterY",
          forceY<NodeDatum>((d) => {
            if (d.type === "source") {
              const src = d.data as SourceMeta;
              if (src.tags && src.tags.length > 0) {
                const center = tagCenters.get(src.tags[0]);
                if (center) return center.y;
              }
            }
            return height / 2;
          }).strength(clusterStrength),
        );
      } else {
        simulation.force("cluster", null);
        simulation.force("clusterY", null);
      }
    }

    // Links -- d3 enter/update/exit join with curved paths
    const link = g
      .selectAll<SVGPathElement, LinkDatum>("path.link")
      .data(links, linkKeyFn)
      .join(
        (enter) =>
          enter
            .append("path")
            .attr("class", "link")
            .attr("fill", "none")
            .attr("stroke", (d) => edgeColor(d.kind))
            .attr("stroke-width", (d) => edgeWidth(d.strength ?? 1))
            .attr("stroke-opacity", 0)
            .call((sel) =>
              sel
                .transition()
                .duration(400)
                .attr("stroke-opacity", (d: LinkDatum) =>
                  baseLinkOpacity(d, nodeMap),
                ),
            ),
        (update) =>
          update.call((sel) =>
            sel
              .transition()
              .duration(300)
              .attr("stroke-opacity", (d: LinkDatum) =>
                baseLinkOpacity(d, nodeMap),
              )
              .attr("stroke", (d: LinkDatum) => edgeColor(d.kind)),
          ),
        (exit) =>
          exit.call((sel) =>
            sel
              .transition()
              .duration(300)
              .attr("stroke-opacity", 0)
              .remove(),
          ),
      );

    // Nodes -- d3 enter/update/exit join
    const node = g
      .selectAll<SVGGElement, NodeDatum>("g.node")
      .data(nodes, (d) => d.id)
      .join(
        (enter) => {
          const gEnter = enter
            .append("g")
            .attr("class", "node")
            .style("cursor", "pointer")
            .style("opacity", 0);

          // Source nodes: circles with revised encoding
          gEnter
            .filter((d) => d.type === "source")
            .each(function (d) {
              const src = d.data as SourceMeta;
              const el = select(this);
              const isFlagged = src.status === "flagged";
              const isNeedsReplacement = src.status === "needs-replacement";
              const isAbstractOnly = src.access_level === "ABSTRACT-ONLY";

              if (isAbstractOnly) {
                el.append("circle")
                  .attr("r", d.size)
                  .attr("fill", "transparent")
                  .attr("stroke", "#565f89")
                  .attr("stroke-width", 1.5);
                el.append("circle")
                  .attr("r", d.size)
                  .attr("fill", "#565f89")
                  .attr("fill-opacity", 0.85)
                  .attr("clip-path", `url(#half-${d.id})`);
              } else if (isFlagged) {
                el.append("circle")
                  .attr("r", d.size)
                  .attr("fill", "transparent")
                  .attr("stroke", "#565f89")
                  .attr("stroke-width", 1.5)
                  .attr("stroke-opacity", 1);
              } else {
                el.append("circle")
                  .attr("r", d.size)
                  .attr("fill", "#565f89")
                  .attr("fill-opacity", 0.85)
                  .attr("stroke", "#565f89")
                  .attr("stroke-width", 1.5)
                  .attr("stroke-opacity", 0.4);
              }

              if (isNeedsReplacement) {
                const s = d.size * 0.5;
                el.append("line")
                  .attr("x1", -s).attr("y1", -s)
                  .attr("x2", s).attr("y2", s)
                  .attr("stroke", "#f7768e")
                  .attr("stroke-width", 2);
                el.append("line")
                  .attr("x1", s).attr("y1", -s)
                  .attr("x2", -s).attr("y2", s)
                  .attr("stroke", "#f7768e")
                  .attr("stroke-width", 2);
              }
            });

          // Claim nodes: rotated squares (diamonds) with revised encoding
          gEnter
            .filter((d) => d.type === "claim")
            .each(function (d) {
              const claim = d.data as ClaimMeta;
              const el = select(this);
              const isWeakOrCritical =
                claim.strength === "WEAK" || claim.strength === "CRITICAL";
              el.append("rect")
                .attr("width", d.size * 1.4)
                .attr("height", d.size * 1.4)
                .attr("x", (-d.size * 1.4) / 2)
                .attr("y", (-d.size * 1.4) / 2)
                .attr("transform", "rotate(45)")
                .attr("fill", claimFill(claim.confidence))
                .attr("fill-opacity", 0.85)
                .attr("stroke", claimFill(claim.confidence))
                .attr("stroke-width", isWeakOrCritical ? 3 : 1.5)
                .attr("stroke-opacity", 0.4);
            });

          // Fade in
          gEnter
            .transition()
            .duration(400)
            .style("opacity", (d: NodeDatum) =>
              d.matchesFilter ? 1 : 0.15,
            );

          return gEnter;
        },
        (update) =>
          update.call((sel) =>
            sel
              .transition()
              .duration(300)
              .style("opacity", (d: NodeDatum) =>
                d.matchesFilter ? 1 : 0.15,
              ),
          ),
        (exit) =>
          exit.call((sel) =>
            sel.transition().duration(300).style("opacity", 0).remove(),
          ),
      )
      .call(
        d3drag<SVGGElement, NodeDatum>()
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
          }),
      );

    // Hover / click / right-click events (re-bound on merged selection)
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
        // Brighten connected edges on hover
        link.attr("stroke-opacity", (l: LinkDatum) => {
          const sId =
            typeof l.source === "string" ? l.source : l.source.id;
          const tId =
            typeof l.target === "string" ? l.target : l.target.id;
          if (sId === d.id || tId === d.id) return 0.8;
          return baseLinkOpacity(l, nodeMap);
        });
      })
      .on("mousemove", (event: MouseEvent) => {
        tooltip.x = event.clientX;
        tooltip.y = event.clientY;
      })
      .on("mouseleave", () => {
        tooltip.visible = false;
        // Restore edge opacity
        link.attr("stroke-opacity", (l: LinkDatum) =>
          baseLinkOpacity(l, nodeMap),
        );
      })
      .on("click", (event: MouseEvent, d: NodeDatum) => {
        if (event.shiftKey) {
          toggleNodeSelection(d.id);
          return;
        }
        if (d.type === "source") {
          selectedSource.set(d.id);
          rightPanel.set("source");
        } else {
          selectedClaim.set(d.id);
          rightPanel.set("claim");
        }
      })
      .on("contextmenu", (event: MouseEvent, d: NodeDatum) => {
        event.preventDefault();
        event.stopPropagation();
        contextMenu = {
          visible: true,
          x: event.clientX,
          y: event.clientY,
          items: buildContextMenuItems(d.id, d.type),
        };
      });

    // --- Evidence gap detection (always-on) ---
    const gaps = detectGaps(nodes, links);
    gapReport = gaps;
    currentNodes = nodes;
    currentLinks = links;
    focusedNodeIndex = -1;

    const gapClaimSet = new Set(gaps.underSupportedClaims);
    const gapOrphanSet = new Set(gaps.orphanSources);
    const gapNodeIds = new Set([...gapClaimSet, ...gapOrphanSet]);

    // Apply showGaps overlay: dim non-gap nodes
    if (showGaps) {
      node.style("opacity", (d: NodeDatum) =>
        gapNodeIds.has(d.id) ? 1 : 0.2,
      );
      link.attr("stroke-opacity", 0.08);
    }

    // Under-supported claim pulsing border overlay
    const pulseOverlay = g
      .selectAll<SVGRectElement, NodeDatum>("rect.gap-pulse")
      .data(
        nodes.filter((n) => n.type === "claim" && gapClaimSet.has(n.id)),
        (d) => d.id,
      )
      .join("rect")
      .attr("class", "gap-pulse")
      .attr("width", (d) => d.size * 1.4 + 4)
      .attr("height", (d) => d.size * 1.4 + 4)
      .attr("x", (d) => (-d.size * 1.4 - 4) / 2)
      .attr("y", (d) => (-d.size * 1.4 - 4) / 2)
      .attr("transform", "rotate(45)")
      .attr("fill", "none")
      .attr("stroke", "#e0af68")
      .attr("stroke-opacity", 0.7)
      .style("animation", "pulse-border 2s ease-in-out infinite")
      .style("pointer-events", "none");

    if (showGaps) {
      pulseOverlay.style("filter", "drop-shadow(0 0 4px #e0af68)");
    }

    // Orphan source badge: dimmed + "0" text
    const orphanBadge = g
      .selectAll<SVGGElement, NodeDatum>("g.orphan-badge")
      .data(
        nodes.filter((n) => n.type === "source" && gapOrphanSet.has(n.id)),
        (d) => d.id,
      )
      .join("g")
      .attr("class", "orphan-badge")
      .style("pointer-events", "none");

    orphanBadge
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("fill", "#e0af68")
      .attr("font-size", "9px")
      .attr("font-weight", "bold")
      .text("0");

    // Dim orphan source nodes to 40% opacity (unless showGaps highlights them)
    node
      .filter((d: NodeDatum) => d.type === "source" && gapOrphanSet.has(d.id))
      .style("opacity", showGaps ? 1 : 0.4);

    if (showGaps) {
      node
        .filter(
          (d: NodeDatum) => d.type === "source" && gapOrphanSet.has(d.id),
        )
        .style("filter", "drop-shadow(0 0 4px #e0af68)");
    }

    // --- Focus ring for keyboard navigation ---
    const focusRing = g
      .append("circle")
      .attr("class", "focus-ring")
      .attr("r", 0)
      .attr("fill", "none")
      .attr("stroke", "#7aa2f7")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .style("pointer-events", "none")
      .style("display", "none");

    // Tick -- curved bezier arcs + node transforms
    simulation.on("tick", () => {
      link.attr("d", (d: LinkDatum) => {
        const sx = (d.source as NodeDatum).x!,
          sy = (d.source as NodeDatum).y!;
        const tx = (d.target as NodeDatum).x!,
          ty = (d.target as NodeDatum).y!;
        const dx = tx - sx,
          dy = ty - sy;
        const dr = Math.sqrt(dx * dx + dy * dy) * 0.6;
        return `M${sx},${sy}A${dr},${dr} 0 0,1 ${tx},${ty}`;
      });

      node.attr("transform", (d: NodeDatum) => `translate(${d.x},${d.y})`);

      // Move gap overlays with their nodes
      pulseOverlay.attr("transform", (d) => `translate(${d.x},${d.y}) rotate(45)`);
      orphanBadge.attr("transform", (d) => `translate(${d.x},${d.y})`);

      // Update focus ring position
      if (focusedNodeIndex >= 0 && focusedNodeIndex < nodes.length) {
        const fn = nodes[focusedNodeIndex];
        focusRing
          .style("display", null)
          .attr("cx", fn.x ?? 0)
          .attr("cy", fn.y ?? 0)
          .attr("r", fn.size + 6);
      } else {
        focusRing.style("display", "none");
      }
    });
    } catch (err) {
      console.error("GraphView render error:", err);
      renderError = true;
    }
  }

  // --- Keyboard navigation ---
  function handleKeydown(event: KeyboardEvent) {
    if (currentNodes.length === 0) return;

    if (event.key === "Tab") {
      event.preventDefault();
      if (event.shiftKey) {
        focusedNodeIndex =
          focusedNodeIndex <= 0
            ? currentNodes.length - 1
            : focusedNodeIndex - 1;
      } else {
        focusedNodeIndex =
          focusedNodeIndex >= currentNodes.length - 1
            ? 0
            : focusedNodeIndex + 1;
      }
      return;
    }

    if (event.key === "Enter" && focusedNodeIndex >= 0) {
      event.preventDefault();
      const n = currentNodes[focusedNodeIndex];
      if (n.type === "source") {
        selectedSource.set(n.id);
        rightPanel.set("source");
      } else {
        selectedClaim.set(n.id);
        rightPanel.set("claim");
      }
      return;
    }

    if (event.key === "Escape") {
      focusedNodeIndex = -1;
      selectedSource.set("");
      selectedClaim.set("");
      return;
    }

    // Arrow keys: traverse to connected nodes via edges
    if (
      (event.key === "ArrowRight" || event.key === "ArrowDown") &&
      focusedNodeIndex >= 0
    ) {
      event.preventDefault();
      const next = findConnectedNode(focusedNodeIndex, 1);
      if (next >= 0) focusedNodeIndex = next;
      return;
    }

    if (
      (event.key === "ArrowLeft" || event.key === "ArrowUp") &&
      focusedNodeIndex >= 0
    ) {
      event.preventDefault();
      const prev = findConnectedNode(focusedNodeIndex, -1);
      if (prev >= 0) focusedNodeIndex = prev;
      return;
    }
  }

  function findConnectedNode(fromIdx: number, direction: number): number {
    const fromNode = currentNodes[fromIdx];
    if (!fromNode) return -1;

    const connected: string[] = [];
    for (const lnk of currentLinks) {
      const srcId =
        typeof lnk.source === "string" ? lnk.source : lnk.source.id;
      const tgtId =
        typeof lnk.target === "string" ? lnk.target : lnk.target.id;
      if (srcId === fromNode.id) connected.push(tgtId);
      else if (tgtId === fromNode.id) connected.push(srcId);
    }

    if (connected.length === 0) return -1;

    const connectedIndices = connected
      .map((id) => currentNodes.findIndex((n) => n.id === id))
      .filter((i) => i >= 0)
      .sort((a, b) => a - b);

    if (connectedIndices.length === 0) return -1;

    if (direction > 0) {
      const next = connectedIndices.find((i) => i > fromIdx);
      return next !== undefined ? next : connectedIndices[0];
    } else {
      const prev = [...connectedIndices].reverse().find((i) => i < fromIdx);
      return prev !== undefined ? prev : connectedIndices[connectedIndices.length - 1];
    }
  }

  onMount(() => {
    const rect = container.getBoundingClientRect();
    width = rect.width || 600;
    height = rect.height || 400;

    svg = select(container)
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("role", "img")
      .attr("aria-label", "Evidence graph showing sources and claims");

    // SVG accessibility title
    svg.append("title").text("Evidence graph showing sources and claims");

    // Create the persistent g.graph-content group once
    g = svg.append("g").attr("class", "graph-content");

    // Zoom
    const zoom = d3zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Resize observer with 150ms debounce
    const observer = new ResizeObserver(() => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const r = container.getBoundingClientRect();
        width = r.width;
        height = r.height;
        svg.attr("viewBox", `0 0 ${width} ${height}`);
        if (simulation) {
          simulation
            .force("center", forceCenter(width / 2, height / 2))
            .alpha(0.3)
            .restart();
        }
      }, 150);
    });
    observer.observe(container);

    // Load LaTeX co-citations then do initial render
    loadTexCoCitations().then(() => {
      render($sources, $claims);
    });

    return () => {
      clearTimeout(resizeTimer);
      observer.disconnect();
      if (simulation) simulation.stop();
      svg?.remove();
    };
  });

  // Reactive render: replaces manual store subscriptions.
  // Batches sources+claims updates in same tick into one render call.
  $effect(() => {
    const s = $sources;
    const c = $claims;
    render(s, c);
  });
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="relative h-full w-full overflow-hidden bg-bg"
  bind:this={container}
  tabindex="0"
  role="application"
  aria-label="Evidence graph with keyboard navigation"
  onkeydown={handleKeydown}
>
  {#if $sources.length > 0 || $claims.length > 0}
    <GraphFilterBar
      sources={$sources}
      {onFilterChange}
      {layoutMode}
      {onLayoutChange}
    />
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
  {:else if layoutMode === "table"}
    <div class="absolute inset-0 pt-6">
      <GraphTable sources={$sources} claims={$claims} />
    </div>
  {/if}

  <GraphTooltip
    visible={tooltip.visible}
    x={tooltip.x}
    y={tooltip.y}
    text={tooltip.text}
  />

  <ContextMenu
    items={contextMenu.items}
    x={contextMenu.x}
    y={contextMenu.y}
    visible={contextMenu.visible}
    onclose={closeContextMenu}
  />

  <ImpactOverlay
    sourceKey={impactOverlay.sourceKey}
    sources={$sources}
    claims={$claims}
    visible={impactOverlay.visible}
    onclose={() => (impactOverlay.visible = false)}
  />

  <SelectionBar
    {selectedNodes}
    sources={$sources}
    onaction={onSelectionAction}
    onclear={clearSelection}
  />

  {#if gapReport.underSupportedClaims.length > 0 || gapReport.orphanSources.length > 0 || gapReport.fragileSections.length > 0}
    <div class="absolute bottom-1 left-2 right-2 text-xs text-text-muted pointer-events-none">
      {gapReport.underSupportedClaims.length} weak claims &middot; {gapReport.orphanSources.length} orphan sources &middot; {gapReport.fragileSections.length} fragile sections
    </div>
  {/if}
</div>

<style>
  @keyframes pulse-border {
    0%,
    100% {
      stroke-width: 1.5;
    }
    50% {
      stroke-width: 3.5;
    }
  }
</style>
