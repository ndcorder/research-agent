# Audit Sources — Verify Access Level and Snapshot Every Cited Source

Audit every reference in `references.bib` to determine what the pipeline actually accessed, attempt to find open-access full text, and generate a coverage report.

This is the standalone version of Stage 1d from `/write-paper`. Use it on existing papers to retroactively audit and upgrade source coverage.

## Instructions

### Phase 1: Audit Current Coverage

1. **Read `references.bib`** — extract every BibTeX key, title, authors, year, DOI
2. **Scan `research/sources/`** — check which keys have source extract files
3. **For each reference, determine access level**:
   - Has source file with `Access Level: FULL-TEXT` → ✓ full-text
   - Has PDF in `attachments/` matching this paper → ✓ full-text (run `/ingest-papers` if no source file)
   - Has source file with `Access Level: ABSTRACT-ONLY` → ⚠ abstract-only
   - Has source file with `Access Level: METADATA-ONLY` → ✗ metadata-only
   - No source file at all → ✗ unknown (treat as metadata-only)
4. **For references with no source file**, create a minimal one:
   - Read `research/survey.md`, `research/methods.md`, `research/empirical.md`, `research/theory.md`, `research/gaps.md` (and any other research files)
   - Search for mentions of the paper's title or BibTeX key
   - Extract whatever context exists about this paper from the research files
   - Create `research/sources/<key>.md` using the format from `/write-paper` Stage 1 SOURCE EXTRACTS instructions (Access Level, Content Snapshot, Key Findings Used, Provenance sections), with whatever content is available as the snapshot

### Phase 2: Automated OA Resolution

For each ABSTRACT-ONLY and METADATA-ONLY source, attempt to find a free full-text copy:

1. **If DOI present**, check Semantic Scholar for `openAccessPdf`:
   ```
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=openAccessPdf,title,abstract
   ```
   If `openAccessPdf.url` exists, fetch and snapshot the content.

2. **Web search for PDF**:
   ```
   Use Firecrawl search: "<exact title>" <first author> filetype:pdf
   ```
   Check results for direct PDF links (arxiv.org, biorxiv.org, ssrn.com, .pdf URLs).
   If found, fetch with WebFetch and update the source extract.

3. **Academic repository search**:
   ```
   Use Firecrawl search: "<exact title>" site:researchgate.net OR site:academia.edu OR site:ssrn.com
   ```
   Note any URLs found — even if behind a login wall, record them for the user.

4. **Log every resolution attempt** in `research/log.md`:
   ```markdown
   ### [TIMESTAMP] — Source Audit OA Resolution
   - **Paper**: [key] — "[title]"
   - **Tool**: [tool used]
   - **Query**: [query]
   - **Result**: [RESOLVED: found PDF at URL / NOT FOUND / FOUND BUT INACCESSIBLE: URL behind login]
   ```

### Phase 3: Report

Write `research/source_coverage.md`:

```markdown
# Source Coverage Audit
Generated: [timestamp]

## Summary
- Total references: N
- Full-text accessed: N (X%)
- Abstract-only: N (Y%)
- Metadata-only: N (Z%)
- Upgraded in this audit: N (from abstract→full-text via OA resolution)

## Full-Text Sources
| Key | Title | Access Method |
|-|-|-|
| ... | ... | ... |

## Abstract-Only Sources — Acquisition List
| # | Key | Title | DOI | Citations in Paper | Suggested Action |
|-|-|-|-|-|-|
| 1 | davis1997 | "Toward a Stewardship..." | 10.5465/... | 5 | Found on Academia.edu: [url] |
| 2 | jensen1976 | "Theory of the Firm..." | 10.1016/... | 3 | Try: "Theory of the Firm" filetype:pdf on Bing |

## Metadata-Only Sources
| Key | Title | Notes |
|-|-|-|
| ... | ... | ... |
```

### Phase 4: Offer Acquisition

If there are ABSTRACT-ONLY or METADATA-ONLY papers, present the acquisition list to the user:

"I found [N] papers where I only had the abstract. Drop any PDFs you find into `attachments/` and run `/ingest-papers` to upgrade them to full-text with snapshots."

### Phase 5: Update Claims-Evidence Matrix (if it exists)

If `research/claims_matrix.md` exists, add or update a `Source Access` column:
- For each claim, check which sources support it
- Mark whether each supporting source is `full-text` or `abstract-only`
- Flag any claims supported ONLY by abstract-only sources with ⚠

## Arguments

$ARGUMENTS

If no arguments given, audit ALL references in `references.bib`.
If a BibTeX key is given, audit only that reference.
