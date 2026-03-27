# Stage 1d: Source Coverage Audit & Acquisition

> **Prerequisites**: Read `pipeline/shared-protocols.md` first.

---

**Goal**: Ensure every cited source has a verifiable content snapshot, and obtain full text for critical papers. Maximize automated coverage before asking the user for help.

This stage audits what the research agents actually accessed vs. what they cited, then runs a modular cascade of resolvers to find full text or at minimum summaries for every source. It has six phases: audit, type detection, resolver cascade, content enrichment, human acquisition, and post-acquisition.

---

## Phase 1: Audit

1. **Read `references.bib`** — extract every BibTeX key
2. **Scan `research/sources/`** — check which keys have source extract files
3. **For each reference, classify access level**:
   - If `research/sources/<key>.md` exists AND has `Access Level: FULL-TEXT` → **FULL-TEXT**
   - If a PDF matching this paper exists in `attachments/` → **FULL-TEXT** (but may need ingesting — see Phase 5)
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
   | Key | Title | Source Type | Notes |
   |-|-|-|-|
   | jones2023 | "Title..." | article | Only found as citation in another paper |
   ```

---

## Phase 1b: Source Type Detection

Before running resolvers, classify each reference by source type. This determines which resolvers apply and what acquisition strategy to use.

**Detection rules** (check BibTeX entry type first, then heuristics):

| BibTeX Type | Source Type | Heuristics |
|-|-|-|
| `@article` | `journal_article` | — |
| `@book` | `book` | — |
| `@inbook`, `@incollection` | `book_chapter` | Look up parent book |
| `@techreport` | `technical_report` | — |
| `@misc` with organizational author | `industry_report` | Author is org (ISC2, Verizon, ISACA, Gartner, etc.) |
| `@misc` with person author | `grey_literature` | Check if it has a URL field |
| `@inproceedings`, `@conference` | `conference_paper` | — |
| `@phdthesis`, `@mastersthesis` | `thesis` | — |
| `@online`, `@electronic` | `web_resource` | — |
| Anything else | `unknown` | Treat as journal article |

Add a `Source Type:` field to each source extract file in `research/sources/`. This persists across pipeline reruns and informs resolver routing.

---

## Phase 2: Modular Resolver Cascade

For each ABSTRACT-ONLY and METADATA-ONLY source, run applicable resolvers to find full-text PDFs and/or abstracts. Resolvers are organized into tiers.

**Configuration**: Check `.paper.json` for an `oa_resolution` object. All resolvers default to `true` (or `"auto"` where noted). Check for required env vars / config before each resolver — skip silently if prerequisites aren't met.

**Stop-on-first-PDF rule**: For journal articles and conference papers, stop the Tier 1 cascade after the first successful PDF download. For books, run ALL book-specific resolvers (each may have different chapters/previews). Always run CrossRef regardless of PDF success (it provides abstracts).

### How to add a new resolver

Copy any resolver block below and fill in the fields. The format is intentionally consistent so new data sources can be added without restructuring. Each resolver is independent — removing one does not affect others.

---

### Resolver 1: Unpaywall (`unpaywall`)

**Applies to**: journal_article, conference_paper
**Requires**: Email in `.paper.json` `email` field or `UNPAYWALL_EMAIL` env var
**Default**: enabled (skip if no email configured)
**Extracts**: PDF URL
**Rate limit**: 100K/day (no concern)

**API call**:
```
WebFetch: https://api.unpaywall.org/v2/<doi>?email=<user_email>
```

**What to check**: `best_oa_location.url_for_pdf` (prefer) or `best_oa_location.url_for_landing_page`
**On success**: Download PDF → validate → ingest
**On failure**: Continue to next resolver

---

### Resolver 2: OpenAlex (`openalex`)

**Applies to**: all
**Requires**: nothing (email optional, increases rate limit)
**Default**: enabled
**Extracts**: PDF URL, abstract
**Rate limit**: 10/s without email, 100/s with `mailto` param

**API call**:
```
WebFetch: https://api.openalex.org/works/doi:<doi>?select=id,open_access,best_oa_url,abstract_inverted_index&mailto=<user_email>
```

If no DOI, search by title:
```
WebFetch: https://api.openalex.org/works?filter=title.search:<url_encoded_title>&select=id,open_access,best_oa_url,abstract_inverted_index&mailto=<user_email>
```

**What to check**: `open_access.oa_url` for PDF. Also extract `abstract_inverted_index` — OpenAlex stores abstracts in inverted index format; reconstruct by sorting tokens by position values.
**On success**: Download PDF if URL found → validate → ingest. Always save abstract to source extract even if no PDF.
**On failure**: Continue to next resolver

---

### Resolver 3: Semantic Scholar (`semantic_scholar`)

**Applies to**: journal_article, conference_paper, thesis
**Requires**: nothing
**Default**: enabled
**Extracts**: PDF URL, abstract
**Rate limit**: 100 requests per 5 minutes — add 3s delay between requests

**API call**:
```
WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=openAccessPdf,title,abstract,tldr
```

If no DOI, search by title:
```
WebFetch: https://api.semanticscholar.org/graph/v1/paper/search?query=<url_encoded_title>&limit=3&fields=openAccessPdf,title,abstract,tldr
```

**What to check**: `openAccessPdf.url` for PDF. Save `abstract` and `tldr.text` (machine-generated summary) to source extract.
**On success**: Download PDF → validate → ingest. Always save abstract/TLDR.
**On failure**: Continue to next resolver

---

### Resolver 4: CrossRef (`crossref`)

**Applies to**: all
**Requires**: nothing (email optional for polite pool)
**Default**: enabled
**Extracts**: abstract, reference list, metadata
**Rate limit**: 50/s (polite pool with email: higher)
**Special**: Always runs even if PDF already found — provides abstracts and metadata that enrich source extracts

**API call**:
```
WebFetch: https://api.crossref.org/works/<doi>
```

If no DOI, search by title:
```
WebFetch: https://api.crossref.org/works?query.bibliographic=<url_encoded_title>&rows=3
```

Add header: `User-Agent: ResearchAgent/1.0 (mailto:<user_email>)` if email available.

**What to check**: `message.abstract` (often HTML — strip tags). Also `message.link` for full-text links (check `content-type: application/pdf`). `message.reference` contains the paper's own reference list (useful for snowballing).
**On success**: Save abstract to source extract. If a PDF link with `application/pdf` content-type is found, download → validate → ingest.
**On failure**: Continue to next resolver

---

### Resolver 5: CORE (`core`)

**Applies to**: all
**Requires**: `CORE_API_KEY` env var (free registration at core.ac.uk)
**Default**: enabled (skip if no API key)
**Extracts**: PDF URL, abstract, full text
**Rate limit**: 10/s with key — add 100ms delay between requests

**API call**:
```
WebFetch: https://api.core.ac.uk/v3/search/works?q=title:"<exact title>"&limit=3
Header: Authorization: Bearer <CORE_API_KEY>
```

**What to check**: `downloadUrl` for PDF. `abstract` for abstract text. Some results include `fullText` directly.
**On success**: Download PDF → validate → ingest. Save abstract/fullText.
**On failure**: Continue to next resolver

---

### Resolver 6: PubMed Central (`pubmed_central`)

**Applies to**: journal_article (biomedical/clinical domain only)
**Requires**: nothing (`NCBI_API_KEY` optional, increases rate limit)
**Default**: `"auto"` — enabled only for biomedical/clinical domains (check `.paper.json` topic keywords)
**Extracts**: full text (XML), abstract
**Rate limit**: 3/s without key, 10/s with `NCBI_API_KEY` — add 350ms delay

**API call**:
```
WebFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=<title>&retmode=json
```

If PMC ID found:
```
WebFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<pmcid>&rettype=xml
```

**What to check**: Extract text content from the XML body. Also check for PDF link.
**On success**: Create source extract with full text from XML. Mark as FULL-TEXT.
**On failure**: Continue to next resolver

---

### Resolver 7: arXiv API (`arxiv`)

**Applies to**: journal_article, conference_paper (CS, physics, math, stats, econ, q-bio, q-fin domains)
**Requires**: nothing
**Default**: `"auto"` — enabled for applicable domains based on `.paper.json` topic keywords
**Extracts**: PDF URL, abstract
**Rate limit**: 1 request per 3 seconds

**API call**:
```
WebFetch: https://export.arxiv.org/api/query?search_query=ti:"<exact title>"&max_results=3
```

The response is Atom XML. Parse `<entry>` elements.

**What to check**: Match title against `<title>`. PDF link is at `<link title="pdf" href="..."/>`. Abstract is in `<summary>`.
**On success**: Download PDF → validate → ingest. Save abstract.
**On failure**: Continue to next resolver

---

### Resolver 8: DBLP (`dblp`)

**Applies to**: conference_paper, journal_article (CS/IT domain)
**Requires**: nothing
**Default**: `"auto"` — enabled for CS/IT domains
**Extracts**: links to OA copies, metadata
**Rate limit**: respectful use (no published limit, add 1s delay)

**API call**:
```
WebFetch: https://dblp.org/search/publ/api?q=<url_encoded_title>&format=json&h=3
```

**What to check**: `result.hits.hit[].info.ee` — this is the electronic edition URL (often DOI or direct PDF link). Also check `info.url` for the DBLP page which sometimes links to OA copies.
**On success**: If URL ends in `.pdf` or points to known OA host (arxiv, acm OA, ieee OA), download → validate → ingest.
**On failure**: Continue to next resolver

---

### Resolver 9: BASE — Bielefeld Academic Search Engine (`base`)

**Applies to**: all
**Requires**: nothing
**Default**: enabled
**Extracts**: PDF URL, abstract
**Rate limit**: respectful use — add 1s delay between requests

**API call**:
```
WebFetch: https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi?func=PerformSearch&query=tit:<url_encoded_title>&format=json&hits=3
```

**What to check**: Results contain `dclink` (full text URL), `dcdescription` (abstract), `dcidentifier` (DOI/URL). Check if `dclink` points to a PDF.
**On success**: Download PDF → validate → ingest. Save abstract from `dcdescription`.
**On failure**: Continue to next resolver

---

### Resolver 10: Internet Archive / Open Library (`internet_archive`)

**Applies to**: book, book_chapter, thesis
**Requires**: nothing
**Default**: enabled
**Extracts**: full text (for digitized books), table of contents, previews
**Rate limit**: respectful use — add 1s delay

**API call** (Open Library search):
```
WebFetch: https://openlibrary.org/search.json?title=<url_encoded_title>&author=<url_encoded_author>&limit=3
```

If found, check for readable version:
```
WebFetch: https://openlibrary.org/works/<work_id>.json
```

**What to check**: `availability.status` — if `"borrowable"` or `"open"`, the book can be read. Check `ia` field for Internet Archive identifier. Full text may be at `https://archive.org/stream/<ia_id>`.
**On success**: If full text accessible, extract key chapters (intro, conclusion, key theoretical chapters) using the Read tool. Create source extract with chapter summaries. Mark as FULL-TEXT.
**On failure**: Even if not borrowable, Open Library often has: table of contents, first page preview, edition data, subject tags. Save whatever is available to enrich the source extract.

