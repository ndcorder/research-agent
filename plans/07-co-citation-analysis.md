# Plan 07: Co-Citation & Bibliometric Analysis

## Problem

When experienced researchers review a paper, they intuitively notice missing "expected" references — papers that are almost always cited alongside other papers in the bibliography. If your paper cites Transformer attention (Vaswani et al. 2017) but doesn't cite BERT (Devlin et al. 2019) in an NLP context, that's suspicious. The current pipeline has no mechanism to detect these gaps because it never analyzes how its references relate to each other in the broader citation network.

## Goal

Add a co-citation analysis step after the bibliography is built, identifying papers that are frequently co-cited with the current references but missing from the bibliography.

## Design

### What is Co-Citation Analysis?

Two papers are "co-cited" when a third paper cites both of them. High co-citation frequency between papers A and B means they're viewed as intellectually related by the research community. If your bibliography contains A but not B, and A-B co-citation is very high, you're likely missing an important reference that reviewers will expect.

### New Stage: Stage 1b-ii — Bibliometric Analysis

Runs after citation snowballing (Plan 01) and before Stage 1c (Codex cross-check). Uses the Semantic Scholar API to pull co-citation data.

### Implementation

#### Step 1: Build Co-Citation Pairs

For each paper in `references.bib` (or a subset of the most important 20-30):

```
WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=citations.paperId,citations.title,citations.year,citations.citationCount
```

This returns papers that cite this reference. For each citing paper, it also cites other papers — those are co-cited with our reference.

More efficiently, use the **Recommendations API**:
```
WebFetch: https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:<doi>?fields=title,authors,year,externalIds,citationCount&limit=10
```

This returns papers frequently appearing alongside the input paper — essentially co-citation recommendations.

#### Step 2: Aggregate and Score

For each recommended paper:
- Count how many of our existing references it's co-cited with
- Weight by the citation count of the co-citing papers
- Filter out papers already in `references.bib`

Score = (number of co-citation links to our bibliography) × log(citation count)

#### Step 3: Report

Write `research/cocitation_analysis.md`:

```markdown
# Co-Citation Analysis
Generated: [timestamp]

## High-Confidence Missing References
Papers co-cited with 3+ papers in your bibliography:

| Rank | Title | Authors | Year | Co-cited With | Score | Already Cited? |
|-|-|-|-|-|-|-|
| 1 | "BERT: Pre-training..." | Devlin et al. | 2019 | vaswani2017, radford2018, liu2019 | 12.4 | NO — recommend adding |
| 2 | ... | ... | ... | ... | ... | ... |

## Medium-Confidence Suggestions
Papers co-cited with 2 papers in your bibliography:
[table]

## Citation Clusters
Groups of papers frequently cited together (intellectual communities):

### Cluster 1: [theme]
- paper1, paper2, paper3 — your coverage: 2/3

### Cluster 2: [theme]
- paper4, paper5, paper6 — your coverage: 1/3 ⚠ gap
```

#### Step 4: Integration

- High-confidence missing references (co-cited with 3+) are automatically added to the bibliography builder queue for verification and inclusion
- Medium-confidence suggestions are presented to the pipeline (or user in interactive mode) for judgment
- Citation cluster gaps are flagged in the research notes for the writing agents

### Agent Design

Single agent (model: claude-sonnet-4-6[1m]):

```
You are a bibliometric analyst performing co-citation analysis.
REFERENCES: [list of top 20-30 BibTeX keys with DOIs]

For each reference with a DOI:
1. Use the Semantic Scholar recommendations API to find papers frequently co-cited with it:
   https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:<doi>?fields=title,authors,year,externalIds,citationCount&limit=10
2. If no DOI, try by title:
   https://api.semanticscholar.org/graph/v1/paper/search?query=<title>&limit=1
   Then use the paperId for recommendations.
3. Collect all recommended papers across all references
4. For each recommended paper, count how many of our references it's co-recommended with
5. Filter out papers already in references.bib (match by title similarity or DOI)
6. Rank by co-citation count × log(citationCount)

Write the analysis to research/cocitation_analysis.md.
Create source extracts for top-ranked missing papers.
RESEARCH LOG: Log all API calls to research/log.md.
```

### Depth Mode

| Setting | Standard | Deep |
|-|-|-|
| References analyzed | Top 20 by citation count | All references |
| Recommendation limit per paper | 10 | 20 |
| Auto-add threshold | Co-cited with 4+ | Co-cited with 3+ |
| Cluster analysis | Skip | Include |

### Rate Limiting

Semantic Scholar recommendations API: same 100/5min limit. With 20-30 references, this is manageable. Add 3-second delays between requests if needed.

## Files to Modify

1. `template/claude/commands/write-paper.md` — Update orchestrator stage table to include Stage 1b-ii
2. `template/claude/commands/cite-network.md`:
   - Integrate co-citation analysis into the standalone cite-network command
3. `template/claude/CLAUDE.md`:
   - Document co-citation analysis in pipeline overview

## Files to Create

1. `template/claude/pipeline/stage-1b2-cocitation.md` — New pipeline stage file for co-citation analysis

## Risks

- Semantic Scholar recommendations API may not be available for all papers. Mitigation: fall back to manual co-citation counting via the citations endpoint.
- Co-citation analysis biases toward popular papers (rich-get-richer). Mitigation: this is actually desirable for a research paper — you WANT to cite the well-known related work.
- May suggest papers that are famous but not actually relevant to the specific topic. Mitigation: the agent filters by topic relevance, and suggestions are verified before inclusion.

## Acceptance Criteria

- [ ] Co-citation analysis runs after snowballing in the pipeline
- [ ] Uses Semantic Scholar recommendations API with fallback
- [ ] Reports high-confidence missing refs, medium-confidence suggestions, and citation clusters
- [ ] High-confidence missing refs auto-added to bibliography builder
- [ ] Citation cluster gaps flagged for writing agents
- [ ] Research log captures all API calls
- [ ] Standalone `/cite-network` command also performs co-citation analysis
