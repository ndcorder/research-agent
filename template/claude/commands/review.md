# Review Manuscript

Perform a comprehensive review of the current manuscript.

## Instructions

1. **Read `main.tex`** completely
2. **Evaluate against these criteria**, reporting issues by severity (Critical / Major / Minor):

### Structure and Completeness
- All expected sections present (check `.venue.json` for venue-specific sections, or default IMRAD)
- Abstract within word limit (check `.venue.json` for `abstract_word_limit`)
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
- Consistent tense

### Technical Quality
- All claims supported by citations or data
- Figures/tables referenced in text before they appear
- All `\ref{}` and `\citep{}`/`\citet{}` resolve correctly
- No placeholder text (TODO, TBD, FIXME, \lipsum)

### LaTeX Quality
- Compile with: `latexmk -pdf -interaction=nonstopmode main.tex`
- Report errors and significant warnings

3. **Output a structured review** with:
   - Summary assessment (1-2 sentences)
   - Issues grouped by severity (Critical, Major, Minor)
   - Specific suggestions with line references
   - Per-section word counts

## Arguments

$ARGUMENTS

Accepts an optional focus area (e.g., "writing quality", "technical"). If empty, review everything.
