import { parse as parseYaml } from "yaml";

export interface ParsedDocument {
  frontmatter: Record<string, unknown>;
  content: string;
}

export function parseFrontmatter(raw: string): ParsedDocument {
  const trimmed = raw.trimStart();
  if (!trimmed.startsWith("---")) {
    return { frontmatter: {}, content: raw };
  }

  const afterFirst = trimmed.slice(3);
  const endIdx = afterFirst.indexOf("\n---");
  if (endIdx === -1) {
    return { frontmatter: {}, content: raw };
  }

  const yamlStr = afterFirst.slice(0, endIdx).trim();
  const content = afterFirst.slice(endIdx + 4).trim();

  try {
    const frontmatter = parseYaml(yamlStr) || {};
    return { frontmatter, content };
  } catch {
    return { frontmatter: {}, content: raw };
  }
}

export function serializeFrontmatter(
  frontmatter: Record<string, unknown>,
  content: string
): string {
  const lines: string[] = ["---"];
  for (const [key, value] of Object.entries(frontmatter)) {
    if (Array.isArray(value)) {
      lines.push(`${key}: [${value.map((v) => JSON.stringify(v)).join(", ")}]`);
    } else if (typeof value === "string") {
      lines.push(`${key}: "${value}"`);
    } else {
      lines.push(`${key}: ${value}`);
    }
  }
  lines.push("---");
  lines.push("");
  lines.push(content);
  return lines.join("\n");
}
