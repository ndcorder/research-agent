# Initialize Paper

Generate the full content of a research paper based on a topic description.

## Instructions

The user will provide a paper topic, research question, or abstract-level description. Your job:

1. **Read `main.tex`** to understand the current template structure and packages available
2. **Research the topic** using the `research-lookup` skill, `perplexity::search`, or `perplexity::reason` to gather:
   - Key papers and seminal works in the field
   - Current state of the art
   - Open problems and research gaps
   - Common methodologies
3. **Build `references.bib`** with 15-30 real, verified references using `/add-citation` workflow
4. **Generate the paper structure** in `main.tex`:
   - `\maketitle`
   - `\begin{abstract}` — 150-300 word structured summary
   - `\section{Introduction}` — Motivation, gap, contribution, paper organization
   - `\section{Related Work}` — Thematic literature survey (not study-by-study)
   - `\section{Methods}` or `\section{Approach}` — Methodology in detail
   - `\section{Results}` or `\section{Experiments}` — Findings with tables/figures
   - `\section{Discussion}` — Interpretation, limitations, future work
   - `\section{Conclusion}` — Key takeaways
   - `\bibliographystyle{plainnat}` and `\bibliography{references}`
5. **Write in full paragraphs** — never leave bullet points in the manuscript
6. **Compile** with `latexmk -pdf -interaction=nonstopmode main.tex` and fix any errors

## User Input

$ARGUMENTS