---

### Resolver 11: DOAB — Directory of Open Access Books (`doab`)

**Applies to**: book, book_chapter
**Requires**: nothing
**Default**: enabled
**Extracts**: PDF URL, metadata
**Rate limit**: respectful use — add 1s delay

**API call**:
```
WebFetch: https://directory.doabooks.org/rest/search?query=<url_encoded_title>&expand=metadata,bitstreams
```

**What to check**: `bitstreams` array for PDF download links. `metadata` for abstract/description.
**On success**: Download PDF → validate → ingest.
**On failure**: Continue to next resolver

---

### Resolver 12: Google Books (`google_books`)

**Applies to**: book, book_chapter
**Requires**: nothing (`GOOGLE_BOOKS_API_KEY` optional, increases quota)
**Default**: enabled
**Extracts**: preview pages, description, table of contents
**Rate limit**: 1000/day without key, higher with key

**API call**:
```
WebFetch: https://www.googleapis.com/books/v1/volumes?q=intitle:<url_encoded_title>+inauthor:<author_surname>&maxResults=3
```

**What to check**: `items[].volumeInfo.description` (publisher description/abstract), `items[].volumeInfo.previewLink` (Google Books preview), `items[].accessInfo.pdf.isAvailable` (PDF download), `items[].volumeInfo.tableOfContents`.
**On success**: If PDF available, download → validate → ingest. Otherwise, save description and scrape key preview pages (introduction, first chapter, conclusion) using Firecrawl. Mark as ABSTRACT-ONLY with enriched content.
**On failure**: Continue to next resolver

