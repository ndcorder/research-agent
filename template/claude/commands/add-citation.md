# Add Citation

Add a properly formatted BibTeX entry to references.bib.

## Instructions

The user provides a paper identifier (DOI, arXiv ID, title, or URL). Your job:

1. **Look up the paper** using available tools:
   - For DOI: use `perplexity::search` or CrossRef API via bash (`curl`)
   - For arXiv ID: query arXiv API
   - For title: search with `perplexity::search` to find the canonical reference
2. **Extract complete metadata**:
   - All authors (last, first format)
   - Full title
   - Journal/conference name
   - Volume, number, pages
   - Year
   - DOI
   - Publisher (for books/proceedings)
3. **Generate BibTeX key**: `firstauthorlastnameYear` format (e.g., `smith2024`)
4. **Check for duplicates** in `references.bib` — don't add if already present
5. **Append** the entry to `references.bib` with proper formatting:
   ```bibtex
   @article{key,
     author  = {Last, First and Last, First},
     title   = {Full Title},
     journal = {Journal Name},
     volume  = {X},
     number  = {Y},
     pages   = {1--10},
     year    = {2024},
     doi     = {10.xxxx/xxxxx},
   }
   ```
6. **Confirm** the addition and show the key for use with `\citep{key}` or `\citet{key}`

## Paper to Add

$ARGUMENTS
