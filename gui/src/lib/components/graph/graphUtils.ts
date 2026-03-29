import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  forceX,
  forceY,
} from "d3-force";
import type { SimulationNodeDatum, SimulationLinkDatum } from "d3-force";
import { scalePoint, scaleLinear } from "d3-scale";
import { interpolateRgb } from "d3-interpolate";
import type { SourceMeta, ClaimMeta } from "$lib/types";

export {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  forceX,
  forceY,
};

export type NodeDatum = SimulationNodeDatum & {
  id: string;
  type: "source" | "claim";
  label: string;
  color: string;
  size: number;
  data: SourceMeta | ClaimMeta;
  matchesFilter: boolean;
};

export type LinkDatum = SimulationLinkDatum<NodeDatum> & {
  source: string | NodeDatum;
  target: string | NodeDatum;
  kind?: "evidence" | "cocitation" | "contradicts";
  strength?: number;
};

export const sourceColor = (status: string | null): string => {
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

export const claimColor = (confidence: string): string => {
  switch (confidence) {
    case "high":
      return "#9ece6a";
    case "medium":
      return "#e0af68";
    default:
      return "#565f89";
  }
};

/** Build a relative density color scale for claim nodes.
 *  Uses the paper's own density distribution to set thresholds. */
export function densityColorScale(
  claims: ClaimMeta[]
): (density: number) => string {
  const densities = claims.map((c) => c.evidence_density).filter((d) => d >= 0);
  if (densities.length === 0) {
    return () => "#565f89";
  }
  const sorted = [...densities].sort((a, b) => a - b);
  const p25 = sorted[Math.floor(sorted.length * 0.25)] ?? 1;
  const p75 = sorted[Math.floor(sorted.length * 0.75)] ?? 4;
  const lo = Math.min(p25, 1);
  const hi = Math.max(p75, lo + 1);

  const scale = scaleLinear<string>()
    .domain([0, lo, hi])
    .range(["#f7768e", "#e0af68", "#9ece6a"])
    .interpolate(interpolateRgb)
    .clamp(true);

  return (density: number) => scale(density);
}

// --- Revised colorblind-safe visual encoding ---

/** Edge colors (colorblind-safe) */
export const edgeColor = (kind?: string): string => {
  if (kind === "contradicts") return "#e0af68"; // orange
  if (kind === "cocitation") return "#565f89"; // gray
  return "#7aa2f7"; // blue (supports/evidence - default)
};

/** Edge width (3 levels only) */
export const edgeWidth = (strength: number): number => {
  if (strength >= 4) return 4;
  if (strength >= 2) return 2.5;
  return 1.2;
};

/** Claim fill by confidence (grayscale) */
export const claimFill = (confidence: string): string => {
  if (confidence === "high") return "#c0caf5";
  if (confidence === "medium") return "#787c99";
  return "#3b3f5c";
};

/** Parse source keys from a claim's evidence_sources string.
 *  Format: "gordon2002 (FT,direct)=4, salas2025 (AO,direct)=2, ..." */
export function extractSourceKeys(evidenceStr: string | undefined): string[] {
  if (!evidenceStr) return [];
  return evidenceStr
    .split(",")
    .map((entry) => entry.trim().split(/\s/)[0])
    .filter(Boolean);
}

/** Parse \cite{}, \citep{}, \citet{} commands from LaTeX to find co-cited source groups */
export function parseTexCoCitations(tex: string): string[][] {
  const groups: string[][] = [];
  const re = /\\cite[pt]?\*?\{([^}]+)\}/g;
  let m;
  while ((m = re.exec(tex)) !== null) {
    const keys = m[1]
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
    if (keys.length >= 2) {
      groups.push(keys);
    }
  }
  return groups;
}

export function sourceMatchesFilter(
  s: SourceMeta,
  activeTags: Set<string>,
  activeStatuses: Set<string>,
): boolean {
  const tagOk =
    activeTags.size === 0 ||
    (s.tags != null && s.tags.some((t) => activeTags.has(t)));
  const statusOk =
    activeStatuses.size === 0 || activeStatuses.has(s.status ?? "");
  return tagOk && statusOk;
}