---

### Resolver 13: Web Search for PDF (`web_search`)

**Applies to**: all
**Requires**: nothing
**Default**: enabled
**Extracts**: PDF URL
**Rate limit**: N/A

**Search query** (adapt based on source type):
```
mcp__firecrawl__firecrawl_search({
  query: "\"<exact paper title>\" <first author last name> filetype:pdf",
  limit: 5
})
```

For books, also try:
```
"<exact book title>" <author> "full text" OR "free download" OR "open access" filetype:pdf
```

**What to check**: Results include a direct PDF URL (ending in `.pdf` or from known preprint servers: arxiv.org, biorxiv.org, ssrn.com, repec.org, hal.science, zenodo.org). Do NOT download PDFs from unknown/suspicious domains.
**On success**: Download PDF → validate → ingest
**On failure**: Continue to next resolver

---

### Resolver 14: Academic Repository Search (`repository_search`)

**Applies to**: all
**Requires**: nothing
**Default**: enabled
**Extracts**: landing page URLs (may require free account)
**Rate limit**: N/A

**Search query**:
```
mcp__firecrawl__firecrawl_search({
  query: "\"<exact paper title>\" site:researchgate.net OR site:academia.edu OR site:ssrn.com OR site:zenodo.org OR site:hal.science",
  limit: 3
})
```

