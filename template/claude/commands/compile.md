# Compile LaTeX

Compile the paper and report results.

## Instructions

1. **Format and lint source**: Run `python scripts/format_sentences.py main.tex` to apply one-sentence-per-line formatting, non-breaking spaces before `\ref`/`\eqref`, smart quotes, `\ldots`, en-dashes for ranges, and whitespace cleanup. This produces cleaner diffs without affecting compiled output.
2. **Check that `latexmk` is available**: `which latexmk`. If not found, try `pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex` as fallback.
3. Run `latexmk -pdf -interaction=nonstopmode main.tex`
4. Parse the output for:
   - **Errors**: Report each with file, line number, and the error message
   - **Warnings**: Report overfull/underfull boxes, undefined references, missing citations
   - **Success**: Confirm PDF was generated
5. If there are errors:
   - Read the relevant lines in `main.tex`
   - Fix the issues
   - Recompile — but **maximum 3 fix-recompile cycles**. If still failing after 3, report the remaining errors and stop.
6. On success, report page count (if `pdfinfo` is available: `pdfinfo main.pdf | grep Pages`, otherwise skip)

$ARGUMENTS
