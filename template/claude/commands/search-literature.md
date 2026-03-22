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
4. **Organize results by theme**, not chronologically
5. **Prioritize**:
   - Foundational works (high citation count)
   - Recent state-of-the-art (2023-2026)
   - Methodological papers relevant to the approach
   - Direct competitors or closely related work
6. **If zero results** are found from all tools, report which tools were tried and what queries were used, so the user can refine.
7. **Output** a structured list the user can review before adding to `references.bib` with `/add-citation`

## Query

$ARGUMENTS
