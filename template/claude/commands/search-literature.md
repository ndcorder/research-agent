# Search Literature

Find relevant papers for the given topic or research question.

## Instructions

1. **Parse the query** from the user's input
2. **Search multiple sources** using available tools:
   - `perplexity::search` or `perplexity::reason` for broad academic search
   - `research-lookup` skill for structured paper retrieval
   - `arxiv-database` skill for preprints (CS, physics, math, quant-bio)
   - `pubmed-database` skill for biomedical literature
   - `biorxiv-database` skill for life sciences preprints
   - `openalex-database` skill for cross-disciplinary search
3. **For each relevant paper found**, extract:
   - Full author list
   - Title
   - Journal/venue and year
   - DOI or arXiv ID
   - 1-2 sentence summary of relevance
4. **Organize results** by theme, not chronologically
5. **Prioritize**:
   - Highly cited foundational works
   - Recent state-of-the-art (last 2-3 years)
   - Methodological papers relevant to the approach
   - Direct competitors or closely related work
6. **Output** a structured list the user can review before adding to `references.bib`

## Query

$ARGUMENTS
