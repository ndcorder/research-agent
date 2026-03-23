# Clean — Remove Build Artifacts and Working Files

Clean up LaTeX build artifacts and optionally remove working directories.

## Instructions

1. **Always clean LaTeX artifacts**:
   - If `latexmk` is available: run `latexmk -c`
   - Otherwise: `rm -f *.aux *.bbl *.blg *.fdb_latexmk *.fls *.log *.out *.synctex.gz *.toc`
2. **Report** what was cleaned

3. **If `all` is in arguments**, also remove working directories:
   - `research/` — intermediate research notes (not the final paper)
   - `reviews/` — review feedback (already incorporated into revisions)
   - `archive/` — research archive (can be regenerated with `/archive`)
   - `.paper-state.json` — pipeline state (allows fresh restart)
   - `.paper-progress.txt` — progress file
   - `figures/scripts/` — figure generation scripts (figures themselves are kept)
   - **IMPORTANT**: Before deleting, list what will be removed and warn the user. Proceed with deletion — if they didn't want this, they should not have passed `all`.

4. **Never delete**:
   - `main.tex`, `references.bib`, `.paper.json`, `.venue.json`
   - `figures/*.pdf` (generated figures are part of the paper)
   - `attachments/` (user-provided materials)
   - `vendor/`, `.claude/`, `.git/`

## Arguments

$ARGUMENTS

Usage: `/clean` (artifacts only) or `/clean all` (artifacts + working dirs)
