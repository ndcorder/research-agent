# Analyze Data — Statistical Analysis and Figure Generation

Analyze datasets, run statistical tests, generate publication-quality figures, and integrate results into the paper.

## Instructions

1. **Check Python environment first**:
   ```bash
   python3 -c "import pandas, numpy, scipy, matplotlib, seaborn" 2>&1
   ```
   If any are missing, install them: `python3 -m pip install pandas numpy scipy matplotlib seaborn scikit-learn statsmodels openpyxl`
   If `python3` itself is unavailable, report the issue and stop.

2. **Locate data files** in `attachments/` or a path specified by the user. Supported formats: CSV, TSV, JSON, Excel (.xlsx), Parquet, NumPy (.npy/.npz).
   - If no data files are found, report and stop.
   - For files over 100MB, use chunked reading (`pandas.read_csv(..., chunksize=10000)`) or sample.

3. **Read and profile the data**:
   - Report: dimensions, column types, missing values, basic statistics
   - Identify the dependent/independent variables

4. **Run appropriate statistical analyses**:
   - Use the `statistical-analysis` skill from `.claude/skills/statistical-analysis/SKILL.md` if available (read it first)
   - Normality tests (Shapiro-Wilk) to determine parametric vs non-parametric
   - Descriptive statistics (mean, SD, median, IQR, range)
   - Inferential tests as appropriate (t-test, ANOVA, Mann-Whitney, chi-squared, etc.)
   - Effect sizes (Cohen's d, eta-squared, odds ratios)
   - Confidence intervals
   - Correlation analyses where relevant

5. **Generate figures** using Python scripts:
   - Save all figures to `figures/` as PDF (vector format)
   - Save generating scripts to `figures/scripts/` for reproducibility
   - Apply publication styling: no gridlines, readable fonts, appropriate sizing
   - Run each script and verify the output file exists

6. **Generate results tables** as LaTeX code with booktabs formatting

7. **Integrate into paper**:
   - Read `main.tex` and find the Results section (check for `\section{Results}`, `\section{Experiments}`, or similar)
   - If no Results section exists, add one
   - Add `\includegraphics{}` and tables with proper `\label{}`, `\caption{}`, and `\ref{}` in text

8. **Write analysis report** to `research/data_analysis.md`

## Data Source

$ARGUMENTS

If no arguments given, scan `attachments/` for data files.
