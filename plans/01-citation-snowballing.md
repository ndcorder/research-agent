# Plan 01: Citation Snowballing

## Problem

The research phase discovers papers through keyword search but never follows the citation graph. This misses papers that use different terminology for the same concepts, papers from adjacent fields, and the "expected" references that reviewers will look for. Systematic review methodology considers snowballing essential alongside database searching.

## Goal

Add backward and forward citation snowballing as a post-bibliography-builder step in Stage 1, so the pipeline discovers papers that keyword search structurally cannot find.

## Design

### New Stage: Stage 1b — Citation Snowballing

Runs after the bibliography builder completes and before Stage 1c (Codex cross-check). Takes the top N seed papers from `references.bib` and chases their citation graphs one level deep.

### Seed Selection

Not all references are worth snowballing. Select seeds by:
1. **Most-cited in the research files** — papers referenced across multiple research agent outputs (survey.md, methods.md, etc.)
2. **Foundational papers** — oldest papers in the bibliography (likely seminal works)
3. **Most recent papers** — 2024-2026 papers whose citation graphs contain the latest work

Standard mode: 10 seed papers. Deep mode: 20 seed papers.

### Backward Snowballing Agent (model: claude-sonnet-4-6[1m])

```
You are a citation analyst performing backward snowballing.
TOPIC: [TOPIC]
SEED PAPERS: [list of seed BibTeX keys with titles]

For each seed paper:
1. Fetch its reference list using Semantic Scholar API:
   https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=references.title,references.authors,references.year,references.externalIds,references.citationCount
2. If DOI not available, search by title:
   https://api.semanticscholar.org/graph/v1/paper/search?query=<title>&fields=references.title,references.authors,references.year,references.externalIds,references.citationCount
3. From each paper's reference list, identify references that are:
   - Relevant to [TOPIC] (title/author match)
   - NOT already in references.bib
   - Highly cited (citationCount > 50) OR very recent (2024-2026)
4. For each candidate, check if it's already in references.bib by title similarity

Output: A deduplicated list of discovered papers with full metadata.
Write to research/snowball_backward.md.
Create source extracts in research/sources/ for each new paper found.
RESEARCH LOG: Log every API call to research/log.md.
```

### Forward Snowballing Agent (model: claude-sonnet-4-6[1m])

```
You are a citation analyst performing forward snowballing.
TOPIC: [TOPIC]
SEED PAPERS: [list of seed BibTeX keys with titles — focus on seminal/older papers]

For each seed paper:
1. Fetch papers that cite it using Semantic Scholar API:
   https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=citations.title,citations.authors,citations.year,citations.externalIds,citations.citationCount
2. From the citing papers, identify those that are:
   - Relevant to [TOPIC]
   - NOT already in references.bib
   - Recent (2023-2026) — forward snowballing is most valuable for finding recent work
3. Prioritize papers with high citation counts (emerging influential work)

Output: A deduplicated list of discovered papers with full metadata.
Write to research/snowball_forward.md.
Create source extracts in research/sources/ for each new paper found.
RESEARCH LOG: Log every API call to research/log.md.
```

### Integration with Pipeline

Both agents run in parallel. After they complete:
1. A bibliography builder agent (model: haiku) adds verified new papers to `references.bib`
2. Update `research/source_coverage.md` counts
3. Log snowballing stats in `.paper-state.json`:
   ```json
   "snowballing": {
     "done": true,
     "seeds": 10,
     "backward_found": N,
     "forward_found": N,
     "added_to_bib": N
   }
   ```

### Rate Limiting

Semantic Scholar API allows 100 requests/5 minutes without a key. With 10 seeds × 2 directions = 20 requests, this is well within limits. For deep mode (20 seeds), may need brief pauses. Add a note in the agent prompt to handle 429 responses with a 5-second backoff.

### Depth Mode Differences

| Setting | Standard | Deep |
|-|-|-|
| Seed papers | 10 | 20 |
| Max new papers per direction | 15 | 30 |
| Citation depth | 1 level | 1 level (2 levels would explode) |
| Forward snowball time window | 2023-2026 | 2020-2026 |

## Files to Modify

1. `template/claude/pipeline/stage-1b-snowballing.md` — Modify the existing Stage 1b file with backward/forward snowballing agents
2. `template/claude/commands/write-paper.md` — Update orchestrator stage table if adding new sub-stages
3. `template/claude/CLAUDE.md` — Mention snowballing in pipeline overview

## Files to Create

None — Stage 1b already has its own pipeline file.

## Risks

- Semantic Scholar API may not have all papers (coverage ~200M but not universal). Mitigation: fall back to OpenAlex API for papers not found.
- Forward snowballing on very old seminal papers may return thousands of citations. Mitigation: cap at top 50 by citation count, filter by recency.
- Duplicate detection by title similarity is imperfect. Mitigation: also compare DOIs and author last names.

## Acceptance Criteria

- [ ] Stage 1b exists in `pipeline/stage-1b-snowballing.md` with backward and forward snowballing agents
- [ ] Agents use Semantic Scholar API with proper error handling
- [ ] New papers are verified and added to references.bib
- [ ] Source extracts created for all discovered papers
- [ ] Pipeline state tracks snowballing completion
- [ ] Standard mode: ~10-15 new papers discovered. Deep mode: ~20-30.
- [ ] Research log captures all API calls
