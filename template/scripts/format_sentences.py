#!/usr/bin/env python3
"""Format and lint LaTeX source files.

Two passes:
1. Sentence splitting — one sentence per line (semantic linebreaks)
2. Linting — non-breaking spaces, smart quotes, ellipsis, en-dashes, etc.

LaTeX treats single newlines as spaces, so compiled output is identical.

Usage:
    python scripts/format_sentences.py              # formats main.tex in-place
    python scripts/format_sentences.py paper.tex    # formats specified file
    python scripts/format_sentences.py --check      # dry run, exit 1 if changes needed
"""

import re
import sys

# Environments where sentence splitting is disabled
PROTECTED_ENVS = {
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "flalign", "flalign*", "eqnarray", "eqnarray*",
    "verbatim", "lstlisting", "minted", "alltt",
    "tikzpicture", "pgfpicture",
    "tabular", "tabular*", "tabularx", "longtable", "array",
    "algorithmic", "algorithm", "algorithm2e",
    "filecontents", "filecontents*",
}

# Environments where linting is also disabled (literal text)
LITERAL_ENVS = {"verbatim", "lstlisting", "minted", "alltt"}

# Abbreviations that don't end sentences
ABBREVIATIONS = {
    "e.g.", "i.e.", "cf.", "vs.", "etc.", "al.", "Fig.", "fig.",
    "Eq.", "eq.", "Ref.", "ref.", "Sec.", "sec.", "Ch.", "ch.",
    "Dr.", "Prof.", "Mr.", "Mrs.", "Ms.", "Jr.", "Sr.", "St.",
    "Vol.", "vol.", "No.", "no.", "pp.", "Ed.", "ed.", "Rev.",
    "Dept.", "dept.", "Univ.", "univ.", "Corp.", "Inc.", "Ltd.",
    "approx.", "est.", "resp.", "Figs.", "figs.", "Eqs.", "eqs.",
    "Refs.", "refs.", "Secs.", "secs.", "Chs.", "chs.",
}

# Label words that need non-breaking space before \ref/\eqref
_LABEL_WORDS = (
    r"Figure|Table|Section|Theorem|Lemma|Definition|Corollary|"
    r"Proposition|Chapter|Appendix|Algorithm|Listing|Equation|"
    r"Fig\.|Eq\.|Sec\.|Ch\.|Tab\."
)


# ---------------------------------------------------------------------------
# Pass 1: Sentence splitting
# ---------------------------------------------------------------------------

def is_structural(line: str) -> bool:
    """True if line is a LaTeX structural command, not prose."""
    s = line.strip()
    if not s or s.startswith("%"):
        return True
    if re.match(r"^\\(begin|end)\{", s):
        return True
    if re.match(
        r"^\\(section|subsection|subsubsection|paragraph|subparagraph|chapter|part"
        r"|label|caption|includegraphics|bibliographystyle|bibliography"
        r"|title|author|date|maketitle|tableofcontents|listoffigures"
        r"|listoftables|appendix|newpage|clearpage|pagebreak"
        r"|vspace|hspace|bigskip|medskip|smallskip|centering"
        r"|raggedright|raggedleft|mbox)\b",
        s,
    ):
        return True
    if re.match(r"^[}\]]+\s*(%.*)?$", s):
        return True
    return False


def find_sentence_breaks(text: str) -> list[int]:
    """Return indices where a new sentence begins (split points)."""
    breaks = []
    i = 0
    in_math = False

    while i < len(text):
        ch = text[i]

        if ch == "$" and (i == 0 or text[i - 1] != "\\"):
            in_math = not in_math
            i += 1
            continue

        if in_math:
            i += 1
            continue

        # Recognize \ldots as a potential sentence boundary
        if text[i : i + 6] == "\\ldots":
            rest = text[i + 6 :]
            m = re.match(r"([}\)\]]*)\s+", rest)
            if m:
                next_pos = i + 6 + m.end()
                if next_pos < len(text) and (
                    text[next_pos].isupper() or text[next_pos] == "\\"
                ):
                    split_at = i + 6 + len(m.group(1))
                    breaks.append(split_at)
            i += 6
            continue

        if ch in ".?!":
            before = text[max(0, i - 11) : i + 1]
            is_abbrev = False
            for a in ABBREVIATIONS:
                if before.endswith(a):
                    start = len(before) - len(a)
                    if start == 0 or not before[start - 1].isalpha():
                        is_abbrev = True
                        break
            if is_abbrev:
                i += 1
                continue

            rest = text[i + 1 :]
            m = re.match(r"([}\)\]]*)\s+", rest)
            if m:
                next_pos = i + 1 + m.end()
                if next_pos < len(text) and (
                    text[next_pos].isupper() or text[next_pos] == "\\"
                ):
                    split_at = i + 1 + len(m.group(1))
                    breaks.append(split_at)

        i += 1

    return breaks


