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
  knowledge/      # LightRAG knowledge graph (auto-built from sources, gitignored)
  log.md          # Research provenance log (all searches, queries, tools, results)
  provenance.jsonl  # Machine-readable provenance ledger (every action traced)
reviews/          # Review feedback (created by /write-paper)
provenance/       # Provenance audit trail (cuts archive, auto-iteration artifacts)
  cuts/           # Archived text from content that was cut (never delete without archiving)
archive/          # Browsable research archive with index (created at end of /write-paper or via /archive)
.paper.json       # Paper topic and configuration
.claude/
  commands/       # Slash commands (30 commands)
  pipeline/       # Stage-specific instructions for /write-paper (read on-demand per stage)
    shared-protocols.md   # Codex deliberation, provenance logging, domain detection, tool fallback
    stage-1-research.md   # Deep literature research (agents 1-12)
    stage-1b-snowballing.md   # Citation snowballing (backward + forward)
    stage-1b2-cocitation.md   # Co-citation & bibliometric analysis
    stage-1c-codex-crosscheck.md  # Codex research cross-check
    stage-1d-source-acquisition.md  # Source audit, OA resolution, acquisition
    stage-2-planning.md   # Thesis, outline, claims-evidence matrix
    stage-2b-codex-thesis.md  # Codex thesis stress-test
    stage-2c-targeted-research.md  # Deep mode targeted research
    stage-2d-novelty-check.md  # Novelty verification
    stage-3-writing.md    # Section-by-section writing
    stage-4-figures.md    # Figures, tables, visual elements
    stage-5-qa.md         # QA review loop
    stage-5-post-qa.md    # Post-QA audits, ref validation, risk radar
    stage-6-finalization.md  # Final polish, de-AI, provenance report
  skills/         # -> vendor/claude-scientific-skills (177 scientific skills)
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
10. **Claims-Evidence Matrix**: Every major claim must map to specific evidence (experiment, citation, or proof) in `research/claims_matrix.md`. Each claim is scored for evidence density (base score by source access level + modifiers for citations, recency, relevance, domain) and labeled: STRONG (>= 6), MODERATE (3-5.9), WEAK (1-2.9), CRITICAL (< 1). Writing agents adjust confidence language by strength. No CRITICAL claims may survive to finalization. WEAK claims must use hedged language. The matrix also includes three argumentation columns:
    - **Warrant**: WHY the evidence supports the claim (the logical bridge). Quality rated: Sound, Reasonable, Weak, Missing, or Invalid. Claims with Missing or Invalid warrants are structural defects that must be resolved before writing.
    - **Qualifier**: Scope limitations or conditions under which the claim holds.
    - **Rebuttal**: Anticipated counterarguments and where they're addressed in the paper.
    Writing agents must ensure each major claim paragraph includes the warrant (not just citations), appropriate qualifiers, and rebuttal references. The Technical Reviewer (Stage 5) and Depth Reviewer (`/auto`) verify warrant quality. No claim may pass QA with a Missing warrant.
11. **No em dashes**: Never use em dashes (—) or en dashes (–) as punctuation. Rewrite using commas, parentheses, colons, or separate sentences. Em dashes are the single most recognizable AI writing pattern.
12. **Provenance logging**: Every agent that writes, revises, or cuts manuscript content must append entries to `research/provenance.jsonl`. See the Provenance Logging Protocol in `pipeline/shared-protocols.md`.

## Autonomous Pipeline: /write-paper

The primary workflow. Run `/write-paper <topic>` to launch the full pipeline:

1. **Deep Research** — Parallel agents search literature, then citation snowballing discovers papers that keyword search cannot find, then co-citation analysis identifies important papers frequently cited alongside your references but missing from the bibliography
2. **Source Acquisition** — Audit source access levels, attempt OA resolution, pause for user to provide paywalled PDFs if needed
3. **Planning** — Thesis statement, contribution, detailed outline, claims-evidence matrix, novelty verification
4. **Writing** — Sequential agents write each section (1000-2500 words each)
5. **Figures & Tables** — Ensure adequate visual elements
6. **Quality Assurance** — Parallel review agents + revision loop (up to 5 iterations)
7. **Finalization** — Polish, compile, archive all artifacts, report

