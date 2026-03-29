import { get } from "svelte/store";
import {
  sources,
  claims,
  wordCount,
  texContent,
  paperConfig,
} from "$lib/stores/project";
import { writeFile } from "$lib/utils/ipc";
import { parseCiteKeys } from "$lib/utils/latex";
import { toasts } from "$lib/stores/toast";
import type { SourceMeta, ClaimMeta } from "$lib/types";

function escMd(s: string): string {
  return s.replace(/\|/g, "\\|");
}

function formatDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function buildSourceTable(
  items: SourceMeta[],
  variant: "verified" | "flagged" | "needs-replacement"
): string {
  if (items.length === 0) return "_None_\n";

  if (variant === "verified") {
    const rows = items.map((s) => {
      const key = escMd(s.key);
      const title = escMd(s.title ?? "Untitled");
      const authors = escMd((s.authors ?? []).join(", ") || "Unknown");
      const year = s.year ?? "N/A";
      const evidence = escMd((s.evidence_for ?? []).join(", ") || "-");
      return `| ${key} | ${title} | ${authors} | ${year} | ${evidence} |`;
    });
    return [
      "| Key | Title | Authors | Year | Evidence For |",
      "|-|-|-|-|-|",
      ...rows,
      "",
    ].join("\n");
  }

  if (variant === "flagged") {
    const rows = items.map((s) => {
      const key = escMd(s.key);
      const title = escMd(s.title ?? "Untitled");
      const status = escMd(s.status ?? "flagged");
      const tags = escMd((s.tags ?? []).join(", ") || "-");
      return `| ${key} | ${title} | ${status} | ${tags} |`;
    });
    return [
      "| Key | Title | Status | Notes |",
      "|-|-|-|-|",
      ...rows,
      "",
    ].join("\n");
  }

  // needs-replacement
  const rows = items.map((s) => {
    const key = escMd(s.key);
    const title = escMd(s.title ?? "Untitled");
    const status = escMd(s.status ?? "needs-replacement");
    const tags = escMd((s.tags ?? []).join(", ") || "-");
    return `| ${key} | ${title} | ${status} | ${tags} |`;
  });
  return [
    "| Key | Title | Status | Notes |",
    "|-|-|-|-|",
    ...rows,
    "",
  ].join("\n");
}

function buildClaimsTable(items: ClaimMeta[]): string {
  if (items.length === 0) return "_No claims recorded_\n";

  const rows = items.map((c, i) => {
    const num = i + 1;
    const statement = escMd(c.statement);
    const confidence = escMd(c.confidence);
    const density = c.evidence_density;
    const section = escMd(c.section);
    return `| ${num} | ${statement} | ${confidence} | ${density} | ${section} |`;
  });

  return [
    "| # | Statement | Confidence | Evidence | Section |",
    "|-|-|-|-|-|",
    ...rows,
    "",
  ].join("\n");
}

function buildEvidenceCoverage(items: ClaimMeta[]): string {
  const strong = items.filter((c) => c.evidence_density >= 3);
  const weak = items.filter((c) => c.evidence_density < 2);

  const lines: string[] = [];

  lines.push("Claims with strong evidence (>=3 sources):");
  if (strong.length === 0) {
    lines.push("- _None_");
  } else {
    for (const c of strong) {
      lines.push(`- ${c.statement} (${c.evidence_density} sources)`);
    }
  }

  lines.push("");
  lines.push("Claims needing more evidence (<2 sources):");
  if (weak.length === 0) {
    lines.push("- _None_");
  } else {
    for (const c of weak) {
      lines.push(`- ${c.statement} (${c.evidence_density} sources)`);
    }
  }

  lines.push("");
  return lines.join("\n");
}

export async function exportResearchSummary(
  projectDir: string
): Promise<string> {
  try {
    const config = get(paperConfig);
    const srcList = get(sources);
    const claimList = get(claims);
    const wc = get(wordCount);
    const tex = get(texContent);

    const topic = config?.topic ?? "Untitled";
    const venue = config?.venue ?? "Unknown";
    const depth = config?.depth ?? "standard";

    const citeKeys = parseCiteKeys(tex);

    const verified = srcList.filter((s) => s.status === "verified");
    const flagged = srcList.filter((s) => s.status === "flagged");
    const needsReplacement = srcList.filter(
      (s) => s.status === "needs-replacement"
    );

    const md = [
      `# Research Summary: ${topic}`,
      "",
      `**Venue**: ${venue} | **Depth**: ${depth}`,
      `**Generated**: ${formatDate()}`,
      "",
      "## Statistics",
      `- **Word count**: ${wc}`,
      `- **Sources**: ${srcList.length} (${verified.length} verified, ${flagged.length} flagged)`,
      `- **Claims**: ${claimList.length}`,
      `- **Citations**: ${citeKeys.length}`,
      "",
      "## Sources",
      "",
      `### Verified (${verified.length})`,
      buildSourceTable(verified, "verified"),
      `### Flagged (${flagged.length})`,
      buildSourceTable(flagged, "flagged"),
      `### Needs Replacement (${needsReplacement.length})`,
      buildSourceTable(needsReplacement, "needs-replacement"),
      "## Claims",
      "",
      buildClaimsTable(claimList),
      "## Evidence Coverage",
      "",
      buildEvidenceCoverage(claimList),
      "## Citation Keys",
      `All citation keys used in the paper:`,
      citeKeys.map((k) => `\`${k}\``).join(", ") || "_None_",
      "",
    ].join("\n");

    const filePath = `${projectDir}/research/SUMMARY.md`;
    await writeFile(filePath, md);

    toasts.success("Research summary exported");
    return filePath;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    toasts.error(`Export failed: ${msg}`);
    throw err;
  }
}