export function buildGraph(
  srcList: SourceMeta[],
  claimList: ClaimMeta[],
  activeTags: Set<string>,
  activeStatuses: Set<string>,
  texCoCitations: string[][],
): { nodes: NodeDatum[]; links: LinkDatum[] } {
  const getDensityColor = densityColorScale(claimList);
  const hasFilters = activeTags.size > 0 || activeStatuses.size > 0;
  const matchingSrcKeys = new Set<string>();
  const srcKeySet = new Set(srcList.map((s) => s.key));
  const nodes: NodeDatum[] = [];
  const links: LinkDatum[] = [];
  const linkSet = new Set<string>();

  // Build claim->source links from claims' evidence_sources field
  const claimToSources = new Map<string, string[]>();
  const sourceToClaimCount = new Map<string, number>();
  for (const c of claimList) {
    const keys = extractSourceKeys(c.evidence_sources);
    const validKeys = keys.filter((k) => srcKeySet.has(k));
    claimToSources.set(c.id, validKeys);
    for (const k of validKeys) {
      sourceToClaimCount.set(k, (sourceToClaimCount.get(k) || 0) + 1);
    }
  }

  // Also check source-side evidence_for (original approach)
  for (const s of srcList) {
    if (s.evidence_for) {
      for (const _cid of s.evidence_for) {
        sourceToClaimCount.set(
          s.key,
          (sourceToClaimCount.get(s.key) || 0) + 1,
        );
      }
    }
  }

  // Determine which sources match filters
  for (const s of srcList) {
    if (sourceMatchesFilter(s, activeTags, activeStatuses)) {
      matchingSrcKeys.add(s.key);
    }
  }

  // Determine which claims are connected to matching sources
  const connectedClaimIds = new Set<string>();
  for (const [cid, keys] of claimToSources) {
    if (keys.some((k) => matchingSrcKeys.has(k))) {
      connectedClaimIds.add(cid);
    }
  }

  for (const s of srcList) {
    const evidenceCount = sourceToClaimCount.get(s.key) ?? 0;
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
  }

  for (const c of claimList) {
    const matches = !hasFilters || connectedClaimIds.has(c.id);
    nodes.push({
      id: c.id,
      type: "claim",
      label: c.statement,
      color: getDensityColor(c.evidence_density ?? 0),
      size: Math.max(8, Math.min(18, 6 + (c.evidence_density ?? 0) * 3)),
      data: c,
      matchesFilter: matches,
    });

    // Create links from claims' evidence_sources
    const keys = claimToSources.get(c.id) ?? [];
    for (const srcKey of keys) {
      const lk = `${srcKey}->${c.id}`;
      if (!linkSet.has(lk)) {
        linkSet.add(lk);
        links.push({ source: srcKey, target: c.id, kind: "evidence" });
      }
    }
  }

  // Also add links from source-side evidence_for (fallback)
  const claimIdSet = new Set(claimList.map((c) => c.id));
  for (const s of srcList) {
    if (s.evidence_for) {
      for (const claimId of s.evidence_for) {
        if (claimIdSet.has(claimId)) {
          if (!linkSet.has(`${s.key}->${claimId}`)) {
            linkSet.add(`${s.key}->${claimId}`);
            links.push({
              source: s.key,
              target: claimId,
              kind: "evidence",
            });
          }
        }
      }
    }
  }

  // Co-citation links from claims
  for (const [, keys] of claimToSources) {
    const valid = keys.filter((k) => srcKeySet.has(k));
    for (let i = 0; i < valid.length; i++) {
      for (let j = i + 1; j < valid.length; j++) {
        const a = valid[i],
          b = valid[j];
        const key = a < b ? `${a}<->${b}` : `${b}<->${a}`;
        if (!linkSet.has(key)) {
          linkSet.add(key);
          links.push({ source: a, target: b, kind: "cocitation" });
        }
      }
    }
  }

  // LaTeX co-citation links
  for (const group of texCoCitations) {
    const valid = group.filter((k) => srcKeySet.has(k));
    for (let i = 0; i < valid.length; i++) {
      for (let j = i + 1; j < valid.length; j++) {
        const a = valid[i],
          b = valid[j];
        const key = a < b ? `${a}<->${b}` : `${b}<->${a}`;
        if (!linkSet.has(key)) {
          linkSet.add(key);
          links.push({ source: a, target: b, kind: "cocitation" });
        }
      }
    }
  }

  return { nodes, links };
}

