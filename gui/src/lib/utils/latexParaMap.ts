/** Mapping from a provenance-style target ("introduction/p1") to editor line range */
export interface ParagraphRange {
  startLine: number;
  endLine: number;
}

/** Canonical section name mapping for common LaTeX section titles */
const SECTION_ALIASES: Record<string, string> = {
  "introduction": "introduction",
  "intro": "introduction",
  "related work": "related_work",
  "related works": "related_work",
  "background": "related_work",
  "literature review": "related_work",
  "methods": "methods",
  "methodology": "methods",
  "method": "methods",
  "materials and methods": "methods",
  "approach": "methods",
  "results": "results",
  "findings": "results",
  "experiments": "results",
  "experimental results": "results",
  "discussion": "discussion",
  "analysis": "discussion",
  "conclusion": "conclusion",
  "conclusions": "conclusion",
  "summary": "conclusion",
  "abstract": "abstract",
};

function canonicalSection(title: string): string {
  const lower = title.toLowerCase().trim();
  return SECTION_ALIASES[lower] ?? lower.replace(/\s+/g, "_");
}

const SECTION_RE = /^\\(section|subsection|subsubsection)\*?\{(.+?)\}/;
const COMMENT_RE = /^\s*%/;

/**
 * Parse LaTeX content into a map of "section/pN" -> line range.
 * Paragraphs are separated by blank lines within each top-level section.
 * Only counts \section{} boundaries (not subsections) for provenance target mapping.
 */
export function parseLatexParagraphs(content: string): Map<string, ParagraphRange> {
  const lines = content.split("\n");
  const result = new Map<string, ParagraphRange>();

  let currentSection = "";
  let paraIndex = 0;
  let paraStart = -1;
  let inContent = false; // true after \begin{document}
  let inEnvironment = 0; // depth of non-document environments

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Track document boundaries
    if (/\\begin\{document\}/.test(line)) {
      inContent = true;
      continue;
    }
    if (/\\end\{document\}/.test(line)) {
      // Flush last paragraph
      if (paraStart >= 0 && currentSection) {
        result.set(`${currentSection}/p${paraIndex}`, {
          startLine: paraStart + 1,
          endLine: i,
        });
      }
      break;
    }

    if (!inContent) continue;

    // Track environments (skip content inside figures, tables, etc.)
    if (/\\begin\{(?!document)/.test(line)) {
      // Flush paragraph before environment
      if (inEnvironment === 0 && paraStart >= 0 && currentSection) {
        result.set(`${currentSection}/p${paraIndex}`, {
          startLine: paraStart + 1,
          endLine: i,
        });
        paraIndex++;
        paraStart = -1;
      }
      inEnvironment++;
      continue;
    }
    if (/\\end\{(?!document)/.test(line)) {
      inEnvironment = Math.max(0, inEnvironment - 1);
      continue;
    }
    if (inEnvironment > 0) continue;

    // Detect section boundaries
    const sectionMatch = line.match(SECTION_RE);
    if (sectionMatch) {
      // Flush previous paragraph
      if (paraStart >= 0 && currentSection) {
        result.set(`${currentSection}/p${paraIndex}`, {
          startLine: paraStart + 1,
          endLine: i,
        });
      }

      const level = sectionMatch[1];
      const title = sectionMatch[2].replace(/\\[a-zA-Z]+\{([^}]*)\}/g, "$1");

      // Only top-level \section resets the section context
      if (level === "section") {
        currentSection = canonicalSection(title);
        paraIndex = 0;
      }
      // Subsections start a new paragraph within the current section
      else if (currentSection) {
        paraIndex++;
      }

      paraStart = -1;
      continue;
    }

    // Skip comments and commands-only lines
    if (COMMENT_RE.test(line)) continue;

    // Blank line = paragraph break
    if (trimmed === "") {
      if (paraStart >= 0 && currentSection) {
        result.set(`${currentSection}/p${paraIndex}`, {
          startLine: paraStart + 1,
          endLine: i,
        });
        paraIndex++;
        paraStart = -1;
      }
      continue;
    }

    // Content line — start a new paragraph if we don't have one
    if (paraStart < 0 && currentSection) {
      paraStart = i;
    }
  }

  // Flush any remaining paragraph
  if (paraStart >= 0 && currentSection) {
    result.set(`${currentSection}/p${paraIndex}`, {
      startLine: paraStart + 1,
      endLine: lines.length,
    });
  }

  return result;
}

/**
 * Given a 1-based editor line number, find which provenance target it maps to.
 * Returns null if the line isn't within any mapped paragraph.
 */
export function lineToTarget(
  paraMap: Map<string, ParagraphRange>,
  line: number
): string | null {
  for (const [target, range] of paraMap) {
    if (line >= range.startLine && line <= range.endLine) {
      return target;
    }
  }
  return null;
}
