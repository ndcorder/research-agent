# Ingest Papers — Extract and Catalog Reference PDFs

Read PDFs from `attachments/`, extract their content, generate BibTeX entries, and produce summaries for citation.

## Instructions

1. **Scan `attachments/`** for PDF files. If no PDFs found, report and stop. Ignore non-PDF files (`.csv`, `.docx`, etc. are handled by `/analyze-data`).
2. **Create output directory**: `mkdir -p research/ingested`
3. **For each PDF**, use the Read tool to extract content:
   - Read pages 1-5 to find: title, authors, abstract, journal/venue, year, DOI
   - Read the last 3-5 pages (use the `pages` parameter, e.g., `pages: "last 5"`) for the references section
   - **Note**: The Read tool supports max 20 pages per request. For longer papers, read strategically (first 5 + last 5), not the entire PDF.
4. **Generate a BibTeX entry** for each paper:
   - Extract complete metadata (authors, title, journal, volume, pages, year, DOI)
   - Read `.claude/skills/citation-management/SKILL.md` for BibTeX formatting guidance
   - Key format: `firstauthorlastnameYear` (handle collisions with a/b suffix)
   - Read `references.bib` first — check for duplicates by title before adding
   - Append to `references.bib`
5. **Write a summary file** for each paper to `research/ingested/<filename-without-ext>.md`:
   - Full citation
   - Abstract (extracted or summarized)
   - Key findings (3-5 points)
   - Methodology summary
   - Relevance to current paper (read `.paper.json` for topic — if file doesn't exist, skip relevance assessment)
   - Citation key for referencing
6. **Report** how many papers were ingested, their citation keys, and any that failed extraction

## Papers to Ingest

$ARGUMENTS

If no arguments given, ingest ALL PDFs in `attachments/`.