// --------------- Evidence Gap Detection ---------------

export interface GapReport {
  underSupportedClaims: string[]; // claims with < 2 supporting sources
  orphanSources: string[]; // sources connected to 0 claims
  fragileSections: string[]; // sections where all claims depend on single source
}

export function detectGaps(nodes: NodeDatum[], links: LinkDatum[]): GapReport {
  const claimEvidenceCount = new Map<string, number>();
  const sourceEvidenceCount = new Map<string, number>();
  const claimIds = new Set<string>();
  const sourceIds = new Set<string>();

  for (const n of nodes) {
    if (n.type === "claim") claimIds.add(n.id);
    if (n.type === "source") sourceIds.add(n.id);
  }

  for (const id of claimIds) claimEvidenceCount.set(id, 0);
  for (const id of sourceIds) sourceEvidenceCount.set(id, 0);

  for (const link of links) {
    if (link.kind !== "evidence") continue;
    const srcId =
      typeof link.source === "string" ? link.source : link.source.id;
    const tgtId =
      typeof link.target === "string" ? link.target : link.target.id;

    if (sourceIds.has(srcId) && claimIds.has(tgtId)) {
      claimEvidenceCount.set(tgtId, (claimEvidenceCount.get(tgtId) ?? 0) + 1);
      sourceEvidenceCount.set(
        srcId,
        (sourceEvidenceCount.get(srcId) ?? 0) + 1,
      );
    }
    if (claimIds.has(srcId) && sourceIds.has(tgtId)) {
      claimEvidenceCount.set(srcId, (claimEvidenceCount.get(srcId) ?? 0) + 1);
      sourceEvidenceCount.set(
        tgtId,
        (sourceEvidenceCount.get(tgtId) ?? 0) + 1,
      );
    }
  }

  const underSupportedClaims: string[] = [];
  for (const [id, count] of claimEvidenceCount) {
    if (count < 2) underSupportedClaims.push(id);
  }

  const orphanSources: string[] = [];
  for (const [id, count] of sourceEvidenceCount) {
    if (count === 0) orphanSources.push(id);
  }

  // Fragile sections: all claims depend on same single source
  const sectionClaims = new Map<string, string[]>();
  for (const n of nodes) {
    if (n.type === "claim") {
      const claim = n.data as ClaimMeta;
      const section = claim.section || "unknown";
      if (!sectionClaims.has(section)) sectionClaims.set(section, []);
      sectionClaims.get(section)!.push(n.id);
    }
  }

  const claimSources = new Map<string, Set<string>>();
  for (const link of links) {
    if (link.kind !== "evidence") continue;
    const srcId =
      typeof link.source === "string" ? link.source : link.source.id;
    const tgtId =
      typeof link.target === "string" ? link.target : link.target.id;
    if (sourceIds.has(srcId) && claimIds.has(tgtId)) {
      if (!claimSources.has(tgtId)) claimSources.set(tgtId, new Set());
      claimSources.get(tgtId)!.add(srcId);
    }
  }

  const fragileSections: string[] = [];
  for (const [section, cids] of sectionClaims) {
    if (cids.length === 0) continue;
    const allSectionSources = new Set<string>();
    for (const cid of cids) {
      const srcs = claimSources.get(cid);
      if (srcs) {
        for (const s of srcs) allSectionSources.add(s);
      }
    }
    if (allSectionSources.size === 1) {
      const theSource = Array.from(allSectionSources)[0];
      const allSingle = cids.every((cid) => {
        const srcs = claimSources.get(cid);
        return srcs && srcs.has(theSource) && srcs.size <= 1;
      });
      if (allSingle) fragileSections.push(section);
    }
  }

  return { underSupportedClaims, orphanSources, fragileSections };
}