**What to check**: If found on these sites, note the URL. Some have direct PDF downloads; others require a free account.
**On success**: If direct PDF available, download → validate → ingest. Otherwise, add URL to human acquisition list with hint: "Found on [site] — free account may be needed"
**On failure**: End of Tier 1 cascade

---

### PDF Validation Protocol

**Every PDF download** (from any resolver) must pass this validation before the source is marked FULL-TEXT. This prevents ingesting login pages, corrupted files, or wrong papers.

1. **File integrity check**:
   - File exists at `attachments/<bibtexkey>.pdf`
   - File size > 10KB (smaller files are likely error pages)
   - First 5 bytes contain `%PDF-` magic bytes: `head -c 5 attachments/<key>.pdf`
   - If any check fails → **INVALID** — delete the file, log "download returned non-PDF (likely login wall or redirect)", continue searching

2. **Content extraction**:
   - Read the downloaded PDF using the Read tool (pages 1-2) to extract text from the first two pages

3. **Identity verification** (fuzzy matching — account for OCR errors, formatting differences):
   - **Title check**: Does the paper title (or a significant substring, 5+ consecutive words) appear in the first 2 pages? Normalize case and whitespace before matching.
   - **Author check**: Does at least one author surname appear in the first 2 pages?

4. **Verdict**:
   - Title + author match → **VALID** — proceed with ingestion, update source extract to `Access Level: FULL-TEXT`
   - Title match, no author → **LIKELY VALID** — proceed but log warning: "Author name not found in PDF — verify manually"
   - No title match but author match → **UNCERTAIN** — log warning, keep PDF, flag for human review in Phase 3 list
   - Neither title nor author match → **MISMATCH** — delete the PDF, log "downloaded PDF does not match expected paper: [expected title] vs [found text]", continue searching
   - No extractable text (scanned/image PDF) → **UNVERIFIABLE** — keep the PDF, log warning, proceed with ingestion but flag as "unverified — scanned PDF, may need OCR check"

5. **Log every download attempt** (success or failure) to `research/log.md`:
   ```markdown
   ### [timestamp] — PDF Download
   - **Key**: <bibtexkey>
   - **Source**: <resolver name>
   - **URL**: <download URL>
   - **Validation**: VALID / LIKELY VALID / MISMATCH / INVALID
   - **Details**: <any warnings or mismatch details>
   ```

---

### Abstract Extraction Fallback

