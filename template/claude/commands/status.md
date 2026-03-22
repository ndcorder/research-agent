# Status — Paper Progress Dashboard

Show the current state of the paper writing pipeline.

## Instructions

1. **Read `.paper-state.json`** if it exists for pipeline stage tracking
2. **Analyze `main.tex`**:
   - Count words per section (strip LaTeX commands for approximate count)
   - List all `\section{}` and `\subsection{}` headings
   - Check for placeholder text (TODO, TBD, FIXME, \lipsum, \mbox{})
   - Count `\citep{}` and `\citet{}` usage
   - Count `\ref{}` cross-references
   - Check for unresolved references (compile and check log)
3. **Analyze `references.bib`**:
   - Count total entries
   - List entry types breakdown (@article, @inproceedings, etc.)
   - Check for entries not cited in main.tex
   - Check for citation keys used in main.tex but missing from .bib
4. **Check research files**: List files in `research/` with sizes
5. **Check review files**: List files in `reviews/` with sizes
6. **Check figures**: List files in `figures/`
7. **Compile check**: Run `latexmk -pdf -interaction=nonstopmode main.tex` and report errors/warnings
8. **Get page count**: `pdfinfo main.pdf 2>/dev/null | grep Pages`

**Output format:**

```
Paper: [topic from .paper.json]
Venue: [venue or "generic"]

SECTIONS                    Words    Target   Status
─────────────────────────────────────────────────
Introduction                1205     1000     ✓
Related Work                 843     1500     ▸ needs 657 more
Methods                        0     2000     ○ not started
...
─────────────────────────────────────────────────
Total                       2048     8000

REFERENCES: 32 entries (28 cited, 4 orphaned)
FIGURES:    3 files in figures/
REVIEWS:    2 files in reviews/
COMPILES:   ✓ clean (12 pages)

PIPELINE STAGE: Stage 3 — Writing (Methods next)
```

Also write this status to `.paper-progress.txt` so it can be monitored from another terminal via `cat .paper-progress.txt`.

$ARGUMENTS
