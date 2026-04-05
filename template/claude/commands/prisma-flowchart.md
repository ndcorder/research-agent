# PRISMA Flowchart Generator

Generate a PRISMA 2020 flowchart from structured metadata and add it to the manuscript.

---

## Step 1: Load PRISMA metadata

Read `research/prisma_metadata.json`. If it doesn't exist, build it:

```bash
python scripts/prisma-metadata.py --project . build
```

Then read the JSON file and extract:
- **Identification**: `search_strategy.total_identified` for database results, sum of `other_sources[].results` for other methods
- **Deduplication**: `deduplication.duplicates_removed`, `deduplication.after`
- **Screening**: `screening.screened`, `screening.excluded`, `screening.exclusion_reasons[]`
- **Eligibility**: `eligibility.assessed`, `eligibility.excluded`, `eligibility.exclusion_reasons[]`
- **Included**: `included.qualitative_synthesis`, `included.quantitative_synthesis`

## Step 2: Validate counts

Verify the PRISMA flow is internally consistent:
1. `deduplication.after` should equal `screening.screened`
2. `screening.screened - screening.excluded` should approximately equal `eligibility.assessed`
3. `eligibility.assessed - eligibility.excluded` should approximately equal `included.qualitative_synthesis`

If counts don't add up, log warnings but proceed — some sources may have been added via targeted research after initial screening.

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

Replace every `XXXX` with the actual numbers from `prisma_metadata.json`. If any number is estimated, prefix it with `$\approx$\,` (e.g., `$\approx$\,120`).

For exclusion reason nodes, populate from the structured data. Format each reason from the JSON arrays:

**Screening exclusions** — use `screening.exclusion_reasons[]`:
```latex
\node[smallbox, text width=5.5cm] (screen-excl) at (5.5, -4.8) {
  Records excluded (n = SCREENING_EXCLUDED):\\
  % One line per screening.exclusion_reasons entry:
  REASON_1 (n = COUNT_1)\\
  REASON_2 (n = COUNT_2)\\
  ...
};
```

**Eligibility exclusions** — use `eligibility.exclusion_reasons[]`:
```latex
\node[smallbox, text width=5.5cm] (ft-excl) at (5.5, -7) {
  Full-text articles excluded (n = ELIGIBILITY_EXCLUDED):\\
  % One line per eligibility.exclusion_reasons entry:
  REASON_1 (n = COUNT_1)\\
  REASON_2 (n = COUNT_2)\\
  ...
};
```

Generate the full exclusion breakdown from `screening.exclusion_reasons` and `eligibility.exclusion_reasons` — do NOT summarize or group reasons. Each reason from the JSON gets its own line in the flowchart.

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
