---
description: Diagnose research failures — test API connectivity, analyze logs, identify gaps
---

# Debug Research — Diagnose Research Failures

Diagnose why research agents failed to find papers. Tests API connectivity, analyzes the research log, identifies gap patterns, and suggests fixes.

**Model**: Use `claude-sonnet-4-6[1m]` for this command.

## Prerequisites

Check that `.paper.json` exists. If not, abort with: "This command must be run from within a paper project directory."

## Step 1: Analyze the Research Log

Read `research/log.md` if it exists. Parse all entries (format: `### [TIMESTAMP] — [AGENT NAME]` followed by Tool, Query, Result, Key finds, URLs/DOIs).

Build a summary:

1. **Per-tool stats**: For each tool name, count: total calls, successes (`SUCCESS`), failures (`FAILURE`), empty results (`EMPTY`). Calculate success rate.
2. **Failure modes**: Group failure messages into categories:
   - `rate-limited` — mentions of 429, rate limit, throttle, too many requests
   - `timeout` — mentions of timeout, timed out, ETIMEDOUT
   - `not-found` — mentions of 404, not found, no results
   - `auth-error` — mentions of 401, 403, unauthorized, forbidden, API key
   - `server-error` — mentions of 500, 502, 503, internal server error
   - `tool-unavailable` — tool not found, MCP error, connection refused
   - `other` — anything else
3. **Timeline**: Note if failures cluster in time (burst of rate limits) or are spread out.

Also read `research/provenance.jsonl` if it exists. Count research-type entries and note which stages generated research activity.

If neither file exists, report: "No research logs found. The pipeline has not run yet or logs were not generated."

## Step 2: Test API Connectivity

Run these tests in parallel using Bash (use `timeout: 10000` for each curl):

1. **Semantic Scholar**: `curl -s -o /dev/null -w "%{http_code}" "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"`
   - 200 = OK, 429 = rate-limited, other = error

2. **CrossRef**: `curl -s -o /dev/null -w "%{http_code}" "https://api.crossref.org/works?query=test&rows=1"`
   - 200 = OK

3. **OpenAlex**: `curl -s -o /dev/null -w "%{http_code}" "https://api.openalex.org/works?search=test&per_page=1"`
   - 200 = OK

4. **PubMed (NCBI)**: `curl -s -o /dev/null -w "%{http_code}" "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=test&retmax=1"`
   - 200 = OK

5. **Unpaywall**: Check if `UNPAYWALL_EMAIL` env var is set (or `email` in `.paper.json`). If not: MISSING (required for Unpaywall API). Do not make a test request without an email.

6. **CORE**: Check if `CORE_API_KEY` env var is set. If set, test: `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $CORE_API_KEY" "https://api.core.ac.uk/v3/search/works?q=test&limit=1"`

7. **Knowledge Graph**: Check if `OPENROUTER_API_KEY` is set AND `research/knowledge/` directory exists with content.

Report each as a table row: API | Status | Detail.

## Step 3: Identify Gap Patterns

Read `references.bib` and scan `research/sources/` for source extract files.

For each source extract, read the Access Level line. Collect all sources with access level `METADATA-ONLY` or `ABSTRACT-ONLY`.

For each gap source (up to 20):
- Show the BibTeX key, title (from the extract or bib), and current access level
- Search `research/log.md` for entries mentioning this key or title — show which tools were tried
- Categorize why it failed (rate-limited, not found, no PDF available, etc.)

Group the gaps:
- **Rate limited**: Sources where attempts failed due to rate limiting
- **Not found**: Sources where APIs returned no results
- **No OA PDF**: Sources found but no open-access full text available
- **API errors**: Sources where API errors prevented retrieval
- **Not attempted**: Sources with no log entries (may have been added manually or via citation snowballing without follow-up)

## Step 4: Suggest Fixes

Based on findings from Steps 1-3, generate targeted recommendations:

