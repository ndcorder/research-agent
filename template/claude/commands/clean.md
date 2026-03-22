# Clean — Remove Build Artifacts and Working Files

Clean up LaTeX build artifacts and optionally remove working directories.

## Instructions

1. **Always clean LaTeX artifacts**: Run `latexmk -c` to remove .aux, .bbl, .blg, .fdb_latexmk, .fls, .log, .out, .synctex.gz, .toc
2. **Report what was cleaned** and disk space freed
3. **If `--all` or `all` is in arguments**, also:
   - Remove `research/` directory (research notes — these are intermediate, not the final paper)
   - Remove `reviews/` directory (review feedback — already incorporated)
   - Remove `.paper-state.json` (pipeline state — allows fresh restart)
   - Remove `.paper-progress.txt` (progress file)
   - **Ask for confirmation before deleting these** — they represent work that may be useful
4. **Never delete**:
   - `main.tex`, `references.bib`, `.paper.json` (the actual paper)
   - `figures/` (generated figures are part of the paper)
   - `attachments/` (user-provided reference materials)
   - `vendor/` (skills submodule)
   - `.claude/` (project configuration)
   - `.git/` (version history)

$ARGUMENTS
