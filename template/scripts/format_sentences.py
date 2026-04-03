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

# Environments that use display math (tracked separately for sentence splitting)
DISPLAY_MATH_ENVS = {
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "flalign", "flalign*", "eqnarray", "eqnarray*",
}

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

_MAX_ABBREV_LEN = max(len(a) for a in ABBREVIATIONS)

# Label words that need non-breaking space before \ref/\eqref
_LABEL_WORDS = (
    r"Figure|Table|Section|Theorem|Lemma|Definition|Corollary|"
    r"Proposition|Chapter|Appendix|Algorithm|Listing|Equation|"
    r"Fig\.|Eq\.|Sec\.|Ch\.|Tab\."
)

# Reference commands that should have a non-breaking space before them
_REF_COMMANDS = r"\\(?:ref|eqref|pageref|autoref|cref|Cref)\b"

# Citation commands that should have a non-breaking space before them
_CITE_COMMANDS = r"\\(?:cite|citep|citet|citealt|citealp|citeauthor|citeyear|citenum)\b"


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
    in_display_math = False

    while i < len(text):
        ch = text[i]

        # --- Display math: $$ ... $$ ---
        if (
            ch == "$"
            and i + 1 < len(text)
            and text[i + 1] == "$"
            and (i == 0 or text[i - 1] != "\\")
        ):
            in_display_math = not in_display_math
            i += 2
            continue

        # --- Display math: \[ ... \] ---
        if ch == "\\" and i + 1 < len(text) and text[i + 1] == "[" and not in_math:
            in_display_math = True
            i += 2
            continue
        if ch == "\\" and i + 1 < len(text) and text[i + 1] == "]" and in_display_math:
            in_display_math = False
            i += 2
            continue

        if in_display_math:
            i += 1
            continue

        # --- Inline math: $ ... $ ---
        if ch == "$" and (i == 0 or text[i - 1] != "\\"):
            in_math = not in_math
            i += 1
            continue

        if in_math:
            i += 1
            continue

        # --- Skip LaTeX commands that contain dots (e.g. \ldots, \cdots, \dots) ---
        if text[i : i + 6] == "\\ldots" or text[i : i + 5] == "\\dots" or text[i : i + 6] == "\\cdots":
            cmd_len = 6 if text[i : i + 6] in ("\\ldots", "\\cdots") else 5
            rest = text[i + cmd_len :]
            m = re.match(r"([}\)\]]*)\s+", rest)
            if m:
                next_pos = i + cmd_len + m.end()
                if next_pos < len(text) and (
                    text[next_pos].isupper() or text[next_pos] == "\\"
                ):
                    split_at = i + cmd_len + len(m.group(1))
                    breaks.append(split_at)
            i += cmd_len
            continue

        if ch in ".?!":
            before = text[max(0, i - _MAX_ABBREV_LEN) : i + 1]
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

            # --- Skip decimal numbers: "3.14", "0.5" ---
            if ch == "." and i > 0 and text[i - 1].isdigit():
                if i + 1 < len(text) and text[i + 1].isdigit():
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

        # --- Colon followed by a capital letter can start a new "sentence" ---
        if ch == ":":
            rest = text[i + 1 :]
            m = re.match(r"\s+", rest)
            if m:
                next_pos = i + 1 + m.end()
                if next_pos < len(text) and text[next_pos].isupper():
                    # Only split if the text after looks like a full sentence
                    # (at least ~20 chars or another sentence-ending punctuation)
                    remaining = text[next_pos:]
                    if len(remaining) > 30 or re.search(r"[.?!]", remaining):
                        breaks.append(i + 1)

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

    # --- Fix bare [h] and [H] float specifiers → [htbp] ---
    line = re.sub(
        r"(\\begin\{(?:figure|table)\*?\})\[[hH]\]",
        r"\1[htbp]",
        line,
    )

    # --- Fix obsolete {\bf text} → \textbf{text} ---
    line = re.sub(r"\{\\bf\s+([^}]*)\}", r"\\textbf{\1}", line)

    # --- Fix obsolete {\it text} → \emph{text} ---
    line = re.sub(r"\{\\it\s+([^}]*)\}", r"\\emph{\1}", line)

    # --- Non-breaking spaces before \ref, \eqref, \autoref, etc. after label words ---
    line = re.sub(
        rf"((?:{_LABEL_WORDS})) +({_REF_COMMANDS})",
        r"\1~\2",
        line,
    )

    # --- Non-breaking space before \ref, \cref, \eqref after any word character ---
    line = re.sub(
        rf"(\w) +({_REF_COMMANDS})",
        r"\1~\2",
        line,
    )

    # --- Non-breaking space before \cite, \citep, \citet, etc. ---
    # Matches a regular space before a citation command and replaces with ~
    line = re.sub(
        rf"(\S) +({_CITE_COMMANDS})",
        r"\1~\2",
        line,
    )

    # --- Non-breaking space between number and unit commands ---
    # e.g., "5 \%" → "5~\%", "100 \si{...}" → "100~\si{...}"
    line = re.sub(
        r"(\d) +(\\(?:si|SI|%|percent)\b)",
        r"\1~\2",
        line,
    )

    # --- Smart quotes: "text" → ``text'' ---
    # Skip lines that already use `` or '' (already converted)
    if "``" not in line and "''" not in line:
        line = re.sub(r'(?<!\\)"([^"]*)"', r"``\1''", line)

    # --- Single smart quotes: 'text' → `text' ---
    # Only when surrounded by spaces/start-of-line (avoid contractions like don't)
    if "`" not in line:
        line = re.sub(r"(?<=\s)'([^']+)'(?=[\s,.\);:!?])", r"`\1'", line)

    # --- Ellipsis: ... → \ldots ---
    line = re.sub(r"(?<!\.)\.\.\.(?!\.)", r"\\ldots", line)

    # --- En-dash for number ranges: 1-10 → 1--10 ---
    line = re.sub(r"(\d)\s*-(?!-)\s*(\d)", r"\1--\2", line)

    # --- En-dash for page ranges after pp.: pp. 10-20 → pp. 10--20 ---
    line = re.sub(r"(pp\.\s*\d+)\s*-(?!-)\s*(\d)", r"\1--\2", line)

    # --- Normalize display math: $$...$$ → \[...\] ---
    line = re.sub(r"\$\$(.+?)\$\$", r"\\[\1\\]", line)

    # --- Normalize \(...\) → $...$ (only if no $ on line to avoid nesting) ---
    if "$" not in line:
        line = re.sub(r"\\\((.+?)\\\)", r"$\1$", line)

    # --- Prefer \emph over \textit for semantic emphasis ---
    line = re.sub(r"\\textit\{([^}]*)\}", r"\\emph{\1}", line)

    # --- Fix common ligature-breaking: fi, fl in copy-pasted text ---
    line = line.replace("ﬁ", "fi").replace("ﬂ", "fl")

    # --- Remove double periods (common typo, but skip \ldots and ...) ---
    line = re.sub(r"(?<!\\)(?<!\.)\.\.(?!\.)", ".", line)

    # --- Collapse multiple spaces (preserve leading indent) ---
    line = re.sub(r"(?<=\S)  +", " ", line)

    return line

def _lint_pass(content: str) -> str:
    """Apply linting fixes. Skips preamble, literal environments, and comments."""
    lines = content.split("\n")
    result: list[str] = []
    in_preamble = True
    literal_depth = 0
    display_math_depth = 0

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

        # Track display math environments (don't lint math content)
        for env in DISPLAY_MATH_ENVS:
            if f"\\begin{{{env}}}" in line:
                display_math_depth += 1
            if f"\\end{{{env}}}" in line:
                display_math_depth = max(0, display_math_depth - 1)

        if display_math_depth > 0:
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
    paths = args if args else ["main.tex"]

    any_changed = False
    for path in paths:
        with open(path, encoding="utf-8") as f:
            original = f.read()

        formatted = format_latex(original)

        if check_mode:
            if formatted != original:
                print(f"{path}: would reformat")
                any_changed = True
            else:
                print(f"{path}: already formatted")
        else:
            if formatted != original:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(formatted)
                print(f"Formatted {path}")
                any_changed = True
            else:
                print(f"{path}: no changes needed")

    if check_mode and any_changed:
        sys.exit(1)


if __name__ == "__main__":
    main()