Even when no full text is found, several resolvers above return abstracts (OpenAlex, Semantic Scholar, CrossRef, arXiv, CORE, BASE). If a paper remains ABSTRACT-ONLY after all Tier 1 resolvers, ensure the source extract has the actual abstract text from whichever API returned it. Prefer the longest/most detailed abstract if multiple APIs returned one.

---

### Download and Ingestion Protocol

For each successfully resolved paper (any resolver that returns a PDF URL):

1. **Download the PDF** to `attachments/`:
   ```bash
   curl -L -o "attachments/<bibtexkey>.pdf" "<pdf_url>"
   ```

2. **Run PDF Validation Protocol** (above). If validation fails, skip to next resolver or end cascade.

3. **Read the validated PDF** using the Read tool (pages 1-5 + last 3-5 pages) to extract actual paper content.

4. **Update or create `research/sources/<key>.md`** with:
   - `Access Level: FULL-TEXT`
   - `Accessed Via: Downloaded PDF from <url> (resolved by <resolver name>)`
   - Content snapshot from the PDF
   - Source Type (from Phase 1b)

5. **Log the resolution** in `research/log.md` including the download path and which resolver found it.

---

## Phase 2b: Content Enrichment

**Purpose**: For every source still METADATA-ONLY (and thin ABSTRACT-ONLY sources with < 100 words of content) after the resolver cascade, attempt to gather descriptive content through secondary sources. The goal is upgrading to ABSTRACT-ONLY minimum so the evidence system has something to score above zero.

**This phase runs for ALL remaining thin sources**, not just those cited in claims — the knowledge graph benefits from breadth.

**Configuration**: Check `.paper.json` `oa_resolution.content_enrichment` — defaults to `true`.

### Enrichment Strategies by Source Type

**Books** (`book`, `book_chapter`):
1. **Wikipedia/encyclopedia search**: Search for the book title and key concepts
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<book title>\" <author> wikipedia OR encyclopedia summary theory",
     limit: 5
   })
   ```
   Scrape the most relevant result for a 200-500 word summary of the book's central thesis, key arguments, and academic impact.

2. **Academic book review search**: Search for published reviews of the book
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<book title>\" <author> book review journal",
     limit: 3
   })
   ```
   Book reviews in academic journals often summarize the book's argument in 1000-2000 words — excellent proxy content.

3. **Publisher page**: Search for the publisher's description
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<book title>\" <author> site:<publisher_domain>",
     limit: 2
   })
   ```
   Publisher pages typically include a detailed abstract, table of contents, and endorsement quotes that capture the book's scope.

**Industry Reports** (`industry_report`, `technical_report`):
1. **Executive summary / key findings**: Many reports publish free summaries
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<report title>\" <org> executive summary OR key findings OR highlights <year>",
     limit: 5
   })
   ```

2. **Press releases**: Organizations announce report findings
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<report title>\" <org> press release OR announcement <year>",
     limit: 3
   })
   ```

3. **Blog posts / news coverage**: Tech media often covers major industry reports in detail
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<report title>\" <org> analysis OR summary OR findings <year>",
     limit: 3
   })
   ```

**Conference Papers** (`conference_paper`):
1. **Slides / presentations**: Authors often share slides
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<paper title>\" <author> slides OR presentation filetype:pdf",
     limit: 3
   })
   ```

2. **Video abstracts / talks**: Conference recordings
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<paper title>\" <author> talk OR video OR recording <conference>",
     limit: 3
   })
   ```

3. **Extended abstracts**: Some conferences publish these freely
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<paper title>\" extended abstract <conference> <year>",
     limit: 3
   })
   ```

**Theses** (`thesis`):
1. **Institutional repository search**: Most universities publish theses openly
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<thesis title>\" <author> thesis repository OR institutional OR etd",
     limit: 5
   })
   ```

2. **ProQuest / dissertation databases**: Search for the thesis abstract
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<thesis title>\" <author> proquest OR dissertation abstract",
     limit: 3
   })
   ```

**Grey Literature** (`grey_literature`):
1. **Direct URL check**: If the BibTeX entry has a `url` field, fetch it directly with Firecrawl
2. **Web search**: Search for the title — grey literature often lives on organizational websites, working paper series, or preprint servers
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<title>\" <author> working paper OR technical note OR white paper",
     limit: 5
   })
   ```

