# Respond to Reviewers — Point-by-Point Peer Review Response with Tracked Changes

Generate a structured response document addressing every reviewer comment, with corresponding tracked changes in the manuscript.

## Instructions

The user either pastes reviewer comments directly or points to a file in `attachments/reviews/`.

### Phase 1: Parse and Classify

1. **Collect reviewer comments**:
   - If $ARGUMENTS contains a file path, read that file
   - If $ARGUMENTS is empty, check `attachments/reviews/` for review files (`.txt`, `.md`, `.pdf`). If multiple files exist, process all of them (one per reviewer)
   - If no file is found and no comments were pasted, ask the user to provide reviewer comments
2. **Extract individual points** from each reviewer. Number them systematically:
   - R1.1, R1.2, R1.3... for Reviewer 1
   - R2.1, R2.2... for Reviewer 2
   - RE.1, RE.2... for Editor comments (if present)
   - Preserve the original wording of each point as a direct quote
3. **Classify each point** into one of four categories:
   - **CRITICAL** — Fundamental flaw, missing analysis, or methodological concern that must be addressed for acceptance
   - **MAJOR** — Significant issue that should be addressed (missing comparison, unclear explanation, weak evidence)
   - **MINOR** — Small improvements (typos, formatting, wording suggestions, missing references)
   - **PRAISE** — Positive feedback (acknowledge briefly in response; no manuscript change needed)
4. **Map each point to manuscript sections** — Read `main.tex` and identify which section(s), paragraph(s), or line(s) each comment refers to. Record the mapping as `R1.1 -> Section 3.2, paragraph 2` etc.

### Phase 2: Validate and Plan Responses

5. **Read supporting materials**:
   - `main.tex` — the current manuscript
   - `references.bib` — available citation keys
   - `research/sources/` — source extracts and full-text PDFs
   - `research/claims_matrix.md` — evidence-to-claim mappings (if it exists)
   - `research/notes/` — research notes (if they exist)

### Knowledge Graph Integration (Phase 2 enhancement)

For each reviewer point, after identifying the relevant claim(s) from the claims matrix,
use the best available evidence tier:

**Tier 1 — Pre-computed defense brief** (fastest, use when available):

If `research/prepared/defense/defense-brief.md` exists:
1. Read the per-claim defense sheet for the relevant claim
   (e.g., `research/prepared/defense/claim-C3.md`)
2. Use the pre-built objection responses and supporting/challenging evidence as starting
   points for drafting the response
3. Only run live graph queries (Tier 2) if the reviewer raises a specific point that the
   pre-computed defense does not cover

**Tier 2 — Live knowledge graph queries** (use when no defense brief exists):

First check availability: read `stages.knowledge_graph.available` from `.paper-state.json` if it exists, or check `[ -n "$OPENROUTER_API_KEY" ]` and whether `research/knowledge/` has content. If the knowledge graph is NOT available, skip to Tier 3 with a log message: `"⚠ Knowledge graph not available — falling back to manual source reading."`

If the knowledge graph IS available (`research/knowledge/` has been built):
1. Run: `python scripts/knowledge.py evidence-for "<reviewer's specific concern>"`
2. Run: `python scripts/knowledge.py evidence-against "<reviewer's specific concern>"`
3. Run: `python scripts/knowledge.py query "<any specific factual claim the reviewer makes>"`
4. If the reviewer challenges a methodology decision:
   Run: `python scripts/knowledge.py query "<specific methodological concern>"`
5. Use the results to determine whether the reviewer is correct, partially correct, or
   incorrect before drafting the response

**Tier 3 — Manual source reading** (fallback when no graph exists):

If neither a defense brief nor a built knowledge graph is available, continue with the
standard behavior: read `research/sources/` directly and cross-reference the claims matrix
by hand.

**Always** cross-reference `research/claims_matrix.md` (if it exists) for:
- Warrant quality — is this claim well-grounded, or is the reviewer identifying a real gap?
- Evidence score — how strong is the paper's position on this claim?
- Known rebuttals — has the paper already anticipated this objection?

6. **For each CRITICAL and MAJOR point**, determine:
   - **Is the reviewer correct?** Cross-reference claims against source extracts in `research/sources/` and the claims matrix. Check if the reviewer identified a genuine gap or misread the text.
   - **What is the appropriate response?**
     - If the reviewer is correct: plan a specific manuscript change (new text, revised analysis, additional citation, restructured argument)
     - If the reviewer misread or misunderstood: plan a clarification in the manuscript that makes the point unambiguous, plus a respectful explanation in the response. Never dismiss a reviewer — if they misunderstood, the writing was unclear.
     - If the reviewer requests something out of scope: explain why diplomatically, and offer what can be done within the paper's scope
   - **Draft the manuscript edit** — Write the exact new text. Only use citation keys that exist in `references.bib`. If a new reference is needed, note it explicitly so the user can add it.
7. **For each MINOR point**, plan a quick fix or a brief explanation if no change is warranted.
8. **For each PRAISE point**, draft a one-sentence acknowledgment.

