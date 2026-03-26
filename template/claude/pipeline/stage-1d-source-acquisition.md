# Stage 1d: Source Coverage Audit & Acquisition

> **Prerequisites**: Read `pipeline/shared-protocols.md` first.

---

**Goal**: Ensure every cited source has a verifiable content snapshot, and obtain full text for critical papers.

This stage audits what the research agents actually accessed vs. what they cited. Papers where the pipeline only saw an abstract are flagged — the user can provide full-text PDFs before the writing stages begin.

**This stage has three phases: audit, resolve, acquire.**

#### Phase 1: Audit

1. **Read `references.bib`** — extract every BibTeX key
2. **Scan `research/sources/`** — check which keys have source extract files
3. **For each reference, classify access level**:
   - If `research/sources/<key>.md` exists AND has `Access Level: FULL-TEXT` → **FULL-TEXT**
   - If a PDF matching this paper exists in `attachments/` → **FULL-TEXT** (but may need ingesting — see Phase 3)
   - If `research/sources/<key>.md` exists with `Access Level: ABSTRACT-ONLY` → **ABSTRACT-ONLY**
   - If no source file exists → **METADATA-ONLY**
4. **Write audit summary** to `research/source_coverage.md`:
   ```markdown
   # Source Coverage Audit
   Generated: [timestamp]

   ## Summary
   - Total references: N
   - Full-text accessed: N (X%)
   - Abstract-only: N (Y%)
   - Metadata-only: N (Z%)

   ## Full-Text Sources
   | Key | Title | Access Method |
   |-|-|-|
   | smith2024 | "Title..." | arXiv full text |

   ## Abstract-Only Sources (need upgrade)
   | Key | Title | DOI | Why It Matters |
   |-|-|-|-|
   | davis1997 | "Toward a Stewardship..." | 10.5465/... | Foundational theory — cited 5 times in paper |

   ## Metadata-Only Sources (need investigation)
   | Key | Title | Notes |
   |-|-|-|
   | jones2023 | "Title..." | Only found as citation in another paper |
   ```

#### Phase 2: Automated OA Resolution

For each ABSTRACT-ONLY and METADATA-ONLY source, attempt to find a legal open-access copy. Try each API in order — **stop on first successful PDF download** (don't call remaining APIs for that paper). Always collect abstracts from APIs that return them, even if full text isn't found.

**Configuration**: Check `.paper.json` for an `oa_resolution` object to see which APIs are enabled (all default to `true`). Check for `email` field or `UNPAYWALL_EMAIL` env var (needed for Unpaywall). Check for `CORE_API_KEY` env var (needed for CORE). Check for `NCBI_API_KEY` env var (optional, increases PubMed rate limit).

1. **Unpaywall** (skip if no email configured):
   ```
   WebFetch: https://api.unpaywall.org/v2/<doi>?email=<user_email>
   ```
   Check `best_oa_location.url_for_pdf` (prefer) or `best_oa_location.url_for_landing_page`. Unpaywall covers ~30M OA articles and is the most comprehensive single source for legal OA copies. Rate limit: 100K/day (no concern).

2. **OpenAlex** (no key needed):
   ```
   WebFetch: https://api.openalex.org/works/doi:<doi>?select=id,open_access,best_oa_url,abstract_inverted_index&mailto=<user_email>
   ```
   Check `open_access.oa_url` for PDF. Also extract `abstract_inverted_index` — OpenAlex stores abstracts in inverted index format; reconstruct by sorting tokens by position values. Save the abstract to the source extract even if no PDF is found. Adding `mailto` raises rate limit from 10/s to 100/s.

3. **Semantic Scholar** (existing):
   ```
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=openAccessPdf,title,abstract
   ```
   Check `openAccessPdf.url`. Also save `abstract` to the source extract if available. Rate limit: 100/5min (already handled).

4. **CORE** (skip if `CORE_API_KEY` env var not set):
   ```
   WebFetch: https://api.core.ac.uk/v3/search/works?q=title:"<exact title>"&limit=3
   Header: Authorization: Bearer <CORE_API_KEY>
   ```
   Check `downloadUrl` field in results. CORE covers 200M+ works from institutional repositories. Rate limit: 10/s with key — add 100ms delay between requests.

5. **PubMed Central** (only if detected domain is Biomedical/Clinical — check `.paper.json` topic keywords; or if `oa_resolution.pubmed_central` is explicitly `true`):
   ```
   WebFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=<title>&retmode=json
   ```
   If PMC ID found, full XML is at:
   ```
   WebFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<pmcid>&rettype=xml
   ```
   Extract text content from the XML. Rate limit: 3/s without key, 10/s with `NCBI_API_KEY` — add 350ms delay between requests.

6. **Web search for PDF** (existing):
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<exact paper title>\" <first author last name> filetype:pdf",
     limit: 5
   })
   ```
   If results include a direct PDF URL (ending in `.pdf` or from known preprint servers like arxiv.org, biorxiv.org, ssrn.com, repec.org), attempt to fetch and snapshot the content.

7. **Academic repository search** (existing):
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<exact paper title>\" site:researchgate.net OR site:academia.edu OR site:ssrn.com",
     limit: 3
   })
   ```
   If found on these sites, note the URL — it may require a free account to download, which goes on the user's acquisition list.

**Abstract extraction fallback**: Even when no full text is found, several APIs above return abstracts (OpenAlex, Semantic Scholar, PubMed). If a paper remains ABSTRACT-ONLY after all resolution steps, ensure the source extract has the actual abstract text from whichever API returned it. This improves evidence quality even without full text.

