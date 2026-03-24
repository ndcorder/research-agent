# Research Paper Writing Agent

Scientific paper writing workspace powered by Claude Code with agent-based orchestration.

## Project Structure

```
main.tex          # Primary LaTeX document
references.bib    # BibTeX references
figures/          # Generated and imported figures
attachments/      # Reference PDFs, data files, supplementary materials
research/         # Literature research outputs (created by /write-paper)
  sources/        # Raw source extracts per cited paper (abstract, key findings, provenance)
  log.md          # Research provenance log (all searches, queries, tools, results)
reviews/          # Review feedback (created by /write-paper)
archive/          # Browsable research archive with index (created at end of /write-paper or via /archive)
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
10. **Claims-Evidence Matrix**: Every major claim must map to specific evidence (experiment, citation, or proof) in `research/claims_matrix.md`

## Autonomous Pipeline: /write-paper

The primary workflow. Run `/write-paper <topic>` to launch the full pipeline:

1. **Deep Research** — Parallel agents search literature across all available sources
2. **Planning** — Thesis statement, contribution, detailed outline, claims-evidence matrix, novelty verification
3. **Writing** — Sequential agents write each section (1000-2500 words each)
4. **Figures & Tables** — Ensure adequate visual elements
5. **Quality Assurance** — Parallel review agents + revision loop (up to 5 iterations)
6. **Finalization** — Polish, compile, archive all artifacts, report

This runs for 1-4 hours (standard) or 3-8 hours (deep). Three model tiers with 1M context: `claude-opus-4-6[1m]` for writing/reasoning, `claude-sonnet-4-6[1m]` for research/review, `haiku` for mechanical tasks. Set `depth` in `.paper.json` to `"deep"` for 3× research effort.

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
- `/ask` — Query research artifacts to answer questions about the research (searches sources, notes, reviews, log)

### Data & Figures
- `/analyze-data` — Statistical analysis on datasets, generate publication figures
- `/praxis-analyze` — Technique-specific analysis via Praxis (XRD, DSC, EIS, mechanical, spectroscopy, etc.) with venue-matched journal figures

### Quality & Build
- `/review` — Comprehensive manuscript quality review
- `/check-consistency` — Find notation, terminology, abbreviation, and tense inconsistencies
- `/audit-claims` — Flag overclaims, unsupported statements, missing significance tests
- `/validate-references` — Verify every citation is real (CrossRef, search). Critical before submission.
- `/novelty-check` — Verify the paper's contribution hasn't already been published
- `/de-ai-polish` — Remove AI writing patterns from the manuscript
- `/reproducibility-checklist` — Check methods completeness (NeurIPS/ICML style checklist)
- `/lay-summary` — Generate plain-language summary, tweet thread, elevator pitch
- `/compile` — Compile LaTeX to PDF and report errors
- `/status` — Progress dashboard (word counts, refs, pipeline stage)
- `/preview-pipeline` — Dry run of `/write-paper` (shows plan without executing)

### Codex Bridge (optional — adversarial AI review)
- `/codex-review` — Get a second-opinion review from OpenAI Codex (challenges assumptions, finds logical gaps)

### Submission & Archive
- `/archive` — Bundle all research artifacts into a browsable `archive/` folder with README index (auto-runs at end of /write-paper)
- `/prepare-submission` — Generate submission package (anonymized, cover letter, supplementary)
- `/clean` — Remove build artifacts and working directories

## Codex Bridge Integration

If `codex-bridge` is installed (`npm i -g codex-bridge`), it provides a second AI perspective throughout the pipeline via OpenAI Codex:

- **Research cross-check** (Stage 1c): `codex_ask` validates key findings and flags missing perspectives
- **Thesis stress-testing** (Stage 2b): `codex_plan` challenges your contribution statement before you write
- **Section spot-checks** (Stage 3): `codex_review` catches issues in each core section as it's written
- **Figure/claims audit** (Stage 4c): `codex_ask` verifies figures match their claims
- **Adversarial review** (Stage 5): `codex_review` runs alongside the 3 agent reviewers as a 4th perspective
- **Risk radar** (Post-QA): `codex_risk_radar` assesses scientific, ethical, reproducibility, and novelty risks
- **Collaboration stats** (Stage 6): `codex_stats` reports how the two AI systems worked together
- **On-demand critique**: `/codex-review` for manual review of any section

All codex integration is **graceful** — if codex-bridge is not installed or configured, every step that uses it is silently skipped. The pipeline works fine without it.

**Disagreement protocol**: If Codex disagrees with Claude's assessment, both perspectives are presented. Neither side silently wins.

## Praxis Integration

If Praxis is installed (cloned to `vendor/praxis/`), it provides domain-specific scientific data analysis:

- **50+ characterisation techniques**: XRD, DSC, TGA, FTIR, Raman, XPS, EIS, mechanical testing, AFM, SEM, VSM, BET, etc.
- **9 journal figure styles**: Nature, Science, ACS, Elsevier, Wiley, RSC, Springer, IEEE, MDPI — auto-matched to venue
- **Colourblind-safe palettes** by default
- **Technique-aware analysis**: returns domain-specific metrics (crystallite size, Tg, modulus, coercivity, etc.)

**Usage**: Read `.claude/skills/praxis/SKILL.md` for the API. Use `vendor/praxis/references/cookbook.md` for worked examples. Import via `sys.path.insert(0, "vendor/praxis/scripts")`.

**In the pipeline**: Stage 4 auto-detects data files in `attachments/` and uses Praxis for technique-specific analysis with venue-matched figures. Falls back to generic matplotlib if Praxis is not installed.

## Agent Usage Guidelines

When spawning agents for paper work:
- **Writing/revision/expansion/de-AI agents**: Use `model: "claude-opus-4-6[1m]"`. Deep reasoning and prose quality.
- **Research agents**: Run in parallel. Each writes to a separate file in `research/`. Use `model: "claude-sonnet-4-6[1m]"`.
- **Review agents**: Run in parallel. Each writes to a separate file in `reviews/`. Use `model: "claude-sonnet-4-6[1m]"`.
- **Gap analysis agent**: Uses `model: "claude-opus-4-6[1m]"` — requires deep reasoning about what's missing.
- **Bibliography, reference validation, lay summary, reproducibility, section lit searches**: Use `model: "haiku"`. Mechanical lookup and formatting tasks.
- Always include detailed, specific prompts for each agent — they have no shared context.

## File Conventions

- All `.tex` files use UTF-8 encoding
- BibTeX keys: `authorYear` format (e.g., `smith2024`)
- Figure filenames: descriptive, lowercase, hyphens (e.g., `model-architecture.pdf`)
- Prefer vector formats (PDF, EPS) for figures; PNG only for photographs/screenshots
- Float placement: use `[htbp]` not `[H]` unless absolutely necessary
