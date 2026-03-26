# Citation Network — Visualize Reference Coverage

Analyze citation patterns and identify coverage gaps in the bibliography.

## Instructions

1. **Parse `references.bib`**: Extract all entries with metadata (authors, year, title, venue)
2. **Parse `main.tex`**: Find all `\citep{}` and `\citet{}` occurrences, map which section cites which reference
3. **Generate analysis**:

### Citation Distribution
- Citations per section (which sections cite heavily, which are thin)
- Citations by year (are references recent enough?)
- Citations by venue type (journal vs conference vs preprint)
- Author frequency (which authors appear most — potential bias?)

### Coverage Analysis
- **Temporal**: Flag if >50% of references are older than 5 years
- **Venue diversity**: Flag if >50% from same venue
- **Author diversity**: Flag if any author appears in >20% of references
- **Recency**: Are the most recent state-of-the-art papers included?

### Gap Identification
- Sections with fewer than 3 citations (may need more references)
- If `research/survey.md` exists, cross-reference themes against citation coverage
- Methodological approaches mentioned but not cited
- Comparisons claimed but baselines not cited

### Orphan Detection
- References in .bib never cited in text (candidates for removal)
- Citation keys in text not found in .bib (broken references)

### Co-Citation Analysis
Use the Semantic Scholar recommendations API to find papers frequently co-cited with your existing references but missing from the bibliography.

For each reference in `references.bib` that has a DOI (up to the top 20 by citation count):
1. Fetch recommendations: `https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:<doi>?fields=title,authors,year,externalIds,citationCount&limit=10`
2. If no DOI, search by title first: `https://api.semanticscholar.org/graph/v1/paper/search?query=<title>&limit=1`, then use the paperId for recommendations
3. If the recommendations API fails, fall back to the citations endpoint and count co-citation overlap manually

For each recommended paper:
- Count how many existing references it was co-recommended with
- Filter out papers already in `references.bib` (match by DOI or title similarity)
- Score: (co-citation link count) × log(citationCount + 1)

Report results in two tiers:
- **High-confidence missing refs** (co-cited with 3+ of your references): strong candidates for addition
- **Medium-confidence suggestions** (co-cited with 2 of your references): worth evaluating

Add 3-second delays between API requests. Handle 429 responses with 5-second backoff.

4. **Generate visualizations** if Python with matplotlib is available:
   - Run `python3 -c "import matplotlib"` to check availability
   - If available: save citation timeline and section heatmap to `figures/`
   - If not available: skip visualization, report data in text tables only

5. **Write report** to `research/citation_analysis.md`
6. **Suggest specific papers** to add for identified gaps (use Perplexity or web search)

## Arguments

$ARGUMENTS

Runs on current `main.tex` and `references.bib`. No arguments required.
