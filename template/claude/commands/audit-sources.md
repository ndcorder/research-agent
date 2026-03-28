# Audit Sources — Verify Access Level and Snapshot Every Cited Source

Audit every reference in `references.bib` to determine what the pipeline actually accessed, attempt to find open-access full text, and generate a coverage report.

This is the standalone version of Stage 1d from `/write-paper`. Use it on existing papers to retroactively audit and upgrade source coverage.

## Instructions

**Read `pipeline/stage-1d-source-acquisition.md` now.** This command executes the same phases defined there. The stage file is the authoritative reference for all resolver details, API calls, rate limits, and validation protocols. Do not duplicate that logic here — read it fresh each time.

### Execute Stage 1d Phases

Run the following phases from `stage-1d-source-acquisition.md`:

1. **Phase 1: Audit** — Classify every reference by access level (FULL-TEXT / ABSTRACT-ONLY / METADATA-ONLY)

2. **Phase 1b: Source Type Detection** — Classify each reference by source type (journal_article, book, conference_paper, etc.) from BibTeX entry types

3. **Phase 2: Modular Resolver Cascade** — Run the full resolver cascade (Unpaywall, OpenAlex, Semantic Scholar, CrossRef, CORE, PubMed, arXiv, DBLP, BASE, Internet Archive, DOAB, Google Books, web search, repository search) with PDF validation on every download

4. **Phase 2b: Content Enrichment** — For remaining METADATA-ONLY and thin ABSTRACT-ONLY sources, gather secondary content (Wikipedia, book reviews, executive summaries, citation context, publisher descriptions)

5. **Phase 3: Human Acquisition** — Present prioritized list of remaining gaps to the user. Include which resolvers were attempted and suggestions for where to find the source.

6. **Phase 4: Update Coverage Report** — Write `research/source_coverage.md` with final counts, resolution sources table, and PDF validation summary.

### Additional Steps (standalone-only)

These steps are specific to `/audit-sources` and not part of the `/write-paper` pipeline:

**For references with no source file at all**, create a minimal one before running resolvers:
- Read `research/survey.md`, `research/methods.md`, `research/empirical.md`, `research/theory.md`, `research/gaps.md` (and any other research files)
- Search for mentions of the paper's title or BibTeX key
- Extract whatever context exists about this paper from the research files
- Create `research/sources/<key>.md` with whatever content is available as the snapshot

**Update Claims-Evidence Matrix** (if `research/claims_matrix.md` exists):
1. **Update source access levels** — for each claim, check which sources support it and update access levels based on the audit results (sources may have been upgraded)
2. **Recompute evidence density scores** — use the scoring model from `/write-paper` Stage 2 step 5:
   - Base score per source: FULL-TEXT primary = 3, FULL-TEXT secondary = 2, ABSTRACT-ONLY = 1, Enriched ABSTRACT-ONLY (secondary sources) = 0.5, METADATA-ONLY = 0
   - Modifiers: highly cited (+0.5), recent 2024-2026 (+0.5), direct relevance (+1), same domain (+0.5)
   - Claim score = sum of all supporting source scores
   - Thresholds: STRONG >= 6, MODERATE 3-5.9, WEAK 1-2.9, CRITICAL < 1
3. **Update Score and Strength columns** in the matrix
4. Flag WEAK claims with ⚠ and CRITICAL claims with ⛔
5. Flag any claims supported ONLY by abstract-only sources with ⚠

**Rebuild Knowledge Graph** (if `scripts/knowledge.py` exists and `OPENROUTER_API_KEY` is set):
```bash
python scripts/knowledge.py build
```
Run with `run_in_background: true`. The graph should be rebuilt after source acquisition to incorporate new content.

**Update Source Manifest**:
```bash
python3 scripts/update-manifest.py
```

## Arguments

$ARGUMENTS

If no arguments given, audit ALL references in `references.bib`.
If a BibTeX key is given, audit only that reference.