### Phase 3: Generate Response Document

9. **Create `response_to_reviewers.tex`** in the project root with this structure:

```latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{hyperref}

% Reviewer comment styling
\definecolor{reviewercolor}{RGB}{80,80,80}
\definecolor{responsecolor}{RGB}{0,0,140}
\definecolor{changecolor}{RGB}{0,120,0}
\newcommand{\reviewerquote}[1]{\par\medskip\noindent\textcolor{reviewercolor}{\textit{#1}}\par\smallskip}
\newcommand{\response}[1]{\noindent\textcolor{responsecolor}{#1}}
\newcommand{\changeref}[1]{\textcolor{changecolor}{\textbf{[Change:} #1\textbf{]}}}

\begin{document}
\title{Response to Reviewers}
\maketitle

We thank the reviewers for their careful reading and constructive feedback.
Below we address each point individually. All changes are indicated in the
revised manuscript using blue text for additions and strikethrough for deletions.

\section*{Summary of Changes}
% Bulleted list of the most significant changes made

\section*{Reviewer 1}

\subsection*{R1.1 [CRITICAL]}
\reviewerquote{Exact reviewer quote here...}
\response{Our response explaining what was done and why...}
\changeref{Section X.Y, paragraph Z}

% ... repeat for all points ...

\end{document}
```

- Group points by reviewer
- Within each reviewer, order by severity: CRITICAL first, then MAJOR, MINOR, PRAISE
- Include the severity tag in each subsection header
- Every CRITICAL and MAJOR response must reference a specific location in the revised manuscript
- The "Summary of Changes" section should list the 5-10 most important changes as bullets

10. **If the user prefers Markdown** (check $ARGUMENTS for "md" or "markdown"), generate `response_to_reviewers.md` instead with equivalent formatting using blockquotes for reviewer comments and bold for responses.

### Phase 4: Generate Tracked-Changes Manuscript

11. **Create `main-revised.tex`** — a copy of `main.tex` with tracked changes:
    - Add `\usepackage[markup=default]{changes}` to the preamble (after other packages)
    - Add author definitions for tracking: `\definechangesauthor[name={Authors}, color=blue]{A}`
    - For every text that was modified:
      - Replaced text: `\replaced[id=A]{new text}{old text}`
      - Added text: `\added[id=A]{new text}`
      - Deleted text: `\deleted[id=A]{old text}`
    - Add a comment linking each change to the reviewer point: e.g., `% R1.2: strengthened evidence for claim X`
    - Do NOT apply changes to `main.tex` directly — the user must approve first

12. **Compile both documents**:
    - `latexmk -pdf -interaction=nonstopmode response_to_reviewers.tex`
    - `latexmk -pdf -interaction=nonstopmode main-revised.tex`
    - Report any compilation errors. Fix LaTeX issues (max 3 attempts each).

### Phase 5: Report

13. **Print a summary table**:

```
| # | Category | Section | Change | Status |
|-|-|-|-|-|
| R1.1 | CRITICAL | Sec 3.2 | Added comparison with baseline Y | Done |
| R1.2 | MAJOR | Sec 4.1 | Clarified statistical test | Done |
| R2.1 | MINOR | Sec 2 | Fixed typo | Done |
| R2.2 | PRAISE | — | Acknowledged | — |
```

14. **Flag unresolved items** — Any point where:
    - A new reference is needed but not yet in `references.bib`
    - New data or analysis is required that cannot be generated from existing materials
    - The reviewer requests access to code/data that needs to be prepared separately
    - The response requires author judgment (conflicting reviewer opinions, scope decisions)

15. **Remind the user**:
    - Review `response_to_reviewers.tex` for tone and accuracy
    - Review `main-revised.tex` to approve all tracked changes
    - Once approved, the user can copy the content from `main-revised.tex` back into `main.tex` (removing the `changes` package markup) or run `/prepare-submission` to generate the final package
    - If reviewers disagree with each other, flag the conflict explicitly and let the user decide

## Edge Cases

- **Reviewer comments in non-English**: Translate to English for the response, but quote the original language as well
- **Vague reviewer comments** (e.g., "The writing needs improvement"): Ask the user for clarification, or apply best-effort interpretation and flag it as needing review
- **Contradictory reviewers** (R1 says X is a strength, R2 says X is a weakness): Address both perspectives, note the disagreement, and let the user decide the approach
- **Comments about supplementary materials**: If the paper has supplementary content, include changes there too. If not, note that supplementary material may need to be created.
- **Second-round reviews** (R1 on revision): Check if `response_to_reviewers.tex` already exists. If so, create `response_to_reviewers_r2.tex` and `main-revised-r2.tex` to avoid overwriting the first round.

## Arguments

$ARGUMENTS

Accepts: reviewer comments (pasted text), a file path to review comments, or "md"/"markdown" to generate Markdown output instead of LaTeX. If empty, searches `attachments/reviews/` for review files.
