# Stage 1b-ii: Co-Citation & Bibliometric Analysis

> **Prerequisites**: Read `pipeline/shared-protocols.md` first. Stage 1b (snowballing) must be complete.

---

**Goal**: Identify important papers missing from the bibliography by analyzing co-citation patterns — papers that the research community frequently cites alongside your existing references.

Two papers are "co-cited" when a third paper cites both. High co-citation frequency between papers A and B means they are intellectually related. If your bibliography contains A but not B, and A-B co-citation is very high, you are likely missing a reference that reviewers will expect.

#### Reference Selection

Select references from `references.bib` for analysis:
- Standard mode: Top 20 by citation count
- Deep mode: All references with DOIs

#### Co-Citation Analysis Agent

Spawn a single agent (model: claude-sonnet-4-6[1m]):

```
You are a bibliometric analyst performing co-citation analysis.
TOPIC: [TOPIC]
REFERENCES: [list of selected BibTeX keys with titles and DOIs from references.bib]
EXISTING_TITLES: [list of all titles in references.bib for deduplication]

For each reference with a DOI:
1. Use the Semantic Scholar recommendations API to find papers frequently co-cited with it:
   https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:<doi>?fields=title,authors,year,externalIds,citationCount&limit=10
   (Deep mode: limit=20)
2. If no DOI, try searching by title first:
   https://api.semanticscholar.org/graph/v1/paper/search?query=<title>&limit=1
   Then use the returned paperId for recommendations:
   https://api.semanticscholar.org/recommendations/v1/papers/forpaper/<paperId>?fields=title,authors,year,externalIds,citationCount&limit=10
3. If the recommendations API fails for a paper, fall back to the citations endpoint:
   https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=citations.paperId,citations.title,citations.year,citations.citationCount
   Then count which cited papers appear across multiple of our references' citation lists.

SEMANTIC SCHOLAR RATE LIMITING: [include from shared-protocols.md]

After collecting all recommendations:
4. For each recommended paper, count how many of our existing references it was co-recommended with
5. Filter out papers already in references.bib (match by DOI or title similarity — normalize case and remove punctuation for comparison)
6. Compute score: (number of co-citation links to our bibliography) × log(citationCount + 1)
7. Rank by score descending

Classify results:
- HIGH CONFIDENCE: Co-cited with 3+ references (standard) or 3+ references (deep)
- MEDIUM CONFIDENCE: Co-cited with 2 references

Write the full analysis to research/cocitation_analysis.md using this format:

# Co-Citation Analysis
Generated: [timestamp]
Analyzed [N] references from bibliography.

## High-Confidence Missing References
Papers co-cited with 3+ papers in your bibliography:

| Rank | Title | Authors | Year | Co-cited With | Score | Action |
|-|-|-|-|-|-|-|
| 1 | "Paper Title" | Author et al. | 2024 | key1, key2, key3 | 12.4 | RECOMMEND ADDING |

## Medium-Confidence Suggestions
Papers co-cited with 2 papers in your bibliography:

| Rank | Title | Authors | Year | Co-cited With | Score | Action |
|-|-|-|-|-|-|-|

## Citation Clusters
[DEEP MODE ONLY] Groups of papers frequently cited together (intellectual communities):

### Cluster 1: [theme]
- paper1, paper2, paper3 — your coverage: 2/3

### Cluster 2: [theme]
- paper4, paper5, paper6 — your coverage: 1/3 ⚠ gap

## API Call Log
[List every API call: timestamp, endpoint, parameters, result count]

Create source extracts in research/sources/ for each high-confidence missing paper (access level: METADATA-ONLY unless abstract is available from the API response).
RESEARCH LOG: Log every API call to research/log.md with timestamp, tool, query, result summary, and URLs/DOIs found.
```

#### Integration

After the co-citation agent completes:

1. **High-confidence missing references** (co-cited with 3+ existing refs): Spawn a **Co-Citation Bibliography Builder** (model: claude-sonnet-4-6[1m]):
```
You are a meticulous bibliographer processing co-citation analysis results.
Read research/cocitation_analysis.md.
Read the current references.bib.

For each HIGH CONFIDENCE missing reference:
1. Verify it is not already in references.bib (check by DOI, title similarity, and author last names)
2. Search to verify it is a real publication (use Perplexity, web search, or domain databases)
3. Find complete metadata and generate a BibTeX entry
4. Add verified entries to references.bib under a new % Co-citation analysis section

Report: total candidates, verified, duplicates skipped, new entries added.
RESEARCH LOG: Log every verification to research/log.md.
```

2. **Medium-confidence suggestions**: Left in `research/cocitation_analysis.md` for the pipeline (or user in interactive mode) to evaluate. Writing agents can consult this file when they need additional references.

3. **Citation cluster gaps** (deep mode only): Flagged in the analysis report. Writing agents should check `research/cocitation_analysis.md` for cluster gaps relevant to their section.

#### Depth Mode Differences

| Setting | Standard | Deep |
|-|-|-|
| References analyzed | Top 20 by citation count | All references |
| Recommendation limit per paper | 10 | 20 |
| Auto-add threshold | Co-cited with 3+ | Co-cited with 3+ |
| Cluster analysis | Skip | Include |

#### Rate Limiting

Semantic Scholar recommendations API: 100 requests/5 minutes without a key. With 20 references at 1 request each, well within limits. Deep mode with all references may need pacing. The agent must follow the Semantic Scholar Rate Limiting Protocol from `pipeline/shared-protocols.md`.

**Checkpoint**: Verify `research/cocitation_analysis.md` exists. Update `.paper-state.json`: mark `cocitation` as done with stats (references_analyzed, high_confidence_found, medium_confidence_found, auto_added).
