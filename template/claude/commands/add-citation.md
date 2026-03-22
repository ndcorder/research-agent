# Add Citation

Add a properly formatted BibTeX entry to references.bib.

## Instructions

The user provides a paper identifier (DOI, arXiv ID, title, or URL). Your job:

1. **Look up the paper** using available tools in this order (try the next if one fails):
   - For DOI: use WebFetch on `https://api.crossref.org/works/DOI`
   - For arXiv ID: use WebFetch on `https://export.arxiv.org/api/query?id_list=ARXIV_ID`
   - For title: search with Perplexity (`mcp__perplexity__search`) to find the canonical reference
   - Fallback: use general web search
2. **Extract complete metadata**:
   - All authors (Last, First format)
   - Full title
   - Journal/conference name
   - Volume, number, pages
   - Year
   - DOI
   - Publisher (for books/proceedings)
3. **Choose the correct entry type**:
   - `@article` — journal papers (has journal, volume, pages)
   - `@inproceedings` — conference papers (has booktitle for the conference name)
   - `@book` — books (has publisher)
   - `@misc` — arXiv preprints, technical reports, websites (use `howpublished` or `note` for URL)
   - `@phdthesis` / `@mastersthesis` — dissertations
4. **Generate BibTeX key**: `firstauthorlastnameYear` format (e.g., `smith2024`). If this key already exists in `references.bib`, append a letter: `smith2024a`, `smith2024b`, etc.
5. **Check for duplicates** in `references.bib` — compare by title (case-insensitive). Don't add if already present.
6. **Append** the entry to `references.bib` with proper formatting
7. **If lookup fails** (paper not found, ambiguous results): report what was found and ask the user to clarify rather than guessing

## Paper to Add

$ARGUMENTS
