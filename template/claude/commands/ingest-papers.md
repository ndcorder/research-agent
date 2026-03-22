# Ingest Papers — Extract and Catalog Reference PDFs

Read PDFs from `attachments/`, extract their content, generate BibTeX entries, and produce summaries for citation.

## Instructions

1. **Scan `attachments/`** for PDF files
2. **For each PDF**, use the Read tool (which supports PDF reading) to extract content:
   - Read the first 5 pages to find: title, authors, abstract, journal/venue, year, DOI
   - Read the references section (usually last pages) for bibliography mining
3. **Generate a BibTeX entry** for each paper:
   - Extract complete metadata (authors, title, journal, volume, pages, year, DOI)
   - Use `citation-management` skill for proper formatting
   - Key format: `firstauthorlastnameYear`
   - Append to `references.bib` (check for duplicates first)
4. **Write a summary file** for each paper to `research/ingested/`:
   - `research/ingested/<filename>.md` with:
     - Full citation
     - Abstract
     - Key findings (3-5 bullet points)
     - Methodology summary
     - Relevance to the current paper topic (read `.paper.json` for topic)
     - Notable figures/tables
     - Citation key for referencing
5. **Report** how many papers were ingested and their citation keys

## Tips
- If a PDF is a scan/image-based, note that text extraction may be limited
- Cross-reference extracted papers against existing `references.bib` to avoid duplicates
- If DOI is found, verify metadata via Perplexity or web search for accuracy
- Create `research/ingested/` directory if it doesn't exist: `mkdir -p research/ingested`

## Papers to Ingest

$ARGUMENTS

If no arguments given, ingest ALL PDFs in `attachments/`.
