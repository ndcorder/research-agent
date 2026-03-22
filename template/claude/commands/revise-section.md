# Revise Section

Rewrite a specific section of the paper based on feedback or quality criteria.

## Instructions

The user specifies a section and optionally provides feedback (reviewer comments, quality issues, etc.).

1. **Parse the section name** from $ARGUMENTS. If no section specified, ask the user which section to revise.
2. **Read `main.tex`** and locate the target section. If the section doesn't exist (typo or missing heading), report the available sections and ask for clarification.
3. **Analyze the current text** for:
   - Clarity and precision of language
   - Logical flow and argumentation
   - Adequacy of citations
   - Technical accuracy
   - Paragraph structure (no bullet points)
4. **If feedback is provided**, address each point specifically
5. **If no feedback**, apply general improvements:
   - Strengthen topic sentences
   - Improve transitions
   - Eliminate vague language
   - Add missing citations — but **only use keys that exist in `references.bib`**. Read `references.bib` first to know available keys. Never insert a `\citep{}` or `\citet{}` with a key that isn't in the bib file.
   - Ensure consistent terminology
6. **Rewrite the section** in `main.tex` using the Edit tool
7. **Compile** to verify no LaTeX errors: `latexmk -pdf -interaction=nonstopmode main.tex` (max 3 attempts)
8. **Report** what changed and why

## Section and Feedback

$ARGUMENTS
