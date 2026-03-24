# Search Literature

Find relevant papers for the given topic or research question.

## Instructions

1. **Parse the query** from $ARGUMENTS. If empty, read `.paper.json` for the paper topic.
2. **Search using all available tools** — try in this order, use whichever are available:
   - Perplexity search (`mcp__perplexity__search` or `mcp__perplexity__reason`)
   - Web search (WebSearch or WebFetch)
   - Firecrawl search (`mcp__firecrawl__firecrawl_search`) if available
   - Read `.claude/skills/arxiv-database/SKILL.md` for arXiv search guidance if the topic is CS/physics/math
   - Read `.claude/skills/pubmed-database/SKILL.md` for PubMed search guidance if the topic is biomedical
3. **For each relevant paper found** (target: 10-20 results), extract:
   - Full author list
   - Title
   - Journal/venue and year
   - DOI or arXiv ID (if findable)
   - 1-2 sentence summary of relevance
4. **Create source extracts** for each paper found:
   - Write `research/sources/<bibtexkey>.md` using the enhanced format (see `/write-paper` Stage 1 SOURCE EXTRACTS instructions)
   - Set `Access Level` based on what you actually accessed:
     - If you read the full paper (arXiv, open-access journal): `FULL-TEXT`
     - If you only read the abstract or a Perplexity summary: `ABSTRACT-ONLY`
     - If you only found it cited elsewhere: `METADATA-ONLY`
   - The Content Snapshot must contain the actual text you read — paste the abstract at minimum
   - If a source file already exists for this key, do not overwrite — only upgrade (abstract→full-text)
   - Run: `mkdir -p research/sources` before writing
5. **Organize results by theme**, not chronologically
6. **Prioritize**:
   - Foundational works (high citation count)
   - Recent state-of-the-art (2023-2026)
   - Methodological papers relevant to the approach
   - Direct competitors or closely related work
7. **If zero results** are found from all tools, report which tools were tried and what queries were used, so the user can refine.
8. **Output** a structured list the user can review before adding to `references.bib` with `/add-citation`

## Query

$ARGUMENTS
