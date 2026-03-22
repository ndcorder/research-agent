# Analyze Data — Statistical Analysis and Figure Generation

Analyze datasets, run statistical tests, generate publication-quality figures, and integrate results into the paper.

## Instructions

1. **Locate data files** in `attachments/` or a path specified by the user. Supported formats: CSV, TSV, JSON, Excel (.xlsx), Parquet, NumPy (.npy/.npz)
2. **Read and profile the data**:
   - Use the `exploratory-data-analysis` skill for systematic profiling
   - Report: dimensions, column types, missing values, basic statistics
   - Identify the dependent/independent variables
3. **Run appropriate statistical analyses**:
   - Use the `statistical-analysis` skill for test selection
   - Normality tests (Shapiro-Wilk) → parametric vs non-parametric
   - Descriptive statistics (mean, SD, median, IQR, range)
   - Inferential tests as appropriate (t-test, ANOVA, Mann-Whitney, chi-squared, etc.)
   - Effect sizes (Cohen's d, eta-squared, odds ratios)
   - Confidence intervals
   - Correlation analyses where relevant
   - Regression if applicable
4. **Generate figures** using Python scripts:
   - Use `matplotlib` and `seaborn` skills for publication-quality plots
   - Save all figures to `figures/` as PDF (vector format)
   - Save generating scripts to `figures/scripts/` for reproducibility
   - Figure types to consider:
     - Distribution plots (histogram, violin, box)
     - Comparison plots (bar with error bars, grouped)
     - Correlation plots (scatter with regression line, heatmap)
     - Time series (line plots with confidence bands)
   - Apply publication styling: no gridlines, serif fonts, appropriate DPI
5. **Generate results tables**:
   - Create LaTeX table code with booktabs formatting
   - Include statistical test results (test statistic, df, p-value, effect size)
   - Insert into `main.tex` in the Results section
6. **Write analysis report** to `research/data_analysis.md`:
   - Dataset description
   - Statistical test results with interpretation
   - Figure descriptions and file paths
   - Key findings summary
7. **Integrate into paper**:
   - Add `\includegraphics{}` for each figure in Results section of `main.tex`
   - Add results tables to Results section
   - Ensure all figures/tables are referenced in text with `\ref{}`

## Python Environment

Run analysis scripts with `python3`. Install packages if needed:
```bash
python3 -m pip install pandas numpy scipy matplotlib seaborn scikit-learn statsmodels
```

## Data Source

$ARGUMENTS
