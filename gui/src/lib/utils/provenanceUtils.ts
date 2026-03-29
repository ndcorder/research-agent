import type { ProvenanceEntry } from "$lib/types";

/** A group of provenance events sharing the same target (e.g. "methods/p2") */
export interface TargetGroup {
  target: string;
  section: string;
  events: ProvenanceEntry[];
  firstTimestamp: number;
}

/** Extract the section prefix from a provenance target string */
export function sectionFromTarget(target: string): string {
  // Targets look like "introduction/p1", "methods/p2", "results/p3", etc.
  // Also handle bare section names and slash-less targets
  const slash = target.indexOf("/");
  if (slash === -1) return target.toLowerCase();
  return target.slice(0, slash).toLowerCase();
}

/** Group flat provenance entries by target, sorted by first-event timestamp */
export function groupByTarget(entries: ProvenanceEntry[]): TargetGroup[] {
  const map = new Map<string, ProvenanceEntry[]>();

  for (const entry of entries) {
    const target = entry.target || "unknown";
    let group = map.get(target);
    if (!group) {
      group = [];
      map.set(target, group);
    }
    group.push(entry);
  }

  const groups: TargetGroup[] = [];
  for (const [target, events] of map) {
    // Sort events within group by timestamp
    events.sort((a, b) => {
      const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return ta - tb;
    });

    const firstTimestamp = events[0]?.timestamp
      ? new Date(events[0].timestamp).getTime()
      : 0;

    groups.push({
      target,
      section: sectionFromTarget(target),
      events,
      firstTimestamp,
    });
  }

  // Sort groups by first event timestamp
  groups.sort((a, b) => a.firstTimestamp - b.firstTimestamp);

  return groups;
}

/** Derive the union of all stage column identifiers from entries, split into pipeline stages and /auto iterations */
export function stageColumns(entries: ProvenanceEntry[]): {
  pipeline: string[];
  auto: string[];
} {
  const pipelineSet = new Set<string>();
  const autoSet = new Set<string>();

  for (const entry of entries) {
    const stage = entry.stage;
    if (!stage) continue;

    // /auto iterations have stage like "auto-1", "auto-2", etc.
    if (stage.startsWith("auto")) {
      autoSet.add(stage);
    } else {
      pipelineSet.add(stage);
    }
  }

  // Sort pipeline stages numerically (e.g. "1", "2", "3", "3b", "5", "6")
  const pipeline = [...pipelineSet].sort((a, b) => {
    const na = parseInt(a) || 0;
    const nb = parseInt(b) || 0;
    if (na !== nb) return na - nb;
    return a.localeCompare(b);
  });

  // Sort auto iterations numerically
  const auto = [...autoSet].sort((a, b) => {
    const na = parseInt(a.replace(/\D/g, "")) || 0;
    const nb = parseInt(b.replace(/\D/g, "")) || 0;
    return na - nb;
  });

  return { pipeline, auto };
}

/** Get unique section names from grouped provenance data */
export function availableSections(groups: TargetGroup[]): string[] {
  const sections = new Set<string>();
  for (const g of groups) {
    sections.add(g.section);
  }
  return [...sections].sort();
}

/** Color class for a provenance action */
export function actionDotColor(action: string): string {
  const a = action.toLowerCase();
  if (a === "write" || a === "add") return "#22c55e"; // green
  if (a === "revise") return "#3b82f6"; // blue
  if (a === "expand" || a === "reorder") return "#f59e0b"; // amber
  if (a === "cut" || a === "remove") return "#ef4444"; // red
  return "#6b7280"; // gray
}
