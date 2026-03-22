# Citation Network — Visualize Reference Coverage

Analyze citation patterns and identify coverage gaps in the bibliography.

## Instructions

1. **Parse `references.bib`**: Extract all entries with their metadata (authors, year, title, venue)
2. **Parse `main.tex`**: Find all `\citep{}` and `\citet{}` occurrences, map which section cites which reference
3. **Generate analysis**:

### Citation Distribution
- Citations per section (which sections cite heavily, which are thin)
- Citations by year (histogram — are references recent enough?)
- Citations by venue type (journal vs conference vs preprint)
- Author frequency (which authors appear most — potential bias?)

### Coverage Analysis
- **Temporal coverage**: Flag if >50% of references are older than 5 years
- **Venue diversity**: Flag if >50% from same venue
- **Author diversity**: Flag if any author appears in >20% of references
- **Self-citation check**: Flag potential self-citations if author names overlap with paper authors
- **Recency check**: Are the most recent state-of-the-art papers included?

### Gap Identification
- Sections with fewer than 3 citations (may need more references)
- Research themes from `research/survey.md` that lack corresponding citations
- Methodological approaches mentioned but not cited
- Comparisons claimed but baselines not cited

### Orphan Detection
- References in .bib never cited in text (candidates for removal)
- Citation keys in text not found in .bib (broken references)

4. **Generate visualization** (if matplotlib available):
   - Save a citation timeline plot to `figures/citation_timeline.pdf`
   - Save a section-citation heatmap to `figures/citation_heatmap.pdf`

5. **Write report** to `research/citation_analysis.md`
6. **Suggest specific papers** to add for identified gaps (use Perplexity/web search)

$ARGUMENTS