8. **For each successfully resolved paper** (steps 1-6 that return a PDF URL):
   - **Download the PDF** to `attachments/` so there is a persistent local copy:
     ```bash
     curl -L -o "attachments/<bibtexkey>.pdf" "<pdf_url>"
     ```
     Verify the download succeeded: file exists, > 10KB, and starts with `%PDF` magic bytes. If the URL returns HTML instead of a PDF (common with login walls), treat it as a failed download and move to step 9.
   - **Read the downloaded PDF** using the Read tool (pages 1-5 + last 3-5 pages) to extract actual paper content
   - Update or create `research/sources/<key>.md` with Access Level: FULL-TEXT, Accessed Via: "Downloaded PDF from <url>", and a content snapshot from the PDF
   - Log the resolution in `research/log.md` including the download path and which API resolved it

9. **For each paper where a URL was found but content couldn't be fetched** (login wall, expired link, CAPTCHA, HTML instead of PDF):
   - Note the URL in the acquisition list with a hint: "Found on Academia.edu — free account required"
   - Do NOT mark the source as FULL-TEXT — it remains ABSTRACT-ONLY until the PDF is actually read

#### Phase 3: Human Acquisition (MANDATORY pause)

After automated resolution, re-count access levels. **This pause is MANDATORY if any sources remain ABSTRACT-ONLY or METADATA-ONLY.** Do NOT skip it, do NOT proceed to Stage 2 without it. The user must explicitly say "skip" or "continue" before the pipeline advances.

1. **Prioritize the acquisition list** — If `research/claims_matrix.md` exists and has evidence density scores, sort by evidence impact: papers that support WEAK or CRITICAL claims get highest priority (upgrading a source from ABSTRACT-ONLY to FULL-TEXT has the most impact on under-supported claims). Otherwise (first pipeline run, no matrix yet), fall back to citation frequency in the research files. In standard mode, present only the **top 5** papers. In deep mode, present ALL abstract-only and metadata-only papers.
2. **Use AskUserQuestion** to present the list and pause. This is a BLOCKING call — the pipeline STOPS here until the user responds:

```
I've completed the literature research and found [N] references. Here's the source coverage:

✓ [X] papers with full text accessed
⚠ [Y] papers where I only read the abstract
✗ [Z] papers where I only have metadata

The following papers would strengthen the manuscript if I had full text.
They're sorted by importance (citation frequency in the paper):

1. **[key]** — "[Title]" ([Year])
   DOI: [doi] | Cited [N] times in draft
   💡 Suggested: Search "[title]" filetype:pdf on Bing
   🔗 Found on Academia.edu: [url] (free account needed)

2. **[key]** — "[Title]" ([Year])
   DOI: [doi] | Cited [N] times in draft
   💡 Suggested: Check your university library access

[... more papers ...]

Drop any PDFs you find into the `attachments/` folder and say "continue" when ready.
Or say "skip" to proceed with abstract-level sources (I'll flag thin evidence in the paper).
```

3. **When the user responds**:
   - If "continue" or similar: scan `attachments/` for new PDFs, run the ingestion logic (same as `/ingest-papers`), update source extracts to FULL-TEXT with content snapshots
   - If "skip" or similar: proceed, but mark all abstract-only sources with a warning flag in the claims-evidence matrix

4. **If ALL sources already have full text** after Phase 2 (every single reference in `references.bib` has a corresponding `research/sources/<key>.md` with `Access Level: FULL-TEXT`), skip the pause. But this should be RARE — verify the count before skipping. If even ONE source is ABSTRACT-ONLY or METADATA-ONLY, you MUST pause.

#### Phase 4: Update Coverage Report

After acquisition is complete (or skipped), update `research/source_coverage.md` with final counts and a resolution sources table showing which API resolved each paper. This file persists as a permanent record of what the pipeline had access to.

Include a **Resolution Sources** section in the coverage report:
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

**Checkpoint**: Verify `research/source_coverage.md` exists. Update `.paper-state.json`:
```json
"source_acquisition": {
  "done": true,
  "completed_at": "...",
  "full_text": N,
  "abstract_only": N,
  "metadata_only": N,
  "user_provided": N,
  "auto_resolved": N
}
```

Update `.paper-progress.txt`: "Stage 1d complete: [N] full-text, [M] abstract-only sources"

#### Knowledge Graph Build

After source acquisition is complete, build the knowledge graph from all source extracts:

```bash
python scripts/knowledge.py build
```

This creates a queryable knowledge graph in `research/knowledge/` from all files in `research/sources/`. The graph extracts entities (papers, theories, methods, findings, authors) and relationships (cites, contradicts, supports, extends) that agents can query during writing.

**If `scripts/knowledge.py` does not exist or `OPENROUTER_API_KEY` is not set**, skip this step silently — the knowledge graph is optional. The pipeline works without it; agents fall back to reading research/ files directly.

Update `.paper-state.json`: add `"knowledge_graph": { "done": true, "entities": N, "relationships": N }` to the stages object.

#### Evidence Score Recomputation

If `research/claims_matrix.md` exists (e.g., re-running Stage 1d on a paper that already has a claims matrix), recompute evidence density scores now. Source access levels may have changed (ABSTRACT-ONLY → FULL-TEXT), which affects claim scores. Use the scoring model from Stage 2 step 5 to update the Score and Strength columns. This ensures the acquisition list in Phase 3 reflects the latest evidence state.
