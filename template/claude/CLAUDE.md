# Research Paper Writing Agent

Scientific paper writing workspace powered by Claude Code with agent-based orchestration.

## Project Structure

```
main.tex          # Primary LaTeX document
references.bib    # BibTeX references
figures/          # Generated and imported figures
attachments/      # Reference PDFs, data files, supplementary materials
  parsed/         # Docling-parsed markdown and extracted figures (symlinks to cache)
research/         # Literature research outputs (created by /write-paper)
  sources/        # Raw source extracts per cited paper (abstract, key findings, provenance)
  source-manifest.json  # Manifest of all source artifacts (PDF, parsed md, extract, deep-read status)
  knowledge/      # LightRAG knowledge graph (auto-built from sources, gitignored)
  log.md          # Research provenance log (all searches, queries, tools, results)
  provenance.jsonl  # Machine-readable provenance ledger (every action traced)
  codex_telemetry.jsonl  # Machine-readable Codex interaction log (tool, outcome, points)
  assumptions.md    # Categorized methodological assumptions (Standard/Reasonable/Risky/Critical)
reviews/          # Review feedback (created by /write-paper)
provenance/       # Provenance audit trail (cuts archive, auto-iteration artifacts)
  cuts/           # Archived text from content that was cut (never delete without archiving)
archive/          # Browsable research archive with index (created at end of /write-paper or via /archive)
.paper.json       # Paper topic and configuration
.claude/
  commands/       # Slash commands (42 commands)
  pipeline/       # Stage-specific instructions for /write-paper and /auto (read on-demand per stage/phase)
    shared-protocols.md   # Codex deliberation, codex telemetry, provenance logging, domain detection, tool fallback
    stage-1-research.md   # Deep literature research (agents 1-12)
    stage-1b-snowballing.md   # Citation snowballing (backward + forward)
    stage-1b2-cocitation.md   # Co-citation & bibliometric analysis
    stage-1c-codex-crosscheck.md  # Codex research cross-check
    stage-1d-source-acquisition.md  # Source audit, OA resolution, acquisition
    stage-1e-deep-read.md # Deep reading of full PDFs, rewrite source extracts
    stage-1f-synthesis.md # Cross-source synthesis: conflicts, methodology critique, framework taxonomy
    stage-2-planning.md   # Thesis, outline, claims-evidence matrix
    stage-2b-codex-thesis.md  # Codex thesis stress-test
    stage-2c-targeted-research.md  # Deep mode targeted research
    stage-2d-novelty-check.md  # Novelty verification
    stage-2e-assumptions.md   # Methodological assumptions analysis
    stage-3-writing.md    # Section-by-section writing (abstract-first alignment, warrant verification, voice guidance)
    stage-3b-coherence.md # Cross-section coherence check (promise fulfillment, concept consistency, rebuttal threading)
    stage-3c-reference-integrity.md  # Reference integrity: artifact verification + misattribution detection
    stage-4-figures.md    # Figures, tables, visual elements
    stage-5-qa.md         # QA review loop
    stage-5-post-qa.md    # Post-QA audits, ref validation, risk radar
    stage-6-finalization.md  # Final polish, de-AI, provenance report
    auto-phase-1-assessment.md    # /auto Phase 1: parallel assessment agents (A-E) + Codex
    auto-phase-2-prioritization.md  # /auto Phase 2: read assessments, build action plan
    auto-phase-3-execution.md     # /auto Phase 3: targeted research + revision agent
    auto-phase-4-verification.md  # /auto Phase 4: verification, post-iteration, early stop
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
13. **Use the provided scripts and tools, not custom ones.** This system has purpose-built scripts (`scripts/parse-pdf.py`, `scripts/knowledge.py`, `scripts/pdf-cache.sh`, `scripts/format_sentences.py`, `scripts/update-manifest.py`) and pipeline stages designed to work together. Do NOT write one-off Python scripts, shell scripts, or "helper" code to replace or bypass them. Do not write custom scripts "for efficiency" or "to batch process" things. If a provided script exists for a task, use it. If no script exists, use the tools and commands as documented in the pipeline instructions. The system is built this way for a reason: scripts are shared across all paper projects via symlinks, tested in CI, and maintained centrally. A custom script in one project is a dead end that other projects cannot benefit from.

## Autonomous Pipeline: /write-paper

The primary workflow. Run `/write-paper <topic>` to launch the full pipeline:

1. **Deep Research** — Parallel agents search literature, then citation snowballing discovers papers that keyword search cannot find, then co-citation analysis identifies important papers frequently cited alongside your references but missing from the bibliography
2. **Source Acquisition** — Audit source access levels, detect source types (article/book/report/etc.), run a 14-resolver cascade (Unpaywall, OpenAlex, Semantic Scholar, CrossRef, CORE, PubMed, arXiv, DBLP, BASE, Internet Archive, DOAB, Google Books, web search, repository search) with PDF validation, then content enrichment for remaining gaps (Wikipedia, book reviews, executive summaries, citation context), pause for user to provide remaining sources
3. **Deep Source Reading** — For every source with a PDF, spawn a dedicated agent to read the full paper and rewrite the source extract with comprehensive, topic-relevant content
4. **Literature Synthesis** — Cross-source analysis: consensus/conflict mapping, methodological critique of cited work, competing framework taxonomy. Produces a unified synthesis document that informs thesis formulation
5. **Planning** — Thesis statement, contribution, detailed outline, claims-evidence matrix, novelty verification, methodological assumptions analysis
6. **Writing** — Draft abstract for alignment (default: on), then sequential agents write each section with warrant verification, voice guidance, and evidence checks. Methods states assumptions explicitly, Discussion addresses risky/critical assumptions in Limitations
7. **Cross-Section Coherence** — Full-manuscript check for promise fulfillment, concept consistency, rebuttal threading, and narrative arc. Fixes critical coherence issues before QA
8. **Reference Integrity** — Programmatic verification that every citation has backing artifacts (bib entry, source extract, content snapshot), auto-removal of fabricated references, then per-section misattribution detection by Sonnet agents cross-checking claims against source extract Content Snapshots
9. **Figures & Tables** — Ensure adequate visual elements
10. **Quality Assurance** — Parallel review agents + reference spot-checks + revision loop (up to 5 iterations). Fabricated references caught inside the loop, not after
11. **Finalization** — Polish, compile, archive all artifacts, report

This runs for 1-4 hours (standard) or 3-8 hours (deep). Two model tiers with 1M context: `claude-opus-4-6[1m]` for writing/reasoning, `claude-sonnet-4-6[1m]` for research/review/mechanical tasks. Set `depth` in `.paper.json` to `"deep"` for 3x research effort.

### Configuration: `.paper.json`

Required fields: `topic`, `depth` (`"standard"` or `"deep"`).

Optional field: `abstract_strategy` (`"first"` or `"last"`, default: `"first"`). A draft abstract is written after Stage 2 and used as an alignment tool during section writing — every writing agent checks that its section delivers on the abstract's promises. The final abstract is still rewritten after all sections are complete. Set to `"last"` to disable draft abstract alignment (not recommended).

Optional fields for source acquisition:
```json
{
  "email": "ndcorder@pm.me",
  "oa_resolution": {
    "unpaywall": true,
    "openalex": true,
    "semantic_scholar": true,
    "crossref": true,
    "core": true,
    "pubmed_central": "auto",
    "arxiv": "auto",
    "dblp": "auto",
    "base": true,
    "internet_archive": true,
    "doab": true,
    "google_books": true,
    "web_search": true,
    "repository_search": true,
    "content_enrichment": true
  }
}
```

- `email`: Used by Unpaywall (required for that API), OpenAlex, and CrossRef polite pool (increases rate limits). Also read from `UNPAYWALL_EMAIL` env var.
- `oa_resolution`: Per-resolver toggles. All default to `true` unless noted. `"auto"` resolvers are enabled based on domain detection: `pubmed_central` for biomedical, `arxiv` for CS/physics/math, `dblp` for CS. `content_enrichment` controls the Phase 2b secondary source gathering (Wikipedia, book reviews, executive summaries).
- `CORE_API_KEY` env var: Required for CORE API (free registration at core.ac.uk). Skipped if not set.
- `NCBI_API_KEY` env var: Optional. Increases PubMed rate limit from 3/s to 10/s.
- `GOOGLE_BOOKS_API_KEY` env var: Optional. Increases Google Books quota from 1000/day.

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
- `/audit-sources` — Audit source coverage: classify every reference by access level and source type, run the full 14-resolver cascade with PDF validation, enrich remaining gaps with secondary sources, generate prioritized acquisition list
- `/deep-read` — Deep-read source PDFs: spawn an agent per source to read the full paper and rewrite source extracts with comprehensive content. Also updates research files and claims matrix when run standalone.
- `/export-sources` — Export source extracts and references to the shared knowledge base (~/.research-agent/shared-sources/)
- `/import-sources` — Import relevant sources from the shared knowledge base into the current paper
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
- `/verify-references` — Run Stage 3c reference integrity check (artifact verification + misattribution detection)
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
- `/codex-telemetry` — Analyze Codex interaction patterns (agreement rates, tool usage, disagreement hotspots)

### Submission & Archive
- `/archive` — Bundle all research artifacts into a browsable `archive/` folder with README index (auto-runs at end of /write-paper)
- `/prepare-submission` — Generate submission package (anonymized, cover letter, supplementary)
- `/respond-to-reviewers` — Generate point-by-point response to peer reviewer comments with tracked changes
- `/make-slides` — Generate presentation slide deck (structured markdown with speaker notes)
- `/make-blog-post` — Generate accessible blog post for general audience
- `/make-deliverables` — Generate all deliverables in parallel (lay summary, slides, blog post)
- `/health` — Diagnose pipeline prerequisites and optional integrations (LaTeX, API keys, knowledge graph, Codex, Praxis)
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
- **Access Level**: `FULL-TEXT` (read the paper), `ABSTRACT-ONLY` (read the abstract or secondary summary), `METADATA-ONLY` (title/authors only)
- **Source Type**: `journal_article`, `book`, `book_chapter`, `conference_paper`, `technical_report`, `industry_report`, `thesis`, `grey_literature`, `web_resource`, `unknown` (fallback, treated as journal article)
- **Content Snapshot**: Verbatim or near-verbatim text that was actually accessed — the raw material behind any claims
- **Key Findings**: The pipeline's interpretation of what's relevant
- **Provenance**: Which tool found it, what query, when
- **Enrichment** (if applicable): `secondary` flag indicating content was gathered from secondary sources (Wikipedia, book reviews, publisher descriptions) rather than the original work. Enriched sources score lower than direct-access sources in the evidence matrix (0.5x ABSTRACT-ONLY base score).
- **Enrichment Sources** (if applicable): List of secondary sources used (e.g., "Wikipedia, book review in Academy of Management Review, publisher description")

The Content Snapshot is the critical field. It answers: "What did the pipeline actually read before making this claim?" If the snapshot only contains an abstract, any claims that go beyond the abstract are suspect. For enriched sources, the snapshot clearly labels content as secondary.

The `/audit-sources` command runs the full 14-resolver cascade and content enrichment, and can retroactively upgrade source coverage on existing papers.

## PDF Parsing with Docling

PDFs acquired during source acquisition are parsed to markdown using [Docling](https://github.com/docling-project/docling) for reliable full-text extraction. This solves the 20-page-per-request limit of the Read tool and produces cleaner text for agents.

**Script**: `python3 scripts/parse-pdf.py <pdf_path> [--output-dir <dir>] [--force]`

**Output**: The parsed markdown and figures are saved next to the **real** PDF. If the PDF is a symlink to the shared cache (`~/.research-agent/pdf-cache/`), outputs go to the cache so parsing happens once per PDF across all projects. The `pdf-cache.sh link` command symlinks them into `attachments/parsed/`:
- `attachments/parsed/<key>.md` — full paper text as markdown with image references (symlink to cache)
- `attachments/parsed/<key>_figures/` — extracted figures, charts, and images (symlink to cache)

PDFs stay in `attachments/` root alongside data files. Parsed derivatives live in the `parsed/` subdirectory to keep things clean.

**Integration**: The parse script is called automatically during:
- Stage 1d (after downloading, validating, and caching a PDF — then `pdf-cache.sh link` symlinks the parsed outputs)
- Stage 1e (for any PDFs not yet parsed — parses then re-links)
- `/ingest-papers` (when processing PDFs from `attachments/`)

All downstream consumers (Stage 1e deep-read agents, writing agents, knowledge graph builder) read the parsed markdown rather than the PDF directly. If Docling is not installed, agents fall back to reading the PDF with the Read tool.

**Requires**: `pip install docling`. The `/health` command checks for this dependency. Docling is optional — the pipeline works without it, but large PDFs may have incomplete extraction.

## Shared Knowledge Base

Source extracts can be shared across papers via `~/.research-agent/shared-sources/`. This avoids redundant literature research when writing multiple papers in the same domain.

- `/export-sources` — copies `research/sources/*.md` and `references.bib` entries to the shared directory, tagged with provenance (paper topic, date, project)
- `/import-sources [topic]` — searches the shared directory for sources relevant to a topic, imports matches into `research/sources/` and `references.bib`
- Stage 1 of `/write-paper` automatically checks for relevant shared sources and notifies the user

The shared knowledge base stores source extracts only (not knowledge graphs). Each extract retains provenance: which paper it came from, when it was exported, and its access level.

## Shared PDF Cache

Downloaded PDFs are cached centrally at `~/.research-agent/pdf-cache/` to avoid re-downloading the same papers across projects. Each cached PDF has a human-readable filename and a JSON metadata sidecar.

```
~/.research-agent/pdf-cache/
  smith2024.pdf      # The actual PDF
  smith2024.json     # Metadata: title, DOI, sha256, resolver, projects list
```

**How it works**: Stage 1d checks the cache before running the resolver cascade. On a cache hit, the PDF is symlinked into `attachments/` and identity-verified. On a cache miss, the resolver cascade runs as normal and newly downloaded PDFs are stored in the cache. Project-local `attachments/<key>.pdf` files are symlinks to the cache; `knowledge.py` and all other tools follow symlinks transparently.

**Deduplication**: Papers are matched by DOI (exact), sha256 (same file), or normalized title (first 80 chars). The cache key (filename) is decoupled from the project's bibtex key via symlinks, so cross-project key collisions are handled automatically.

**Helper script** (`scripts/pdf-cache.sh`):
- `lookup <doi> <title>` — find a cached PDF by DOI or title (use `-` for unknown DOI)
- `store <key> <pdf> <title> [<doi> <resolver> <url> <authors>]` — cache a PDF with metadata
- `link <cache_key> <project_dir> <local_key>` — symlink a cached PDF into a project
- `list` — show all cached PDFs
- `info <cache_key>` — show metadata for a cached PDF

**Integration**: `/export-sources` caches any local (non-symlinked) PDFs. `/import-sources` links cached PDFs when importing relevant sources.

## Knowledge Graph

Each paper can optionally have a knowledge graph built from its source extracts using LightRAG. The graph is stored in `research/knowledge/` (gitignored — rebuilds from sources).

**Build**: `python scripts/knowledge.py build` — reads all `research/sources/*.md`, Docling-parsed markdown from `attachments/parsed/*.md`, and falls back to raw PDF extraction for any PDFs without parsed markdown. Builds a queryable graph with entities and relationships using an LLM (Gemini Flash via OpenRouter) and semantic embeddings (Qwen3 8B via OpenRouter). Parsed markdown is preferred over raw PDF extraction for higher quality text. Each source is ingested once — no duplicates.

**Requires**: `OPENROUTER_API_KEY` environment variable. The knowledge graph is optional — the pipeline works without it.

**Venv**: Auto-bootstraps on first `knowledge.py` run (`.venv/` at the research-agent repo root). No manual `pip install` needed.

**OpenSearch backend** (optional): Set `LIGHTRAG_STORAGE=opensearch` to use OpenSearch instead of the default file-based storage. Start the single-node instance with `docker compose up -d` from the research-agent repo root. Per-project namespace isolation is automatic via `knowledge_namespace` in `.paper.json`, so multiple papers can share one OpenSearch instance without cross-contamination.

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