/** Collect all tags from sources with occurrence counts. */
export function collectTags(sources: SourceMeta[]): Map<string, number> {
  const tagCounts = new Map<string, number>();
  for (const s of sources) {
    if (s.tags) {
      for (const t of s.tags) {
        tagCounts.set(t, (tagCounts.get(t) || 0) + 1);
      }
    }
  }
  return tagCounts;
}

/** Build a tag -> cluster center map for groupByTag force */
export function getTagCenters(
  srcList: SourceMeta[],
  width: number,
  height: number,
): Map<string, { x: number; y: number }> {
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

/** Section order for section-flow layout */
export const SECTION_ORDER = [
  "introduction",
  "related_work",
  "methods",
  "results",
  "discussion",
  "conclusion",
] as const;

/** Compute target positions for section-flow layout.
 *  Claims are placed at their section's X column, distributed vertically.
 *  Sources float at the centroid of their connected claims. */
export function computeSectionPositions(
  nodes: NodeDatum[],
  links: LinkDatum[],
  width: number,
  height: number,
): Map<string, { targetX: number; targetY: number }> {
  const padding = 60;
  const xScale = scalePoint<string>()
    .domain(SECTION_ORDER as unknown as string[])
    .range([padding, width - padding]);

  const positions = new Map<string, { targetX: number; targetY: number }>();

  // Group claim nodes by section
  const sectionClaimsMap = new Map<string, NodeDatum[]>();
  for (const sec of SECTION_ORDER) {
    sectionClaimsMap.set(sec, []);
  }

  for (const n of nodes) {
    if (n.type === "claim") {
      const claim = n.data as ClaimMeta;
      const sec = claim.section ?? "introduction";
      const bucket = sectionClaimsMap.get(sec);
      if (bucket) {
        bucket.push(n);
      } else {
        sectionClaimsMap.get("introduction")!.push(n);
      }
    }
  }

  // Position claims: X from section scale, Y distributed vertically
  const yPadding = 40;
  for (const [sec, claimNodes] of sectionClaimsMap) {
    const x = xScale(sec) ?? width / 2;
    const count = claimNodes.length;
    for (let i = 0; i < count; i++) {
      const y =
        count === 1
          ? height / 2
          : yPadding + ((height - 2 * yPadding) / (count - 1)) * i;
      positions.set(claimNodes[i].id, { targetX: x, targetY: y });
    }
  }

  // Build source -> connected claim IDs lookup from links
  const sourceToConnected = new Map<string, string[]>();
  for (const link of links) {
    if (link.kind === "cocitation") continue;
    const srcId =
      typeof link.source === "string" ? link.source : link.source.id;
    const tgtId =
      typeof link.target === "string" ? link.target : link.target.id;
    if (positions.has(tgtId) && !positions.has(srcId)) {
      if (!sourceToConnected.has(srcId))
        sourceToConnected.set(srcId, []);
      sourceToConnected.get(srcId)!.push(tgtId);
    }
    if (positions.has(srcId) && !positions.has(tgtId)) {
      if (!sourceToConnected.has(tgtId))
        sourceToConnected.set(tgtId, []);
      sourceToConnected.get(tgtId)!.push(srcId);
    }
  }

  // Position sources at centroid of connected claims
  for (const n of nodes) {
    if (n.type !== "source") continue;
    const connected = sourceToConnected.get(n.id);
    if (connected && connected.length > 0) {
      let sumX = 0;
      let sumY = 0;
      let count = 0;
      for (const cid of connected) {
        const pos = positions.get(cid);
        if (pos) {
          sumX += pos.targetX;
          sumY += pos.targetY;
          count++;
        }
      }
      if (count > 0) {
        positions.set(n.id, {
          targetX: sumX / count,
          targetY: sumY / count,
        });
      } else {
        positions.set(n.id, { targetX: width / 2, targetY: height / 2 });
      }
    } else {
      positions.set(n.id, { targetX: width / 2, targetY: height / 2 });
    }
  }

  return positions;
}
