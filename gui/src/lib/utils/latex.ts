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
