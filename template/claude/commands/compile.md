# Compile LaTeX

Compile the paper and report results.

## Instructions

1. **Check that `latexmk` is available**: `which latexmk`. If not found, try `pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex` as fallback.
2. Run `latexmk -pdf -interaction=nonstopmode main.tex`
3. Parse the output for:
   - **Errors**: Report each with file, line number, and the error message
   - **Warnings**: Report overfull/underfull boxes, undefined references, missing citations
   - **Success**: Confirm PDF was generated
4. If there are errors:
   - Read the relevant lines in `main.tex`
   - Fix the issues
   - Recompile — but **maximum 3 fix-recompile cycles**. If still failing after 3, report the remaining errors and stop.
5. On success, report page count (if `pdfinfo` is available: `pdfinfo main.pdf | grep Pages`, otherwise skip)

$ARGUMENTS
