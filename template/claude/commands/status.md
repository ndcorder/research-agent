# Status — Paper Progress Dashboard

Show the current state of the paper writing pipeline.

## Instructions

1. **Read `.paper-state.json`** if it exists for pipeline stage tracking. If not, report "No pipeline state found."
2. **Read `.paper.json`** for topic and target_words. If not found, use defaults (topic: "unknown", target: 8000).
3. **Read `.venue.json`** for venue name. If not found, use "generic".
4. **Analyze `main.tex`**:
   - Find all `\section{}` headings
   - Count words per section (strip LaTeX commands: remove `\command{...}`, `\command`, `{}`, `\\`, `%` comments, then count remaining words). This is approximate — that's fine.
   - Check for placeholder text (TODO, TBD, FIXME, \lipsum, \mbox{})
   - Count `\citep{}` and `\citet{}` usage
5. **Analyze `references.bib`**: Count total entries
6. **Check directories**: Report if `research/`, `reviews/`, `figures/` exist and their file counts
7. **Compile check**: Run `latexmk -pdf -interaction=nonstopmode main.tex 2>&1 | tail -5` and report success/failure. If `pdfinfo` available, report page count.

**Output format** (use plain text, no box-drawing characters):

```
Paper: [topic]
Venue: [venue]

SECTIONS                    Words    Target   Status
Introduction                1205     1000     ok
Related Work                 843     1500     needs 657 more
Methods                        0     2000     not started
...
Total                       2048     8000

REFERENCES: 32 entries
FIGURES:    3 files
REVIEWS:    2 files
COMPILES:   ok (12 pages)
PIPELINE:   Stage 3 - Writing (Methods next)
```

Word count targets per section: Introduction=1000, Related Work=1500, Methods=2000, Results=1500, Discussion=1200, Conclusion=500, Abstract=300. Scale proportionally if `.paper.json` `target_words` differs from 8000.

Also write this output to `.paper-progress.txt` so it can be monitored from another terminal.

$ARGUMENTS
