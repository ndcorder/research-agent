# PRISMA Flowchart Generator

Generate a PRISMA 2020 flowchart from the research log and add it to the manuscript.

---

## Step 1: Extract search statistics

Read the following files to gather screening/selection data:

1. **`research/log.md`** — Extract:
   - Number of database searches performed and results per database/source (e.g., Semantic Scholar: 45, OpenAlex: 32, web search: 18)
   - Total records identified through database searching
   - Any additional records identified through other methods (snowballing, co-citation, manual addition)
   - Records removed as duplicates
   - Records screened (title/abstract level)
   - Records excluded at screening with reasons
   - Full-text articles assessed for eligibility
   - Full-text articles excluded with reasons (e.g., "not empirical", "wrong population", "duplicate study", "insufficient data")
   - Studies included in final synthesis

2. **`references.bib`** — Count the total number of BibTeX entries (this is the final included count).

3. **`research/sources/`** — List all source extract files. Check the `Access Level` field in each:
   - `FULL-TEXT` sources were assessed at full-text level
   - `ABSTRACT-ONLY` sources were screened at abstract level
   - `METADATA-ONLY` sources may have been excluded or only briefly considered
   - Use these access levels as a proxy for the screening funnel if log.md lacks exact numbers.

## Step 2: Compute flowchart numbers

Map the extracted data to the PRISMA 2020 four-phase model:

- **Identification**: Total records from databases + total from other methods (snowballing, co-citation)
- **Duplicates removed**: Difference between raw results and unique records (estimate if not logged)
- **Screening**: Records after deduplication that were screened by title/abstract. Excluded count = screened minus those advancing to eligibility.
- **Eligibility**: Full-text articles assessed. Excluded count with categorized reasons.
- **Included**: Final count of studies in the review (should match references.bib count or the subset used for synthesis).

If exact numbers are unavailable for any phase, estimate from the available data. Add a note in the figure caption: "Counts marked with $\approx$ are estimates derived from the research log."

## Step 3: Generate TikZ PRISMA flowchart

Create the flowchart using TikZ. Write the code directly into `main.tex` (do not use an external .tex file). Place it in the Methods section after the search strategy description.

Use this TikZ structure:

```latex
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    box/.style={rectangle, draw=black, thick, text width=5.5cm, minimum height=1.2cm, align=center, font=\small},
    smallbox/.style={rectangle, draw=black, thick, text width=4cm, minimum height=1cm, align=center, font=\small},
    phase/.style={rectangle, fill=black!10, draw=black, thick, text width=2.8cm, minimum height=1cm, align=center, font=\small\bfseries, rotate=90},
    arrow/.style={->, thick, >=stealth},
    node distance=1.2cm
]

% Phase labels (left side, rotated)
\node[phase] (id-label) at (-5.5, 0) {Identification};
\node[phase] (sc-label) at (-5.5, -3.5) {Screening};
\node[phase] (el-label) at (-5.5, -7) {Eligibility};
\node[phase] (in-label) at (-5.5, -10) {Included};

% Identification
\node[box] (db-records) at (0, 0.8) {Records identified through\\database searching\\(n = XXXX)};
\node[box] (other-records) at (0, -0.8) {Additional records identified\\through other sources\\(n = XXXX)};

% Deduplication
\node[box] (after-dedup) at (0, -2.8) {Records after duplicates removed\\(n = XXXX)};

% Screening
\node[box] (screened) at (0, -4.8) {Records screened\\(n = XXXX)};
\node[smallbox] (screen-excl) at (5.5, -4.8) {Records excluded\\(n = XXXX)};

% Eligibility
\node[box] (fulltext) at (0, -7) {Full-text articles assessed\\for eligibility\\(n = XXXX)};
\node[smallbox] (ft-excl) at (5.5, -7) {Full-text articles excluded,\\with reasons\\(n = XXXX)};

% Included
\node[box] (included) at (0, -9.5) {Studies included in\\qualitative synthesis\\(n = XXXX)};

% Arrows
\draw[arrow] (db-records) -- (after-dedup);
\draw[arrow] (other-records) -- (after-dedup);
\draw[arrow] (after-dedup) -- (screened);
\draw[arrow] (screened) -- (fulltext);
\draw[arrow] (fulltext) -- (included);
\draw[arrow] (screened) -- (screen-excl);
\draw[arrow] (fulltext) -- (ft-excl);

\end{tikzpicture}
\caption{PRISMA 2020 flow diagram showing the identification, screening, eligibility assessment, and inclusion of studies in this review. XXXX.}
\label{fig:prisma}
\end{figure}
```

Replace every `XXXX` with the actual numbers computed in Step 2. If any number is estimated, prefix it with `$\approx$\,` (e.g., `$\approx$\,120`).

If full-text exclusion reasons are available, itemize them inside the exclusion box or add a sub-list below it:
```
Full-text articles excluded (n = XX):\\
Not empirical (n = X)\\
Wrong scope (n = X)\\
Duplicate (n = X)
```

## Step 4: Insert into main.tex

1. Ensure `\usepackage{tikz}` is in the preamble (add it if missing).
2. Place the figure environment in the **Methods** section, ideally after the paragraph describing the search strategy and selection criteria.
3. Add a `\ref{fig:prisma}` cross-reference in the Methods text, e.g.: "The study selection process is summarized in Figure~\ref{fig:prisma}."
4. Verify the figure compiles by running `latexmk -pdf -interaction=nonstopmode main.tex`.

## Step 5: Log provenance

Append to `research/provenance.jsonl`:
```json
{"ts":"[timestamp]","stage":"4","agent":"prisma-flowchart","action":"add","target":"fig:prisma in main.tex","reasoning":"PRISMA 2020 flowchart showing systematic study selection process","sources":["research/log.md"],"iteration":0}
```
