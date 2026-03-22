# Initialize Paper

Generate the full content of a research paper based on a topic description.

## Instructions

The user will provide a paper topic, research question, or abstract-level description. Your job:

1. **Read `.paper.json`** if it exists for topic and venue config. If it doesn't exist, create it with the topic from $ARGUMENTS.
2. **Read `main.tex`** to understand the current template structure and packages
3. **Read `.venue.json`** if it exists for venue-specific section structure and formatting
4. **Research the topic** using available search tools (Perplexity, web search, etc.) to gather:
   - Key papers and seminal works in the field
   - Current state of the art
   - Open problems and research gaps
   - Common methodologies
5. **Build `references.bib`** with 15-25 real, verified references. For each:
   - Search to verify the paper exists
   - Extract complete metadata
   - Use correct BibTeX entry type (@article, @inproceedings, @misc, etc.)
   - **Do NOT fabricate references** — if you can't verify a paper, don't include it
6. **Generate the paper content** in `main.tex`:
   - `\maketitle`
   - `\begin{abstract}` — 150+ word structured summary
   - All sections as defined in `.venue.json` or default IMRAD
   - `\bibliographystyle` and `\bibliography{references}` matching the venue
7. **Write in full paragraphs** — never leave bullet points in the manuscript
8. **Compile** with `latexmk -pdf -interaction=nonstopmode main.tex` and fix any errors (max 3 attempts)

Note: This is a single-pass quick generation. For thorough, journal-quality papers, use `/write-paper` instead.

## User Input

$ARGUMENTS