def _sentence_split_pass(content: str) -> str:
    """Reformat paragraphs to one sentence per line."""
    lines = content.split("\n")
    result: list[str] = []
    in_preamble = True
    protect_depth = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        if in_preamble:
            result.append(line)
            if "\\begin{document}" in line:
                in_preamble = False
            i += 1
            continue

        for env in PROTECTED_ENVS:
            if f"\\begin{{{env}}}" in line:
                protect_depth += 1
            if f"\\end{{{env}}}" in line:
                protect_depth = max(0, protect_depth - 1)

        if protect_depth > 0:
            result.append(line)
            i += 1
            continue

        if not line.strip() or line.strip().startswith("%") or is_structural(line):
            result.append(line)
            i += 1
            continue

        para_lines: list[str] = []
        indent = re.match(r"^(\s*)", line).group(1)  # type: ignore[union-attr]

        while i < len(lines):
            ln = lines[i]
            if not ln.strip():
                break
            if ln.strip().startswith("%"):
                break
            if is_structural(ln):
                break
            if any(f"\\begin{{{e}}}" in ln for e in PROTECTED_ENVS):
                break
            para_lines.append(ln.strip())
            i += 1

        if not para_lines:
            result.append(line)
            i += 1
            continue

        paragraph = " ".join(para_lines)
        paragraph = re.sub(r"  +", " ", paragraph)

        breaks = find_sentence_breaks(paragraph)
        if not breaks:
            result.append(indent + paragraph)
            continue

        sentences: list[str] = []
        prev = 0
        for bp in breaks:
            seg = paragraph[prev:bp].strip()
            if seg:
                sentences.append(seg)
            prev = bp
        tail = paragraph[prev:].strip()
        if tail:
            sentences.append(tail)

        for s in sentences:
            result.append(indent + s)

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Pass 2: Linting
# ---------------------------------------------------------------------------

def lint_line(line: str) -> str:
    """Apply formatting fixes to a single content line."""

    # --- Non-breaking spaces before \ref, \eqref after label words ---
    line = re.sub(
        rf"((?:{_LABEL_WORDS})) +(\\(?:ref|eqref)\b)",
        r"\1~\2",
        line,
    )

    # --- Smart quotes: "text" → ``text'' ---
    # Skip lines that already use `` or '' (already converted)
    if "``" not in line and "''" not in line:
        line = re.sub(r'(?<!\\)"([^"]*)"', r"``\1''", line)

    # --- Ellipsis: ... → \ldots ---
    line = re.sub(r"(?<!\.)\.\.\.(?!\.)", r"\\ldots", line)

    # --- En-dash for number ranges: 1-10 → 1--10 ---
    line = re.sub(r"(\d)\s*-(?!-)\s*(\d)", r"\1--\2", line)

    # --- Normalize \(...\) → $...$ (only if no $ on line to avoid nesting) ---
    if "$" not in line:
        line = re.sub(r"\\\((.+?)\\\)", r"$\1$", line)

    # --- Collapse multiple spaces (preserve leading indent) ---
    line = re.sub(r"(?<=\S)  +", " ", line)

    return line


def _lint_pass(content: str) -> str:
    """Apply linting fixes. Skips preamble, literal environments, and comments."""
    lines = content.split("\n")
    result: list[str] = []
    in_preamble = True
    literal_depth = 0

    for line in lines:
        # Always strip trailing whitespace
        line = line.rstrip()

        if in_preamble:
            result.append(line)
            if "\\begin{document}" in line:
                in_preamble = False
            continue

        # Track literal environments (verbatim, lstlisting, etc.)
        for env in LITERAL_ENVS:
            if f"\\begin{{{env}}}" in line:
                literal_depth += 1
            if f"\\end{{{env}}}" in line:
                literal_depth = max(0, literal_depth - 1)

        if literal_depth > 0:
            result.append(line)
            continue

        # Skip comment-only lines (trailing whitespace already stripped)
        if line.strip().startswith("%"):
            result.append(line)
            continue

        result.append(lint_line(line))

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

def format_latex(content: str) -> str:
    """Run both passes: sentence splitting then linting."""
    content = _sentence_split_pass(content)
    content = _lint_pass(content)
    return content


def main() -> None:
    check_mode = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--check"]
    path = args[0] if args else "main.tex"

    with open(path, encoding="utf-8") as f:
        original = f.read()

    formatted = format_latex(original)

    if check_mode:
        if formatted != original:
            print(f"{path}: would reformat")
            sys.exit(1)
        else:
            print(f"{path}: already formatted")
            sys.exit(0)

    if formatted != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"Formatted {path}")
    else:
        print(f"{path}: no changes needed")


if __name__ == "__main__":
    main()
