# Compile LaTeX

Compile the paper and report results.

## Instructions

1. Run `latexmk -pdf -interaction=nonstopmode main.tex`
2. Parse the output for:
   - **Errors**: Report each with file, line number, and the error message
   - **Warnings**: Report overfull/underfull boxes, undefined references, missing citations
   - **Success**: Confirm PDF was generated, report page count with `pdfinfo main.pdf 2>/dev/null | grep Pages`
3. If there are errors:
   - Read the relevant lines in `main.tex`
   - Fix the issues
   - Recompile and verify the fix
4. Report final status

$ARGUMENTS