**For rate limiting issues**:
- "Wait 5-10 minutes and re-run the pipeline — Semantic Scholar has a 100 req/5min limit for unauthenticated users"
- "Set `NCBI_API_KEY` to increase PubMed rate limit from 3/s to 10/s" (if PubMed was rate-limited)
- "Add `email` to `.paper.json` for CrossRef/OpenAlex polite pool (higher rate limits)"

**For "not found" issues**:
- "Try alternative search terms: [suggest variations based on the failed queries from the log]"
- "Check if the paper is a book, thesis, or grey literature — these need different databases"
- "Run `/audit-sources` to trigger the full 14-resolver OA cascade"

**For API/auth errors**:
- "Set `CORE_API_KEY` for access to 200M+ institutional repository papers"
- "Check network connectivity — [N] APIs returned server errors"
- "Set `OPENROUTER_API_KEY` to enable the knowledge graph"

**For knowledge graph issues**:
- "Run `python scripts/knowledge.py build` to create the knowledge graph from existing sources"
- "Set `OPENROUTER_API_KEY` (required for knowledge graph LLM and embeddings)"

**For low source coverage overall**:
- "Run `/audit-sources` to attempt OA resolution for all references"
- "Run `/deep-read` after acquiring PDFs to upgrade source extracts"
- "Place PDFs manually in `attachments/` and run `/ingest-papers`"

Only show recommendations relevant to the actual issues found. Do not dump all suggestions.

## Step 5: Retry (only if `--retry` flag present)

**Only execute this step if the user's command includes `--retry`.**

From Step 3, select the top 5 highest-impact gap sources (prefer METADATA-ONLY over ABSTRACT-ONLY, prefer sources cited more often in the manuscript).

For each, attempt a fresh search using the tool fallback chain from `pipeline/shared-protocols.md`:
1. Domain-specific database skills
2. Perplexity search
3. Web search
4. Firecrawl search
5. Web fetch of known database URLs

If a source is found at a higher access level, update its source extract in `research/sources/`. Log all attempts to `research/log.md` using the standard log format.

Report: which sources were upgraded, which remain at their current level.

## Output Format

```
Research Diagnostics
====================

Log Analysis (research/log.md)
  Total tool calls:  47
  Success rate:      72% (34/47)

  Per-tool breakdown:
    perplexity__search     18 calls   83% success
    WebSearch              12 calls   75% success
    firecrawl_search        8 calls   50% success
    arxiv-database          5 calls   60% success
    WebFetch                4 calls   50% success

  Failure patterns:
    rate-limited    5 events  (Semantic Scholar: 3, PubMed: 2)
    not-found       4 events  (WebSearch: 2, firecrawl: 2)
    timeout         2 events  (WebFetch: 2)
    tool-unavailable 1 event  (pubmed-database: 1)

API Connectivity
  Semantic Scholar   [OK]     200
  CrossRef           [OK]     200
  OpenAlex           [OK]     200
  PubMed             [OK]     200
  Unpaywall          [WARN]   UNPAYWALL_EMAIL not set
  CORE               [MISSING] CORE_API_KEY not set
  Knowledge Graph    [OK]     OPENROUTER_API_KEY set, graph built

Source Gaps (12 of 38 references below FULL-TEXT)
  ABSTRACT-ONLY (8):
    smith2024       "Deep Learning for X"       tried: perplexity, WebSearch — no OA PDF
    jones2023       "Survey of Y"               tried: perplexity — rate limited
    ...
  METADATA-ONLY (4):
    lee2022         "Method Z"                  not attempted
    ...

Recommendations
  1. Set UNPAYWALL_EMAIL (or add email to .paper.json) for OA resolution
  2. Set CORE_API_KEY for institutional repository access
  3. Run /audit-sources to attempt full cascade for 12 gap sources
  4. Wait 5 min then retry — 5 failures were rate-limited
```

Adapt the format to the actual findings. Omit sections that have no issues (e.g., if all APIs are OK, keep the table but don't add recommendations for connectivity).