This runs for 1-4 hours (standard) or 3-8 hours (deep). Two model tiers with 1M context: `claude-opus-4-6[1m]` for writing/reasoning, `claude-sonnet-4-6[1m]` for research/review/mechanical tasks. Set `depth` in `.paper.json` to `"deep"` for 3x research effort.

### Configuration: `.paper.json`

Required fields: `topic`, `depth` (`"standard"` or `"deep"`).

Optional fields for enhanced OA resolution:
```json
{
  "email": "user@example.com",
  "oa_resolution": {
    "unpaywall": true,
    "openalex": true,
    "semantic_scholar": true,
    "core": true,
    "pubmed_central": "auto",
    "web_search": true,
    "repository_search": true
  }
}
```

- `email`: Used by Unpaywall (required for that API) and OpenAlex (increases rate limit). Also read from `UNPAYWALL_EMAIL` env var.
- `oa_resolution`: Per-API toggles. All default to `true`. `pubmed_central` defaults to `"auto"` (enabled only for biomedical/clinical domains based on topic keywords).
- `CORE_API_KEY` env var: Required for CORE API (free registration at core.ac.uk). Skipped if not set.
- `NCBI_API_KEY` env var: Optional. Increases PubMed rate limit from 3/s to 10/s.

**Architecture**: The `/write-paper` command is a compact orchestrator that reads stage-specific instructions from `pipeline/*.md` files on-demand. Each stage file is read fresh from disk before execution, preventing context compression from degrading late-stage instructions in long-running sessions. Shared protocols (Codex deliberation, provenance logging, tool fallback) live in `pipeline/shared-protocols.md`.

After the pipeline completes, use `/auto [N]` to run additional improvement iterations. Each iteration autonomously assesses the paper, prioritizes changes (including cuts), executes improvements, and verifies no regressions. The provenance ledger (`research/provenance.jsonl`) traces every word back to its origin across both the initial pipeline and all improvement iterations.

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
- `/audit-sources` — Audit source coverage: classify every reference by access level (full-text/abstract/metadata), attempt OA resolution, generate acquisition list
- `/knowledge` — Query the per-paper knowledge graph: semantic search, contradiction detection, evidence for/against claims, entity/relationship exploration
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
- `/auto` — Run N autonomous improvement iterations on a completed paper (assess → prioritize → execute → verify)
- `/provenance` — Query the provenance ledger (trace claims, inspect paragraph history, find gaps)

### Codex Bridge (optional — adversarial AI review)
- `/codex-review` — Get a second-opinion review from OpenAI Codex (challenges assumptions, finds logical gaps)

### Submission & Archive
- `/archive` — Bundle all research artifacts into a browsable `archive/` folder with README index (auto-runs at end of /write-paper)
- `/prepare-submission` — Generate submission package (anonymized, cover letter, supplementary)
- `/clean` — Remove build artifacts and working directories

## Codex Bridge Integration

If `codex-bridge` is installed (`npm i -g codex-bridge`), it provides a second AI perspective throughout the pipeline via OpenAI Codex:

- **Independent research** (Stage 1): `codex_ask` contributes papers and findings from its own training data
- **Research cross-check** (Stage 1c): `codex_ask` validates ALL research files, not just the summary
- **Claims-evidence review** (Stage 2): `codex_ask` challenges whether evidence actually supports each claim
- **Thesis stress-testing** (Stage 2b): `codex_plan` challenges your contribution statement before you write
- **Section spot-checks** (Stage 3): `codex_review` reviews ALL sections as they're written
- **Limitations authoring** (Stage 3): `codex_review` drafts the limitations subsection from an adversarial perspective
- **Figure/claims audit** (Stage 4c): `codex_ask` verifies figures match their claims
- **Adversarial review** (Stage 5): `codex_review` runs alongside the 3 agent reviewers as a 4th perspective
- **Reference verification** (Post-QA): `codex_ask` independently verifies a sample of references
- **Risk radar** (Post-QA): `codex_risk_radar` assesses scientific, ethical, reproducibility, and novelty risks
- **Collaboration stats** (Stage 6): `codex_stats` reports how the two AI systems worked together
- **On-demand critique**: `/codex-review` for manual review of any section

