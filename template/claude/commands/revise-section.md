# Revise Section

Rewrite a specific section of the paper based on feedback or quality criteria.

## Instructions

The user specifies a section and optionally provides feedback (reviewer comments, quality issues, etc.).

1. **Read `main.tex`** and locate the target section
2. **Analyze the current text** for:
   - Clarity and precision of language
   - Logical flow and argumentation
   - Adequacy of citations
   - Technical accuracy
   - Paragraph structure (no bullet points)
3. **If feedback is provided**, address each point specifically
4. **If no feedback**, apply general improvements:
   - Strengthen topic sentences
   - Improve transitions
   - Eliminate vague language
   - Add missing citations where claims need support
   - Ensure consistent terminology
5. **Rewrite the section** in `main.tex` using the Edit tool
6. **Compile** to verify no LaTeX errors introduced: `latexmk -pdf -interaction=nonstopmode main.tex`
7. **Show a summary** of what changed and why

## Section and Feedback

$ARGUMENTS
