export interface TexSection {
  level: number;
  title: string;
  line: number;
  label?: string;
}

const SECTION_PATTERN =
  /^\\(section|subsection|subsubsection|paragraph)\*?\{(.+?)\}/;

const LEVEL_MAP: Record<string, number> = {
  section: 1,
  subsection: 2,
  subsubsection: 3,
  paragraph: 4,
};

export function parseTexSections(content: string): TexSection[] {
  const sections: TexSection[] = [];
  const lines = content.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(SECTION_PATTERN);
    if (match) {
      const command = match[1];
      const title = match[2].replace(/\\[a-zA-Z]+\{([^}]*)\}/g, "$1");
      sections.push({
        level: LEVEL_MAP[command] || 1,
        title,
        line: i + 1,
      });

      // Check for \label on next line
      if (i + 1 < lines.length) {
        const labelMatch = lines[i + 1].match(/\\label\{(.+?)\}/);
        if (labelMatch) {
          sections[sections.length - 1].label = labelMatch[1];
        }
      }
    }
  }

  return sections;
}

export function parseCiteKeys(content: string): string[] {
  const keys: string[] = [];
  const pattern = /\\cite[tp]?\*?\{([^}]+)\}/g;
  let match;
  while ((match = pattern.exec(content)) !== null) {
    const keyStr = match[1];
    for (const key of keyStr.split(",")) {
      const trimmed = key.trim();
      if (trimmed && !keys.includes(trimmed)) {
        keys.push(trimmed);
      }
    }
  }
  return keys;
}

export function countWords(texContent: string): number {
  // Strip LaTeX commands and environments
  const stripped = texContent
    .replace(/%.*/g, "") // comments
    .replace(/\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}/g, " ") // environments
    .replace(/\\[a-zA-Z]+\*?\{[^}]*\}/g, " ") // commands with args
    .replace(/\\[a-zA-Z]+\*?/g, " ") // standalone commands
    .replace(/[{}[\]$&~^_#]/g, " ") // special chars
    .replace(/\s+/g, " ")
    .trim();

  if (!stripped) return 0;
  return stripped.split(/\s+/).length;
}

export interface FigureEnv {
  /** \includegraphics filename (no extension, no path prefix) */
  stem: string;
  /** Raw \caption{...} text, LaTeX stripped */
  caption: string;
  /** \label{fig:...} value, or null */
  label: string | null;
  /** Line number of \begin{figure} */
  line: number;
}

export function parseFigureEnvironments(content: string): FigureEnv[] {
  const figures: FigureEnv[] = [];
  const lines = content.split("\n");
  let inFigure = false;
  let current: Partial<FigureEnv> = {};
  let startLine = 0;
  let captionBuf: string[] | null = null;
  let captionDepth = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (/\\begin\{figure\*?\}/.test(line)) {
      inFigure = true;
      startLine = i + 1;
      current = {};
      captionBuf = null;
      captionDepth = 0;
      continue;
    }
    if (/\\end\{figure\*?\}/.test(line)) {
      if (inFigure && current.stem) {
        figures.push({
          stem: current.stem!,
          caption: current.caption ?? "",
          label: current.label ?? null,
          line: startLine,
        });
      }
      inFigure = false;
      continue;
    }
    if (!inFigure) continue;

    // Accumulate multiline \caption{...} with brace balancing
    if (captionBuf !== null) {
      captionBuf.push(line);
      for (const ch of line) {
        if (ch === "{") captionDepth++;
        else if (ch === "}") captionDepth--;
      }
      if (captionDepth <= 0) {
        const raw = captionBuf.join(" ");
        // Extract content between first { and last }
        const open = raw.indexOf("{");
        const close = raw.lastIndexOf("}");
        if (open !== -1 && close > open) {
          current.caption = raw
            .slice(open + 1, close)
            .replace(/\\[a-zA-Z]+\{([^}]*)\}/g, "$1")
            .replace(/[{}]/g, "")
            .replace(/\s+/g, " ")
            .trim();
        }
        captionBuf = null;
      }
      continue;
    }

    // \includegraphics[...]{path/file.ext} or \includegraphics{path/file}
    const igMatch = line.match(/\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}/);
    if (igMatch) {
      const raw = igMatch[1];
      // Strip path prefix and extension
      const basename = raw.split("/").pop() ?? raw;
      current.stem = basename.replace(/\.\w+$/, "");
    }

    // \caption — start accumulating (handles single-line and multiline)
    if (/\\caption\s*\{/.test(line)) {
      captionBuf = [line];
      captionDepth = 0;
      for (const ch of line) {
        if (ch === "{") captionDepth++;
        else if (ch === "}") captionDepth--;
      }
      // Single-line caption: braces balanced on same line
      if (captionDepth <= 0) {
        const raw = line;
        const open = raw.indexOf("\\caption");
        const braceStart = raw.indexOf("{", open);
        const braceEnd = raw.lastIndexOf("}");
        if (braceStart !== -1 && braceEnd > braceStart) {
          current.caption = raw
            .slice(braceStart + 1, braceEnd)
            .replace(/\\[a-zA-Z]+\{([^}]*)\}/g, "$1")
            .replace(/[{}]/g, "")
            .trim();
        }
        captionBuf = null;
      }
      continue;
    }

    // \label{fig:...}
    const labelMatch = line.match(/\\label\{(fig:[^}]+)\}/);
    if (labelMatch) {
      current.label = labelMatch[1];
    }
  }

  return figures;
}

export interface FigureRef {
  /** The label referenced, e.g. "fig:overview" */
  label: string;
  /** Line number where the reference appears */
  line: number;
}

export function parseFigureRefs(content: string): FigureRef[] {
  const refs: FigureRef[] = [];
  const lines = content.split("\n");
  // Match \ref{fig:...}, \autoref{fig:...}, \cref{fig:...}, \Cref{fig:...}
  const pattern = /\\(?:auto|c|C)?ref\{(fig:[^}]+)\}/g;

  for (let i = 0; i < lines.length; i++) {
    let match;
    pattern.lastIndex = 0;
    while ((match = pattern.exec(lines[i])) !== null) {
      refs.push({ label: match[1], line: i + 1 });
    }
  }

  return refs;
}
