# Plan 03: Enhanced Source Acquisition

## Problem

The current OA resolution chain (Semantic Scholar `openAccessPdf` → web search for PDF → academic repository search) misses many freely available papers. Unpaywall, OpenAlex, CORE, and PubMed Central all have different coverage, and together they catch significantly more OA copies than any single source. The pipeline also relies on the user to find paywalled papers manually, when several of these APIs could resolve them automatically.

## Goal

Expand the automated OA resolution chain in Stage 1d with additional free APIs, reducing the number of papers that require manual user acquisition.

## Design

### Expanded Resolution Chain

Current chain (3 steps):
1. Semantic Scholar `openAccessPdf`
2. Web search for PDF (Firecrawl)
3. Academic repository search (ResearchGate, Academia.edu)

New chain (7 steps, tried in order, stop on first success):

1. **Unpaywall API** (free, email-based auth, ~30M OA articles):
   ```
   WebFetch: https://api.unpaywall.org/v2/DOI?email=<user_email>
   ```
   Check `best_oa_location.url_for_pdf` or `best_oa_location.url_for_landing_page`.
   Unpaywall is the most comprehensive single source for legal OA copies.
   Requires an email address — read from `.paper.json` (new field: `email`) or `UNPAYWALL_EMAIL` env var.

2. **OpenAlex API** (free, no key needed, 250M+ works):
   ```
   WebFetch: https://api.openalex.org/works/doi:<doi>?select=id,open_access,best_oa_url,abstract_inverted_index
   ```
   Check `open_access.oa_url`. Also extract `abstract_inverted_index` (OpenAlex stores abstracts in inverted index format — reconstruct by sorting by position).

3. **Semantic Scholar** (existing step — keep as-is):
   ```
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=openAccessPdf,title,abstract
   ```

4. **CORE API** (free with key, 200M+ from institutional repositories):
   ```
   WebFetch: https://api.core.ac.uk/v3/search/works?q=title:"<exact title>"&limit=3
   ```
   Requires `CORE_API_KEY` env var (free registration). Check `downloadUrl` field.
   Skip if env var not set — CORE is optional.

5. **PubMed Central** (for biomedical papers only — detect from domain):
   ```
   WebFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=<title>&retmode=json
   ```
   If PMC ID found, full XML is available at:
   ```
   WebFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<pmcid>&rettype=xml
   ```
   Only run this step if the detected domain is Biomedical/Clinical.

6. **Web search for PDF** (existing step — keep as-is):
   Firecrawl search with `filetype:pdf`

7. **Academic repository search** (existing step — keep as-is):
   ResearchGate, Academia.edu, SSRN

### PDF Download & Ingestion

For each successfully resolved URL (steps 1-5 that return a PDF URL):
1. Download: `curl -L -o "attachments/<bibtexkey>.pdf" "<url>"`
2. Verify: file exists, > 10KB, is actually a PDF (check magic bytes or MIME)
3. Read pages 1-5 + last 3-5 pages
4. Update source extract to FULL-TEXT with content snapshot

### Abstract Extraction as Fallback

Even when full text isn't available, several APIs return abstracts:
- OpenAlex: `abstract_inverted_index` (needs reconstruction)
- Semantic Scholar: `abstract`
- PubMed: abstract via E-utilities

If a paper remains ABSTRACT-ONLY after all resolution steps, at minimum ensure the source extract has the actual abstract text (not just "abstract was read via Perplexity"). This improves evidence quality even without full text.

### Configuration

Add optional fields to `.paper.json`:
```json
{
  "email": "user@example.com",
  "oa_resolution": {
    "unpaywall": true,
    "openalex": true,
    "semantic_scholar": true,
    "core": true,
    "pubmed_central": "auto",
    "web_search": true,
    "repository_search": true
  }
}
```

All default to `true`. `pubmed_central` defaults to `"auto"` (enabled only for biomedical/clinical domains).

### Rate Limiting

| API | Rate Limit | Mitigation |
|-|-|-|
| Unpaywall | 100K/day | No concern |
| OpenAlex | 10/second unauthenticated, 100/second with `mailto` param | Add `mailto` to URL |
| Semantic Scholar | 100/5min | Already handled |
| CORE | 10/second with key | Add 100ms delay between requests |
| PubMed | 3/second without key, 10/second with `NCBI_API_KEY` | Add 350ms delay |

### Reporting

Update the source coverage report to show which API resolved each paper:
```markdown
## Resolution Sources
| API | Papers Resolved | Papers Attempted |
|-|-|-|
| Unpaywall | 8 | 25 |
| OpenAlex | 3 | 17 |
| Semantic Scholar | 2 | 14 |
| CORE | 1 | 12 |
| PubMed Central | 4 | 4 |
| Web search | 2 | 8 |
| Manual (user) | 3 | 3 |
```

## Files to Modify

1. `template/claude/pipeline/stage-1d-source-acquisition.md` — Phase 2: expand OA resolution chain
2. `template/claude/commands/audit-sources.md` — Phase 2: same expanded chain
3. `template/claude/commands/validate-references.md` — Step 5: same expanded chain for OA during validation
4. `template/claude/CLAUDE.md` — Document new optional config fields

## Files to Create

None.

## Risks

- Multiple API calls per paper × 30-80 papers = 200-500+ API calls. Mitigation: stop on first success (don't call all APIs for every paper), parallelize across papers.
- Some APIs may return stale URLs. Mitigation: always verify the download (check file size, MIME type) before marking as FULL-TEXT.
- Unpaywall requires an email. Mitigation: make it optional, skip if not configured.

## Acceptance Criteria

- [ ] Stage 1d tries Unpaywall, OpenAlex, CORE, and PMC before web search
- [ ] Each API has proper error handling and rate limiting
- [ ] Abstract extraction works as a fallback for all APIs that return abstracts
- [ ] Source coverage report shows resolution source per paper
- [ ] `.paper.json` supports optional email and per-API toggles
- [ ] PMC integration only activates for biomedical/clinical domains
- [ ] Measurably more papers resolve to FULL-TEXT vs current pipeline