**Journal Articles** (`journal_article`) — fallback when Tier 1 resolvers found nothing:
1. **Author's personal/institutional page**: Academics often self-host preprints
   ```
   mcp__firecrawl__firecrawl_search({
     query: "<author name> <institution> publications \"<paper title>\"",
     limit: 3
   })
   ```

2. **Citation context extraction**: Find papers that cite this work and quote key findings
   ```
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=citations.title,citations.abstract
   ```
   Read citing papers' abstracts for mentions of this work's findings. This provides indirect evidence of what the paper claims.

**All source types — universal fallbacks**:
1. **Semantic Scholar TLDR**: If not already captured in Resolver 3, the TLDR field provides a one-sentence machine-generated summary
2. **Google Scholar snippet**: Web search for the title often surfaces a snippet with the abstract

### Enrichment Output

For each enriched source, update `research/sources/<key>.md`:
- Set `Access Level: ABSTRACT-ONLY` (upgraded from METADATA-ONLY)
- Add `Enrichment Sources:` field listing where the content came from
- Add content under `## Content Snapshot` with clear provenance:
  ```markdown
  ## Content Snapshot
  *Enriched from secondary sources (not direct access to the original work)*

  **From Wikipedia**: [summary of the work's central thesis]
  **From book review in [Journal]**: [key arguments and findings]
  **From publisher description**: [scope and chapter overview]
  ```
- Add `## Key Findings` synthesized from enrichment sources

**Important**: Clearly label enriched content as secondary — it's a summary of summaries, not the original work. The evidence matrix should score enriched-ABSTRACT-ONLY sources lower than direct-ABSTRACT-ONLY sources (those where the actual abstract was read). Add an `Enrichment: secondary` flag to the source extract so the scoring model can distinguish them.

---

## Phase 3: Human Acquisition (MANDATORY pause)

After automated resolution and enrichment, re-count access levels. **This pause is MANDATORY if any sources remain ABSTRACT-ONLY or METADATA-ONLY.** Do NOT skip it, do NOT proceed to Stage 2 without it. The user must explicitly say "skip" or "continue" before the pipeline advances.

1. **Prioritize the acquisition list** — If `research/claims_matrix.md` exists and has evidence density scores, sort by evidence impact: papers that support WEAK or CRITICAL claims get highest priority (upgrading a source from ABSTRACT-ONLY to FULL-TEXT has the most impact on under-supported claims). Otherwise (first pipeline run, no matrix yet), fall back to citation frequency in the research files. In standard mode, present only the **top 5** papers. In deep mode, present ALL abstract-only and metadata-only papers.

2. **Use AskUserQuestion** to present the list and pause. This is a BLOCKING call — the pipeline STOPS here until the user responds:

```
I've completed automated source acquisition and found [N] references. Here's the coverage:

✓ [X] papers with full text accessed
⚠ [Y] papers where I only have an abstract or summary
✗ [Z] papers where I only have metadata

Automated resolution upgraded [A] sources via OA APIs and enriched [B] sources with secondary content.

The following papers would strengthen the manuscript if I had full text.
They're sorted by importance (impact on evidence scoring):

1. **[key]** — "[Title]" ([Year]) — [source_type]
   DOI: [doi] | Cited [N] times in draft | Evidence impact: [HIGH/MEDIUM/LOW]
   Tried: [list of resolvers that were attempted]
   💡 Suggested: Search "[title]" on your preferred sources
   🔗 Found on ResearchGate: [url] (free account needed)

2. **[key]** — "[Title]" ([Year]) — [source_type]
   DOI: [doi] | Cited [N] times in draft | Evidence impact: [HIGH/MEDIUM/LOW]
   Tried: [list of resolvers attempted]
   💡 Suggested: Check your library access or private trackers

[... more papers ...]

Drop any PDFs you find into the `attachments/` folder and say "continue" when ready.
Or say "skip" to proceed with current coverage (I'll flag thin evidence in the paper).
```

3. **When the user responds**:
   - If "continue" or similar: scan `attachments/` for new PDFs, run the PDF Validation Protocol on each, then run the ingestion logic (same as `/ingest-papers`), update source extracts to FULL-TEXT with content snapshots
   - If "skip" or similar: proceed, but mark all abstract-only sources with a warning flag in the claims-evidence matrix

