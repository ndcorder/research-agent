# Ingest Papers — Extract and Catalog Reference PDFs

Read PDFs from `attachments/`, extract their content, generate BibTeX entries, and produce summaries for citation.

## Instructions

1. **Scan `attachments/`** for PDF files. If no PDFs found, report and stop. Ignore non-PDF files (`.csv`, `.docx`, etc. are handled by `/analyze-data`).
2. **Create output directories**: `mkdir -p research/sources research/ingested`
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
5. **Write a source extract** for each paper to `research/sources/<bibtexkey>.md` (NOT `research/ingested/`):
   - Use the enhanced source extract format:
     ```markdown
     # <Paper Title>

     **Citation**: <authors>, <title>, <venue>, <year>
     **DOI/URL**: <doi or url>
     **BibTeX Key**: <key>
     **Access Level**: FULL-TEXT
     **Accessed Via**: PDF in attachments/<filename>

     ## Content Snapshot

     > <Paste the abstract verbatim>
     >
     > <Paste the most relevant sections to the current paper's topic (read .paper.json).
     > Include: key methodology description, main results/findings, and conclusions.
     > Target 500-1500 words of actual excerpted content.
     > This is verbatim or near-verbatim from the PDF — not your summary.>

     ## Key Findings Used

     <bullet points of specific findings relevant to the current paper>

     ## Provenance

     - **Found via**: User-provided PDF in attachments/
     - **Ingested**: <timestamp>
     - **PDF file**: attachments/<filename>
     ```
   - If a `research/sources/<key>.md` already exists (e.g., from an earlier abstract-only extract), UPDATE it: change Access Level to FULL-TEXT, replace the Content Snapshot with the richer PDF content, keep existing Key Findings and add new ones.
   - Also write to `research/ingested/<filename-without-ext>.md` as a secondary copy for backward compatibility.
6. **Report** how many papers were ingested, their citation keys, and any that failed extraction

## Papers to Ingest

$ARGUMENTS

If no arguments given, ingest ALL PDFs in `attachments/`.
