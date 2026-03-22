# Research Paper Writing Agent

Scientific paper writing workspace powered by Claude Code with agent-based orchestration.

## Project Structure

```
main.tex          # Primary LaTeX document
references.bib    # BibTeX references
figures/          # Generated and imported figures
attachments/      # Reference PDFs, data files, supplementary materials
research/         # Literature research outputs (created by /write-paper)
reviews/          # Review feedback (created by /write-paper)
.paper.json       # Paper topic and configuration
.claude/skills/   # -> vendor/claude-scientific-skills (177 scientific skills)
```

## LaTeX Compilation

- **Compiler**: `pdflatex` via `latexmk`
- **Compile command**: `latexmk -pdf -interaction=nonstopmode main.tex`
- **Clean command**: `latexmk -c`
- **BibTeX**: Use `natbib` with `\citep{}` and `\citet{}` commands
- After editing references.bib, run: `latexmk -pdf -interaction=nonstopmode main.tex` (latexmk handles bibtex automatically)

## Writing Rules

1. **Always write in full paragraphs.** Never leave bullet points in the final manuscript.
2. **Two-stage writing process**:
   - Stage 1: Research and outline with key points
   - Stage 2: Convert outlines into flowing academic prose with transitions
3. **IMRAD structure**: Introduction, Methods/Approach, Results/Experiments, Discussion
4. **Citations**: Use `\citep{key}` for parenthetical and `\citet{key}` for narrative citations
5. **Figures**: Save to `figures/`, reference with `\includegraphics{figures/filename}`
6. **Tables**: Use `booktabs` package (`\toprule`, `\midrule`, `\bottomrule`)
7. **Cross-references**: Use `\label{}` and `\ref{}` consistently
8. **No placeholder text**: Remove all `\lipsum`, TODO, TBD, FIXME before finalizing
9. **No fabricated references**: Every BibTeX entry must be a real, verifiable publication

## Autonomous Pipeline: /write-paper

The primary workflow. Run `/write-paper <topic>` to launch the full pipeline:

1. **Deep Research** — Parallel agents search literature across all available sources
2. **Planning** — Thesis statement, contribution, detailed outline
3. **Writing** — Sequential agents write each section (1000-2500 words each)
4. **Figures & Tables** — Ensure adequate visual elements
5. **Quality Assurance** — Parallel review agents + revision loop (up to 5 iterations)
6. **Finalization** — Polish, compile, report

This runs for 1-4 hours. Agents use `model: "opus"` for writing, `model: "sonnet"` for research/review.

## Manual Commands

For interactive, step-by-step work:

### Writing
- `/init` — Quick single-pass paper generation
- `/outline` — Generate a structured outline for a section
- `/revise-section` — Rewrite a section based on feedback

### Research & References
- `/search-literature` — Find relevant papers for a topic
- `/add-citation` — Add a properly formatted BibTeX entry
- `/ingest-papers` — Import PDFs from `attachments/`, extract metadata and summaries
- `/cite-network` — Analyze citation patterns, find coverage gaps

### Data & Figures
- `/analyze-data` — Statistical analysis on datasets, generate publication figures

### Quality & Build
- `/review` — Comprehensive manuscript quality review
- `/validate-references` — Verify every citation is real (CrossRef, search). Critical before submission.
- `/compile` — Compile LaTeX to PDF and report errors
- `/status` — Progress dashboard (word counts, refs, pipeline stage)
- `/preview-pipeline` — Dry run of `/write-paper` (shows plan without executing)

### Submission
- `/prepare-submission` — Generate submission package (anonymized, cover letter, supplementary)
- `/clean` — Remove build artifacts and working directories

## Agent Usage Guidelines

When spawning agents for paper work:
- **Research agents**: Run in parallel. Each writes to a separate file in `research/`. Use `model: "sonnet"`.
- **Writing agents**: Run sequentially (later sections reference earlier ones). Use `model: "opus"`.
- **Review agents**: Run in parallel. Each writes to a separate file in `reviews/`. Use `model: "sonnet"`.
- **Revision agents**: Run sequentially. Read all reviews, edit `main.tex`. Use `model: "opus"`.
- Always include detailed, specific prompts for each agent — they have no shared context.

## File Conventions

- All `.tex` files use UTF-8 encoding
- BibTeX keys: `authorYear` format (e.g., `smith2024`)
- Figure filenames: descriptive, lowercase, hyphens (e.g., `model-architecture.pdf`)
- Prefer vector formats (PDF, EPS) for figures; PNG only for photographs/screenshots
- Float placement: use `[htbp]` not `[H]` unless absolutely necessary