4. **If ALL sources already have full text** after Phases 2 and 2b (every single reference in `references.bib` has a corresponding `research/sources/<key>.md` with `Access Level: FULL-TEXT`), skip the pause. But this should be RARE — verify the count before skipping. If even ONE source is ABSTRACT-ONLY or METADATA-ONLY, you MUST pause.

---

## Phase 4: Update Coverage Report

After acquisition is complete (or skipped), update `research/source_coverage.md` with final counts and resolution details.

Include a **Resolution Sources** section:
```markdown
## Resolution Sources
| Resolver | Papers Resolved | Papers Attempted | Abstracts Found |
|-|-|-|-|
| Unpaywall | 8 | 25 | 0 |
| OpenAlex | 3 | 17 | 12 |
| Semantic Scholar | 2 | 14 | 10 |
| CrossRef | 0 | 20 | 15 |
| CORE | 1 | 12 | 3 |
| PubMed Central | 4 | 4 | 4 |
| arXiv | 2 | 8 | 8 |
| DBLP | 1 | 6 | 0 |
| BASE | 1 | 15 | 5 |
| Internet Archive | 2 | 10 | 0 |
| DOAB | 0 | 4 | 0 |
| Google Books | 0 | 8 | 6 |
| Web search | 2 | 20 | 0 |
| Repository search | 1 | 15 | 0 |
| Content enrichment | — | 12 | 12 |
| Manual (user) | 3 | 3 | 0 |
```

Include a **Validation Summary**:
```markdown
## PDF Validation Summary
| Result | Count |
|-|-|
| VALID | 18 |
| LIKELY VALID | 3 |
| MISMATCH (discarded) | 2 |
| INVALID (non-PDF) | 4 |
| UNVERIFIABLE (scanned) | 1 |
```

---

## Phase 5: Knowledge Graph Build

After source acquisition is complete, build the knowledge graph from all source extracts and PDFs:

```bash
python scripts/knowledge.py build
```

**Run this command with `run_in_background: true`** — the knowledge graph build can take 10-30+ minutes depending on source count and PDF volume. Running in background avoids the Bash timeout limit and lets you continue with other work while it builds. You will be notified when it completes.

This creates a queryable knowledge graph in `research/knowledge/` from all files in `research/sources/` and PDFs in `attachments/`. The graph extracts entities (papers, theories, methods, findings, authors) and relationships (cites, contradicts, supports, extends) that agents can query during writing.

**If `scripts/knowledge.py` does not exist or `OPENROUTER_API_KEY` is not set**, skip this step silently — the knowledge graph is optional. The pipeline works without it; agents fall back to reading research/ files directly.

Update `.paper-state.json`: add `"knowledge_graph": { "done": true, "entities": N, "relationships": N }` to the stages object.

---

## Checkpoint

**Checkpoint**: Verify `research/source_coverage.md` exists. Update `.paper-state.json`:
```json
"source_acquisition": {
  "done": true,
  "completed_at": "...",
  "full_text": N,
  "abstract_only": N,
  "metadata_only": N,
  "user_provided": N,
  "auto_resolved": N,
  "enriched": N,
  "validation": {
    "valid": N,
    "likely_valid": N,
    "mismatch": N,
    "invalid": N,
    "unverifiable": N
  }
}
```

Update `.paper-progress.txt`: "Stage 1d complete: [N] full-text, [M] abstract-only, [K] metadata-only sources ([J] auto-resolved, [L] enriched)"

---

## Evidence Score Recomputation

If `research/claims_matrix.md` exists (e.g., re-running Stage 1d on a paper that already has a claims matrix), recompute evidence density scores now. Source access levels may have changed (METADATA-ONLY → ABSTRACT-ONLY, ABSTRACT-ONLY → FULL-TEXT), which affects claim scores. Use the scoring model from Stage 2 step 5 to update the Score and Strength columns.

**Enrichment scoring note**: Sources upgraded via content enrichment (secondary sources) should be scored between METADATA-ONLY (0 base) and direct ABSTRACT-ONLY (standard base score). Use a modifier of 0.5× the standard ABSTRACT-ONLY base score for enriched sources — they have content, but it's secondhand.
