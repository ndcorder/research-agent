# Stage 1b: Citation Snowballing

> **Prerequisites**: Read `pipeline/shared-protocols.md` first.

---

**Goal**: Discover papers that keyword search structurally cannot find by following the citation graph one level deep.

This stage takes the top seed papers from `references.bib` and chases their citations (backward) and citing papers (forward) via the Semantic Scholar API.

#### Seed Selection

Select seed papers from `references.bib` by three criteria:
1. **Most-cited in research files** — papers referenced across multiple research agent outputs (survey.md, methods.md, etc.)
2. **Foundational papers** — oldest papers in the bibliography (likely seminal works)
3. **Most recent papers** — 2024-2026 papers whose citation graphs contain the latest work

Standard mode: 10 seed papers. Deep mode: 20 seed papers.

#### Backward and Forward Snowballing Agents

Spawn both agents in parallel.

**Backward Snowballing Agent** (model: claude-sonnet-4-6[1m])
```
You are a citation analyst performing backward snowballing.
TOPIC: [TOPIC]
SEED PAPERS: [list of seed BibTeX keys with titles and DOIs from references.bib]

For each seed paper:
1. Fetch its reference list using Semantic Scholar API:
   https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=references.title,references.authors,references.year,references.externalIds,references.citationCount
2. If DOI not available, search by title:
   https://api.semanticscholar.org/graph/v1/paper/search?query=<title>&fields=references.title,references.authors,references.year,references.externalIds,references.citationCount
3. From each paper's reference list, identify references that are:
   - Relevant to [TOPIC] (title/author match)
   - NOT already in references.bib
   - Highly cited (citationCount > 50) OR very recent (2024-2026)
4. For each candidate, check if it's already in references.bib by title similarity and DOI match

SEMANTIC SCHOLAR RATE LIMITING: [include from shared-protocols.md]
Maximum new papers to report: 15 (standard) / 30 (deep).

Output: A deduplicated list of discovered papers with full metadata (authors, title, venue, year, DOI, citation count, which seed paper led to them).
Write to research/snowball_backward.md.
Create source extracts in research/sources/ for each new paper found (access level: METADATA-ONLY unless abstract is available from the API response).
RESEARCH LOG: Log every API call to research/log.md with timestamp, tool, query, result summary, and URLs/DOIs found.
```

**Forward Snowballing Agent** (model: claude-sonnet-4-6[1m])
```
You are a citation analyst performing forward snowballing.
TOPIC: [TOPIC]
SEED PAPERS: [list of seed BibTeX keys with titles and DOIs — focus on seminal/older papers]

For each seed paper:
1. Fetch papers that cite it using Semantic Scholar API:
   https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=citations.title,citations.authors,citations.year,citations.externalIds,citations.citationCount
2. If DOI not available, search by title first to get the Semantic Scholar paper ID, then fetch citations.
3. From the citing papers, identify those that are:
   - Relevant to [TOPIC]
   - NOT already in references.bib
   - Recent: 2023-2026 (standard) / 2020-2026 (deep)
4. Prioritize papers with high citation counts (emerging influential work)
5. For very old seminal papers with thousands of citations, cap at top 50 by citation count and filter by recency

SEMANTIC SCHOLAR RATE LIMITING: [include from shared-protocols.md]
Maximum new papers to report: 15 (standard) / 30 (deep).

Output: A deduplicated list of discovered papers with full metadata (authors, title, venue, year, DOI, citation count, which seed paper led to them).
Write to research/snowball_forward.md.
Create source extracts in research/sources/ for each new paper found (access level: METADATA-ONLY unless abstract is available from the API response).
RESEARCH LOG: Log every API call to research/log.md with timestamp, tool, query, result summary, and URLs/DOIs found.
```

#### Integration

After both agents complete, spawn a **Snowball Bibliography Builder** (model: claude-sonnet-4-6[1m]):
```
You are a meticulous bibliographer processing snowballing results.
Read research/snowball_backward.md and research/snowball_forward.md.
Read the current references.bib.

For each discovered paper:
1. Verify it is not already in references.bib (check by DOI, title similarity, and author last names)
2. Search to verify it is a real publication (use Perplexity, web search, or domain databases)
3. Find complete metadata and generate a BibTeX entry
4. Add verified entries to references.bib under a new % Snowballing section

Report: total candidates from backward, total from forward, duplicates removed, new entries added.
RESEARCH LOG: Log every verification to research/log.md.
```

Update `research/source_coverage.md` counts after new papers are added.

#### Depth Mode Differences

| Setting | Standard | Deep |
|-|-|-|
| Seed papers | 10 | 20 |
| Max new papers per direction | 15 | 30 |
| Citation depth | 1 level | 1 level |
| Forward snowball time window | 2023-2026 | 2020-2026 |

#### Rate Limiting

Semantic Scholar API allows 100 requests/5 minutes without a key. With 10 seeds x 2 directions = 20 requests, well within limits. Deep mode (20 seeds) may need brief pauses. Both agents must follow the Semantic Scholar Rate Limiting Protocol from `pipeline/shared-protocols.md`.

**Checkpoint**: Verify `research/snowball_backward.md` and `research/snowball_forward.md` exist. Log snowballing stats in `.paper-state.json`.

Update `.paper-state.json`: mark `snowballing` as done with stats.
