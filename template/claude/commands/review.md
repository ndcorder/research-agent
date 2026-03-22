# Review Manuscript

Perform a comprehensive review of the current manuscript.

## Instructions

1. **Read `main.tex`** completely
2. **Evaluate against these criteria**, reporting issues by severity (critical / major / minor):

### Structure & Completeness
- All IMRAD sections present and properly ordered
- Abstract within 150-300 words, captures key contribution
- Introduction states clear research question and contribution
- Methods reproducible by another researcher
- Results supported by data (tables, figures, statistics)
- Discussion interprets findings, acknowledges limitations
- Conclusion does not introduce new information

### Writing Quality
- Full paragraphs throughout (no bullet points in body)
- Clear topic sentences for each paragraph
- Logical transitions between paragraphs and sections
- No vague language ("various", "some", "interesting")
- Active voice preferred over passive
- Consistent tense (past for methods/results, present for established facts)

### Technical Quality
- All claims supported by citations or data
- Figures/tables referenced in text before they appear
- All `\ref{}` and `\citep{}`/`\citet{}` resolve correctly
- No placeholder text (`\lipsum`, TODO, TBD, FIXME)
- Statistical results properly reported (test, df, p-value, effect size)

### LaTeX Quality
- Compiles without errors: `latexmk -pdf -interaction=nonstopmode main.tex`
- No overfull/underfull hbox warnings above 1pt
- Figures use vector format where possible
- Tables use `booktabs` style
- Cross-references all resolve

3. **Output a structured review** with:
   - Summary assessment (1-2 sentences)
   - Numbered list of issues by severity
   - Specific suggestions for each issue, with line references

$ARGUMENTS