All codex integration is **graceful** — if codex-bridge is not installed or configured, every step that uses it is silently skipped. The pipeline works fine without it.

**Deliberation protocol**: Codex feedback is never blindly accepted. Claude evaluates each point (AGREE / PARTIALLY AGREE / DISAGREE), pushes back with reasoning when it disagrees, and Codex gets one rebuttal. Unresolved disagreements are logged in `reviews/codex_deliberation_log.md` for the user to decide. Neither side silently wins.

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
- **Bibliography, reference validation, lay summary, reproducibility, section lit searches**: Use `model: "claude-sonnet-4-6[1m]"`. Mechanical lookup and formatting tasks.
- Always include detailed, specific prompts for each agent — they have no shared context.

## Source Extracts

Every cited paper gets a source extract file in `research/sources/<bibtexkey>.md`. These files serve as the verifiable ground truth for what the pipeline actually read.

Each source extract includes:
- **Access Level**: `FULL-TEXT` (read the paper), `ABSTRACT-ONLY` (read the abstract), `METADATA-ONLY` (title/authors only)
- **Content Snapshot**: Verbatim or near-verbatim text that was actually accessed — the raw material behind any claims
- **Key Findings**: The pipeline's interpretation of what's relevant
- **Provenance**: Which tool found it, what query, when

The Content Snapshot is the critical field. It answers: "What did the pipeline actually read before making this claim?" If the snapshot only contains an abstract, any claims that go beyond the abstract are suspect.

The `/audit-sources` command can retroactively audit and upgrade source coverage on existing papers.

## Knowledge Graph

Each paper can optionally have a knowledge graph built from its source extracts using LightRAG. The graph is stored in `research/knowledge/` (gitignored — rebuilds from sources).

**Build**: `python scripts/knowledge.py build` — reads all `research/sources/*.md` AND extracts full text from PDFs in `attachments/`, then builds a queryable graph with entities and relationships using an LLM (Gemini Flash via OpenRouter) and semantic embeddings (Qwen3 8B via OpenRouter). PDFs are ingested alongside source extracts so the graph captures the complete content of acquired papers, not just the 500-1500 word snapshots.

**Requires**: `OPENROUTER_API_KEY` environment variable. The knowledge graph is optional — the pipeline works without it.

**Commands**:
- `build` — full rebuild of the knowledge graph from all sources and PDFs
- `update` — incremental update (only ingests files newer than last build)
- `query "question"` — freeform semantic search across sources (cached)
- `contradictions` — find conflicting claims, saved to `research/knowledge_contradictions.md` (cached)
- `evidence-for "claim"` — find sources supporting a claim (cached)
- `evidence-against "claim"` — find sources challenging a claim (cached)
- `entities` — list all extracted concepts, theories, methods, etc.
- `relationships "entity"` — show how a concept connects to others
- `coverage "document.md"` — check which graph entities appear in a document, report missing entities sorted by importance

Query results are cached in `research/knowledge/.cache/` until the next build or update.

The graph is built automatically during `/write-paper` (after Stage 1d), rebuilt incrementally after Stage 2c (deep targeted research) and `/auto` iterations that add references, and queried at every stage where evidence matters: thesis validation (Stage 2), section writing (Stage 3, mandatory section-specific queries), and QA review (Stage 5, contradiction + entity coverage analysis).

## File Conventions

- All `.tex` files use UTF-8 encoding
- BibTeX keys: `authorYear` format (e.g., `smith2024`)
- Figure filenames: descriptive, lowercase, hyphens (e.g., `model-architecture.pdf`)
- Prefer vector formats (PDF, EPS) for figures; PNG only for photographs/screenshots
- Float placement: use `[htbp]` not `[H]` unless absolutely necessary
