# Research Agent

An autonomous research paper writing toolkit for Claude Code. From a topic prompt, it produces a publication-ready, journal-quality LaTeX paper through multi-agent orchestration — running for 1-4 hours (standard) or 3-8 hours (deep mode).

> **New here?** See [QUICKSTART.md](QUICKSTART.md) for the 3-minute setup.
>
> **Visual overview?** Open [docs/pipeline-diagram.html](docs/pipeline-diagram.html) in a browser.
>
> **Security model?** See [SECURITY.md](SECURITY.md). Additional docs: [Architecture](docs/ARCHITECTURE.md), [Developer Guide](docs/DEVELOPER-GUIDE.md), [Venue Reference](docs/VENUE-REFERENCE.md).

---

## Table of Contents

1. [What It Is](#1-what-it-is)
2. [Getting Started](#2-getting-started)
3. [The Full Pipeline: `/write-paper`](#3-the-full-pipeline-write-paper)
4. [The `/auto` Command](#4-the-auto-command)
5. [Provenance System](#5-provenance-system)
6. [Knowledge Graph](#6-knowledge-graph)
7. [All 35 Slash Commands](#7-all-35-slash-commands)
8. [Integrations](#8-integrations)
9. [Writing Rules](#9-writing-rules)
10. [Model Tiers](#10-model-tiers)
11. [Project Structure](#11-project-structure)
12. [Configuration Reference](#12-configuration-reference)

---

## 1. What It Is

Research Agent is a Claude Code workspace template and orchestration system that writes complete, journal-quality research papers autonomously. You provide a topic; the pipeline does the rest.

The core workflow is:

```
create-paper my-paper "LLM reasoning" --venue arxiv
cd my-paper
write-paper
```

That command sequence launches a multi-stage pipeline that:

- Runs 4-12 parallel research agents across academic databases
- Audits source access levels and pauses to let you provide paywalled PDFs
- Builds a knowledge graph from all source extracts (optional, requires OpenRouter)
- Defines a thesis, contribution statement, and claims-evidence matrix
- Verifies novelty before committing to writing
- Writes each section sequentially with dedicated Opus-tier agents
- Generates figures and tables, including venue-matched publication figures via Praxis
- Runs parallel QA review (3 agents plus optional adversarial Codex review) in a loop
- Runs post-QA consistency checks, claims audits, and reference validation
- Produces a finalized, de-AI-polished, compiled PDF with full provenance

Everything produced is traced. Every paragraph in the final paper links back to its origin: which sources informed it, which agent wrote it, what feedback revised it, and what was cut and why.

### Value proposition

| Mode | Research agents | Reference target | Estimated time | Estimated cost |
|-|-|-|-|-|
| Standard | 5 | 30-50 refs | 1-4 hours | ~$50 |
| Deep | 12 + 3 targeted-pass | 60-80 refs | 3-8 hours | ~$150 |

---

## 2. Getting Started

### Prerequisites

**Required:**
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (the `claude` CLI)
- A LaTeX distribution with `pdflatex` and `latexmk`
- Python 3.10+
- Git

**Optional:**
- `codex-bridge` (`npm i -g codex-bridge`) — adversarial AI review from OpenAI Codex throughout the pipeline
- `OPENROUTER_API_KEY` — required to build and query the knowledge graph (LightRAG via Gemini Flash and Qwen3 8B)
- `CORE_API_KEY` — free API key from [CORE](https://core.ac.uk/services/api) (200M+ institutional repository papers). Register at core.ac.uk for a free key.
- `NCBI_API_KEY` — free API key from [NCBI](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/). Increases PubMed Central rate limit from 3/s to 10/s. Only useful for biomedical/clinical papers.
- Praxis scientific analysis toolkit — auto-cloned as a submodule by `create-paper`

### Installation

Symlink the two launcher scripts to somewhere on your PATH:

```bash
git clone https://github.com/ndcorder/research-agent
cd research-agent
ln -s $(pwd)/create-paper ~/.local/bin/create-paper
ln -s $(pwd)/write-paper ~/.local/bin/write-paper
ln -s $(pwd)/sync-papers ~/.local/bin/sync-papers
```

### How updates work

Paper projects symlink their `.claude/commands/`, `.claude/CLAUDE.md`, and `scripts/` back to this repository's template. When you update the template (add a command, fix a prompt, change a writing rule), every paper project sees the change instantly.

If you have existing projects created before the symlink migration, run `sync-papers` once to convert them:

```bash
sync-papers /path/to/your/papers
```

Safe to run multiple times. Projects already using symlinks are skipped.

### Creating a new paper project

```bash
create-paper <directory> [topic] [--venue <venue>] [--deep]
```

**Examples:**

```bash
# Create a project and immediately offer to launch the pipeline
create-paper my-survey "A survey on LLM reasoning" --venue arxiv

# Create the project structure without starting (add topic later)
create-paper my-paper --venue neurips

# Deep mode: 12 agents, 60-80 refs, targeted second pass
create-paper my-paper "Protein structure prediction" --venue nature --deep
```

`create-paper` does the following in one command:
1. Creates the project directory
2. Generates a `main.tex` formatted for the target venue
3. Copies all 35 slash commands into `.claude/commands/`
4. Writes `.paper.json` and `.venue.json`
5. Clones 177 scientific skills as a git submodule (`vendor/claude-scientific-skills`)
6. Clones Praxis as a git submodule (`vendor/praxis`) and installs Python dependencies
7. Initializes `codex-bridge` if it is installed
8. Creates the initial git commit
9. Verifies LaTeX compilation

### Launching the pipeline

From inside the paper project:

```bash
# Method 1: the write-paper launcher script (recommended)
write-paper                      # uses topic from .paper.json
write-paper "new topic"          # overrides topic

# Method 2: through Claude Code interactively
claude
# then type: /write-paper A survey on LLM reasoning
```

The `write-paper` launcher calls `claude "/write-paper $TOPIC"`. The pipeline operates without per-tool confirmations because `.claude/settings.local.json` contains a scoped allowlist that pre-approves every tool the pipeline uses. Tools not on the allowlist (e.g., `git push`, arbitrary shell commands) still prompt for confirmation.

### Monitoring a running pipeline

The pipeline writes a human-readable progress file you can watch from another terminal:

```bash
cat .paper-progress.txt          # current stage, section word counts
ls research/                     # research files as they appear
ls reviews/                      # review files during QA
```

### Available venues

| Flag | Format | Citation style | Page limit |
|-|-|-|-|
| `generic` | Standard article (default) | natbib (`\citep`, `\citet`) | none |
| `ieee` | IEEEtran two-column | numeric | 8 pages |
| `acm` | acmart sigconf, double-blind | natbib | 12 pages |
| `neurips` | NeurIPS single-column | natbib | 9 pages |
| `nature` | Nature family — Results before Methods | numeric superscript | none |
| `arxiv` | arXiv preprint, extended format | natbib | none |
| `apa` | APA 7th edition | apacite | none |

Each venue JSON also includes a `writing_guide` field with venue-specific tone, structure, citation density, figure count, and reviewer expectation guidance. Writing agents read the guide to match the conventions of the target venue.

---

## 3. The Full Pipeline: `/write-paper`

Run with `/write-paper <topic>` inside a Claude Code session, or via the `write-paper` launcher. The pipeline reads `.paper.json` for topic, venue, and depth, then executes the following stages sequentially.

### Checkpoint and resume

After completing each stage or section, the pipeline writes `.paper-state.json` tracking exactly which stages and sections are done. If the session is interrupted, rerunning `/write-paper` reads this file and skips completed work. Partial stage recovery tracks sub-steps within stages (individual research agents, individual sections) so a crash mid-stage resumes from the last completed sub-step, not the start of the stage. `.paper-progress.txt` is updated at each checkpoint with a human-readable summary.

### Stage 1: Deep Literature Research

**Goal:** 30-50 verified references (standard) or 60-80 (deep mode) covering the field comprehensively.

Before spawning agents, the pipeline detects the paper's domain from the topic keywords (Biomedical, Chemistry, CS/AI, Physics, Materials Science, Ecology, Economics, Clinical, or General). This determines which scientific skill databases are prioritized.

**Standard mode: 5 agents in parallel**

| Agent | Task | Output file |
|-|-|-|
| Field Survey | 10-15 most influential papers, major research threads, recent breakthroughs | `research/survey.md` |
| Methodology Deep Dive | Major methodological approaches, state-of-the-art, standard benchmarks | `research/methods.md` |
| Empirical Evidence | Standard benchmarks, datasets, SotA results, reproducibility concerns | `research/empirical.md` |
| Theoretical Foundations | Formal definitions, theorems, connections to broader frameworks | `research/theory.md` |
| Gap Analysis | Research gaps, promising directions, proposed thesis and contribution | `research/gaps.md` |

The Gap Analysis agent (Agent 5) runs AFTER the first four complete, because it reads all their output.

**Deep mode: 7 additional agents in parallel (with agents 1-4)**

| Agent | Task | Output file |
|-|-|-|
| Recent Frontiers | Papers published 2024-2026 only, emerging trends | `research/recent_frontiers.md` |
| Negative Results | What didn't work, failed approaches, replication failures | `research/negative_results.md` |
| Cross-Disciplinary | Insights from adjacent fields | `research/cross_disciplinary.md` |
| Datasets & Reproducibility | All standard datasets, open-source implementations | `research/datasets_reproducibility.md` |
| Industry & Applied | Deployed systems, patents, gap between academic and production | `research/industry_applied.md` |
| Competing Hypotheses | Active scientific debates, schools of thought | `research/competing_hypotheses.md` |
| Intellectual Lineage | Seminal papers, how ideas evolved, paradigm shifts | `research/intellectual_lineage.md` |

**Tool fallback chain:** Every research agent is instructed to try tools in this order: domain-specific database skills (PubMed, arXiv, etc.) → Perplexity search → WebSearch → Firecrawl search → WebFetch on known URLs → research-lookup skill. Agents must try at least 3 different tools before giving up on a query.

**Codex independent contribution:** After all Claude research agents complete, Codex is called to independently suggest papers Claude may have missed, drawing on its own training data. Its suggestions are verified for existence before being passed to the bibliography builder.

**Bibliography builder (haiku model):** Reads all research files, extracts every cited paper, verifies each against CrossRef or search, generates BibTeX entries, and writes `references.bib`. If fewer than 25 references result (standard) or 50 (deep), additional targeted research agents are spawned for underrepresented areas.

**Research log:** After every tool call (success or failure), agents append an entry to `research/log.md` recording timestamp, agent name, tool used, exact query, result, and any URLs or DOIs found. This log is the complete provenance trail of all literature searches.

**Source extracts:** For every cited paper, the agent creates `research/sources/<bibtexkey>.md` recording the access level (FULL-TEXT, ABSTRACT-ONLY, or METADATA-ONLY), the actual content that was read (verbatim or near-verbatim — not a summary), key findings, and provenance.

---

### Stage 1c: Codex Research Cross-Check

A standalone stage that reads every research file and calls Codex to cross-check each one's major claims: are they accurately represented? Are there contradicting studies or missing nuances? Are key papers overlooked?

If Codex identifies missing perspectives or inaccurate claims, a targeted follow-up research agent investigates those specific gaps. All Codex feedback and Claude's evaluations are logged to `research/codex_cross_check.md`.

This stage is **non-skippable**. The pipeline verifies the file exists before proceeding.

---

### Stage 1d: Source Coverage Audit and Acquisition

**Goal:** Ensure every cited source has a verifiable content snapshot before writing begins.

**Phase 1 — Audit:** Every BibTeX key is matched against `research/sources/`. Each paper is classified as FULL-TEXT, ABSTRACT-ONLY, or METADATA-ONLY based on its source extract file.

**Phase 2 — Automated OA resolution:** For each ABSTRACT-ONLY and METADATA-ONLY source, the pipeline attempts to find a free full-text copy:
1. Semantic Scholar API — checks the `openAccessPdf` field
2. Web search for a direct PDF URL (arXiv, bioRxiv, SSRN, ResearchGate, etc.)
3. Academic repository search — notes URLs even if a login is required

Each successfully resolved paper has its source extract upgraded to FULL-TEXT with a new content snapshot.

**Phase 3 — Human acquisition (human-in-the-loop):** After automated resolution, if papers still lack full text, the pipeline pauses and presents a prioritized acquisition list sorted by how many times each paper is cited in the research files. In standard mode it presents the top 5; in deep mode it presents all abstract-only and metadata-only papers. The user can drop PDFs into `attachments/` and reply "continue", or reply "skip" to proceed with abstract-level sources (which get flagged in the claims-evidence matrix).

**Phase 4 — Coverage report:** `research/source_coverage.md` is written with final counts by access level.

---

### Knowledge Graph Build

Immediately after Stage 1d, the pipeline attempts to build a LightRAG knowledge graph:

```bash
python scripts/knowledge.py build
```

This reads all `research/sources/*.md` files, extracts entities (papers, theories, methods, findings, authors) and relationships (cites, contradicts, supports, extends), and builds a queryable graph with semantic embeddings. The graph is stored in `research/knowledge/` (gitignored).

If `scripts/knowledge.py` is not found or `OPENROUTER_API_KEY` is not set, this step is silently skipped. The pipeline works without the knowledge graph; agents fall back to reading research files directly.

---

### Stage 2: Thesis, Contribution, and Outline

With all research complete, the pipeline:

1. **Defines the thesis and contribution** in `research/thesis.md` — the specific problem, the novel contribution, and the key claims.

2. **Determines paper structure** from the topic type and venue. Nature-family papers get Results before Methods. IEEE and ACM papers get tighter sections to respect page limits. Survey papers use thematic analysis sections rather than IMRAD.

3. **Creates the detailed outline** in `main.tex` — all sections and subsections with `% OUTLINE:` comments containing the key arguments, planned citation keys, figure plans, and word targets per section.

4. **Builds the Claims-Evidence Matrix** in `research/claims_matrix.md`. Every major claim the paper will make is listed with: the type of evidence supporting it (experiment, citation, formal proof, or data), which section will present it, and whether the supporting sources are FULL-TEXT or ABSTRACT-ONLY. Claims backed only by abstract-level sources are flagged with a warning.

5. **Codex stress-tests the claims-evidence matrix** — checking whether evidence is actually sufficient for each claim, whether any claims are too strong for the evidence type, and whether obvious claims are missing.

6. **Logs planning provenance** — entries in `research/provenance.jsonl` for the thesis selection, section structure decisions, and each claim's evidence strategy.

---

### Stage 2b: Codex Thesis Stress-Test

A standalone stage that calls `codex_plan` to challenge the paper plan before any writing begins:

- Is the contribution genuinely novel given the related work?
- Is the argument structure sound?
- What will reviewers attack?
- Are there missing sections or weak links?

Results go to `research/codex_thesis_review.md`. If Codex identifies structural problems, they are fixed in the outline before proceeding.

---

### Stage 2c: Targeted Second Research Pass (deep mode only)

Only runs when `depth` is `"deep"`. Now that the thesis and claims are finalized, three agents run a surgical second research pass:

| Agent | Task | Output file |
|-|-|-|
| Supporting Evidence | 3-5 papers providing direct evidence for each key claim | `research/targeted_support.md` |
| Counterarguments | Papers that contradict or challenge the claims, strongest reviewer objections | `research/targeted_counter.md` |
| Methodological Precedents | Papers using similar methods, known limitations, best practices | `research/targeted_methods.md` |

The bibliography builder runs again after to incorporate new references.

---

### Stage 2d: Novelty Verification

A standalone stage that searches for existing work making the same contribution before writing begins. This catches the worst case: investing hours in writing a paper that already exists.

The pipeline searches arXiv, Semantic Scholar, domain-specific databases, and (if available) calls Codex to check its own training data. Results are classified:

- **NOVEL** — proceed
- **PARTIALLY NOVEL** — document the distinction, update thesis to clarify, add similar papers to Related Work
- **NOT NOVEL** — halt the pipeline and report to the user with the conflicting papers

Results are written to `research/novelty_check.md`.

---

### Stage 3: Section-by-Section Writing

Each section gets its own dedicated Opus-tier agent running sequentially. Writing is sequential (each section can reference prior ones); research and review are parallel.

**Deep mode per-section literature searches:** Before each writing agent, a haiku-tier agent quickly searches for literature specific to that section's topics and writes a targeted reference list to `research/section_lit_[section].md`. The writing agent then reads this alongside the main research files.

**Writing order and targets:**

| Order | Section | Key guidance |
|-|-|-|
| 1 | Introduction | Broad context → specific problem → contribution → findings preview → paper organization. 8-12 citations. |
| 2 | Related Work | Organize thematically in 3-5 subsections. 3-5 papers per theme. Explicit positioning of this work. 15-20 citations. |
| 3 | Methods/Approach | Exhaustive: full detail for reproduction, math in equation/align environments, pseudocode if applicable, design rationale. |
| 4 | Results/Experiments | Setup → quantitative results (tables) → ablations → qualitative analysis. At least 2 booktabs tables. |
| 5 | Discussion | Interpret findings, compare with prior work, limitations (written honestly), broader implications, future work. |
| 6 | Conclusion | Concise. Restate problem, summarize approach, highlight key results with numbers. No new information. |
| 7 | Abstract | Written last, reads the full paper first. Specific, quantitative, self-contained. |

**Codex-authored Limitations:** After the Discussion section is written, Codex drafts the Limitations subsection from an adversarial perspective (methodological assumptions, data limitations, scope limitations, threats to validity). Claude evaluates each point, pushes back where warranted, and the Discussion agent integrates the agreed-upon content.

**After each section:** Claude assesses whether the section is substantively complete. If it is thin, missing citations, or leaving obvious gaps, an expansion agent (Opus tier) adds depth. Then Codex does a quick spot-check of the section for logic, evidence proportionality, and gaps. In deep mode, Codex also identifies substantive content gaps for a further expansion round.

**Knowledge graph queries:** If the knowledge graph exists, each writing agent queries it for section-specific evidence, checks for contradictions, and ensures comprehensive coverage using the CLI commands.

**Provenance logging:** After writing each paragraph, the agent appends a provenance entry to `research/provenance.jsonl` recording the paragraph target (`section/pN`), which source extracts informed it, which claims it supports, and a reasoning field explaining the writing choices.

---

### Stage 4: Figures, Tables, and Visual Elements

**Step 4a — Data-driven figures with Praxis (if available):**

If `vendor/praxis/scripts/` exists and `attachments/` contains data files, a data analysis agent auto-detects the characterisation technique and runs Praxis analysis:

```python
import sys
sys.path.insert(0, "vendor/praxis/scripts")
# venue-matched style, colourblind-safe palette, technique-specific metrics
apply_style("<venue_style>")
set_palette("okabe_ito")
```

Figures are exported as PDF to `figures/`, scripts are saved to `figures/scripts/` for reproducibility, and quantitative results are inserted into the Results and Methods sections of `main.tex`.

If Praxis is not installed but data files exist, the pipeline falls back to generic matplotlib using the matplotlib skill.

**Step 4b — Structural figures and tables:**

A visualization agent ensures the paper has:
- At least one overview or architecture figure (TikZ or described in a figure environment)
- At least two booktabs-formatted tables
- All figures and tables referenced in text before they appear
- Descriptive captions (2-3 sentences explaining what is shown and why it matters)

**Step 4c — Codex figure and claims audit:**

Codex audits whether captions accurately describe what is shown, whether surrounding text claims match what the data actually shows, and whether there are misleading axis scales, cherry-picked comparisons, or missing error bars.

---

### Stage 5: Quality Assurance Loop

This stage loops until all quality criteria pass, up to 5 iterations (standard) or 8 (deep mode). Stale review files are deleted before each iteration so reviewers evaluate the latest version.

**Step 5a — Parallel review (3 agents):**

| Reviewer | Focus |
|-|-|
| Technical Reviewer | Claims supported by evidence, methodology sound and reproducible, results properly analyzed, argument coherent Introduction to Conclusion |
| Writing Quality Reviewer | No bullet points in body text, every paragraph complete, transitions smooth, terminology consistent, tense correct, section word counts |
| Citation and Completeness Reviewer | All citation keys exist in .bib, uncited claims flagged, no placeholder text, all cross-references resolve, LaTeX compilation |

**Step 5a-ii — Codex adversarial review (parallel with agents):**

While the 3 review agents run, Codex is called directly as a 4th adversarial reviewer:

> You are an adversarial peer reviewer. Find the weakest points: claims that exceed the evidence, logical gaps in the argument chain, methodological shortcuts, missing baselines or unfair comparisons, conclusions that don't follow from results.

Result goes to `reviews/codex_adversarial.md`. The pipeline verifies all 4 review files exist before proceeding.

**Step 5b — Synthesize:** All review files are read and a prioritized fix list is built (CRITICAL first, then MAJOR, word count shortfalls, missing citations).

**Step 5c — Revision agent (Opus tier):** Fixes every critical and major issue, expands thin sections with substantive content, adds verified citations, and compiles. Content that should be removed is cut, with the removed text archived in `provenance/cuts/`.

**Step 5d — Quality gate:** All criteria in the table below must pass. If any fail, loop back to Step 5a. In deep mode, after the final passing iteration, Codex does one additional deep review looking for subtle issues that earlier reviews missed.

**Quality gate criteria:**

| Criterion | Requirement |
|-|-|
| Sections substantively complete | No obvious gaps, thin arguments, or missing depth |
| Claims-Evidence Matrix | Every claim has status "Supported" |
| References in .bib | 25+ verified entries |
| Placeholder text | Zero (no TODO/TBD/FIXME/lipsum) |
| LaTeX compilation | No errors |
| Tables | 2+ with booktabs |
| Cross-references | All `\ref{}` resolve |
| Citation keys | All `\citep{}`/`\citet{}` exist in .bib |
| Body text | Full paragraphs only, no bullet points |

---

### Post-QA: Consistency and Claims Audit

After the QA loop exits (all criteria met), two final audits run in parallel:

**Consistency Checker:** Finds and fixes notation inconsistencies, terminology drift, abbreviations defined twice or used before definition, tense inconsistencies, and reference format inconsistencies (Figure vs Fig., Section vs Sec.).

**Claims Auditor:** Flags overclaims — "novel"/"first" without evidence, "significantly" without a statistical test, "prove"/"demonstrate" with only experiments, unsupported factual claims, generalizations from limited experiments. Critical and major overclaims are softened in `main.tex`.

After both complete, a **Reproducibility Checker (haiku tier)** verifies that Methods includes all hyperparameters, training details, compute resources, dataset descriptions, evaluation metric definitions, and random seed/variance information.

---

### Post-QA: Reference Validation

A reference validation agent (haiku tier) verifies every BibTeX entry is a real publication:

1. If DOI present: verify via CrossRef API
2. If no DOI: search for exact title via Perplexity or web search
3. Classify each entry: VERIFIED, METADATA MISMATCH, SUSPICIOUS, or FABRICATED
4. Fix metadata mismatches directly in `references.bib`
5. Remove FABRICATED entries from `references.bib` and their citations from `main.tex`

In parallel, Codex independently verifies a random sample of 10-15 references. If Codex flags a reference that Claude's validator marked as verified, both findings are investigated further.

This stage is **non-negotiable**. Fabricated references are the primary risk in AI-assisted writing.

---

### Post-QA: Codex Risk Radar

Codex's `codex_risk_radar` tool assesses the complete manuscript across five dimensions:

| Dimension | Description |
|-|-|
| Scientific risk | Claims that could be proven wrong or are unfalsifiable |
| Ethical risk | Data handling, consent, bias, or dual-use concerns |
| Reputational risk | Anything that could embarrass the authors under scrutiny |
| Reproducibility risk | Whether an independent team could reproduce the results |
| Novelty risk | Whether the contribution is incremental enough for desk rejection |

Each dimension is rated LOW / MEDIUM / HIGH. HIGH-risk items must be addressed before finalization. MEDIUM-risk items are flagged for the user.

---

### Stage 6: Finalization

**Final polish (Opus tier):** Reviews the complete manuscript end-to-end: abstract accuracy, title specificity, introduction's paper-organization paragraph matching actual sections, conclusion referencing actual results with numbers, redundancies removed, formatting consistent.

**Lay summary (haiku tier):** Generates a 200+ word plain-language summary (high school reading level) and a 2-3 sentence elevator pitch, written to `research/summaries.md`. If the venue requires a lay summary (Nature, medical journals), it is added to `main.tex`.

**De-AI polish (Opus tier):** Scans for and removes AI writing patterns:

- Filler phrases: "it is worth noting that", "it should be noted", "in the realm of"
- AI vocabulary: "delve", "tapestry", "multifaceted", "leverage", "utilize", "elucidate", "paradigm"
- Formulaic transitions: "Furthermore,", "Moreover,", "Additionally," at sentence starts
- Redundant phrasing: "in order to", "a total of", "the fact that", "due to the fact that"
- Empty emphasis: "significantly", "notably", "remarkably", "dramatically" without quantification
- Em dashes and en dashes used as punctuation (the single most recognizable AI writing tell)
- Uniform paragraph length (all paragraphs the same length signals AI generation)

**Provenance report (haiku tier):** Reads the complete `research/provenance.jsonl` and generates `research/provenance_report.md` — a human-readable report of every action taken, organized by section and stage, with paragraph-level histories.

**Archive:** The `/archive` command runs automatically to bundle all artifacts into a browsable `archive/` directory with an indexed `README.md`.

**Codex collaboration stats:** `codex_stats` is called to report how the two AI systems collaborated throughout the pipeline.

---

## 4. The `/auto` Command

After the pipeline completes, `/auto` runs additional autonomous improvement iterations on the finished paper. It does not re-run the pipeline — it improves what exists.

```bash
/auto            # run 1 iteration
/auto 3          # run 3 iterations
/auto --continue # resume from last completed iteration
```

Each iteration runs a 4-phase cycle. Like `/write-paper`, `/auto` uses the split-phase pattern: each phase reads its instructions from a dedicated file in `pipeline/` (`auto-phase-1-assessment.md` through `auto-phase-4-verification.md`) to avoid context degradation in long sessions.

### Phase 1: Assessment (4 parallel agents)

| Agent | Focus |
|-|-|
| Depth and Evidence | Which arguments are thin, which claims need stronger evidence, logical leaps, redundant paragraphs that should be cut |
| Structure and Flow | Argument flow between sections, disproportionate sections, reordering opportunities, front-loading of key insights |
| Competitive Positioning | Differentiation from closest prior work, fairness of comparisons, missing recent papers (2024-2026), field familiarity |
| Writing and Polish | Em dashes, AI writing patterns, sentence length variety, vague statements, over- or under-claiming |

Codex also runs in parallel (if available) to identify the 5 highest-impact improvements with fresh eyes.

### Phase 2: Prioritize

All assessment files are read, similar findings are deduplicated, and the top 5 actions for this iteration are selected by impact. Actions are a deliberate mix of strengthening, cutting, structural improvements, and polish. If 3 or fewer meaningful actions are found across all reviewers, early stop is triggered immediately.

The action plan is written to `reviews/auto_iter[N]_plan.md` with each action typed, targeted to a specific location, and annotated with whether research is needed.

### Phase 3: Execute

**Research phase (max 3 queries):** If any selected action requires new evidence, a targeted research agent runs up to 3 searches.

**Revision phase (Opus tier):** Executes every action in the plan. For cuts, the removed text is saved to `provenance/cuts/[section]-[pN]-auto[N].tex` before deletion. After all changes, LaTeX is compiled and errors are fixed.

### Phase 4: Verify

A lightweight verification agent confirms:
- LaTeX compiles without errors
- All citation keys exist in `.bib`
- All `\ref{}` cross-references resolve
- No placeholder text remains
- No bullet points in body text
- No em dashes used as punctuation
- Changes did not break surrounding context
- No new AI writing patterns were introduced

### Early stop on diminishing returns

If `changes_made < 3` after an iteration, the loop stops. The paper has stabilized; additional iterations would introduce noise rather than improvement. This is logged explicitly as a success condition.

### Rules

- Never touch the thesis (contribution statement in `research/thesis.md` is fixed)
- Cuts are first-class improvements — every assessment agent must consider what to remove
- Maximum 3 research queries per iteration
- Every change is logged to `research/provenance.jsonl` with `iteration: N`
- Every cut is archived in `provenance/cuts/`

---

## 5. Provenance System

Every word in the final paper is traceable. The provenance system consists of two components: the machine-readable ledger and the human-readable report.

### The provenance ledger

`research/provenance.jsonl` is an append-only log of every action taken during both the initial pipeline and all `/auto` iterations. One JSON object per line.

**Entry schema:**

```json
{
  "ts": "2026-03-24T14:32:11Z",
  "stage": "3",
  "agent": "section-writing-methods",
  "action": "write",
  "target": "methods/p3",
  "reasoning": "Establishes the core architectural choice — why attention over convolution — citing smith2024 for the theoretical motivation and jones2023 for empirical evidence of the trade-off in this regime.",
  "sources": ["smith2024", "jones2023"],
  "claims": ["C2"],
  "feedback_ref": null,
  "diff_summary": null,
  "iteration": 0
}
```

**Required fields:** `ts`, `stage`, `agent`, `action`, `target`, `reasoning`

**Conditional fields:**
- `sources` — BibTeX keys informing this action (required for `write`, `add`, `expand`)
- `claims` — claim IDs from the claims matrix this action supports
- `feedback_ref` — pointer to the review feedback that triggered this action (required for `revise` and `cut` during QA)
- `diff_summary` — one-line description of what changed (required for `revise`, `cut`, `expand`)
- `archived_to` — path where cut content is saved (required for `cut`)
- `iteration` — 0 for the initial pipeline, 1+ for `/auto` iterations

**Actions:** `write`, `revise`, `cut`, `add`, `expand`, `reorder`, `research`, `plan`

**Paragraph targeting:** `[section]/p[N]` (e.g., `introduction/p1`, `methods/p5`). For subsections: `methods/training-procedure/p2`. For splits: `methods/p3a` and `methods/p3b`.

### Cut archiving

Whenever content is removed from `main.tex`, it is first saved to `provenance/cuts/[section]-[pN]-[context].tex`. The provenance entry for the cut records the `archived_to` path. Content is never deleted without archiving.

### The `/provenance` query command

Query the provenance ledger interactively:

| Query form | What it returns |
|-|-|
| `/provenance` | Full summary: total actions by type, coverage (which paragraphs are traced), source utilization |
| `/provenance methods` | Provenance for every paragraph in the Methods section: who wrote it, sources, reasoning, revision history |
| `/provenance trace C3` | Full chain for claim C3: which paragraphs support it, what sources provide evidence, writing reasoning, any revisions |
| `/provenance history methods/p3` | Complete history of one paragraph: original writing, every revision with feedback reference |
| `/provenance sources smith2024` | Every place smith2024 was used: which paragraphs, what content, whether for claims, background, or methodology |
| `/provenance gaps` | Paragraphs with no provenance entry, claims with no linked provenance, sources never referenced in provenance |
| `/provenance timeline` | Chronological view of all actions; add a stage name to filter |

### The provenance report

At the end of Stage 6 and after each `/auto` run, `research/provenance_report.md` is generated as a human-readable summary of the entire provenance ledger, organized by section with paragraph-level histories, a cuts archive section, and a list of any untraced content.

---

## 6. Knowledge Graph

An optional LightRAG-based knowledge graph built from source extracts. It enables semantic search across all sources, contradiction detection, and claim-level evidence queries.

### Building the graph

```bash
export OPENROUTER_API_KEY=your-key
python scripts/knowledge.py build
```

Reads all `research/sources/*.md` files, extracts entities and relationships using Gemini Flash (via OpenRouter), and builds a queryable graph with Qwen3 8B semantic embeddings. Stored in `research/knowledge/` (gitignored — rebuilds from sources).

The pipeline builds the graph automatically after Stage 1d if the prerequisites are met.

### Query commands

```bash
python scripts/knowledge.py query "how do transformer architectures handle long sequences?"
python scripts/knowledge.py contradictions
python scripts/knowledge.py evidence-for "attention is more parameter-efficient than convolution"
python scripts/knowledge.py evidence-against "scaling laws hold at all model sizes"
python scripts/knowledge.py entities
python scripts/knowledge.py relationships "attention mechanism"
```

| Command | Output |
|-|-|
| `query "question"` | Freeform semantic search; synthesized answer with source citations |
| `contradictions` | Conflicting claims across sources; saved to `research/knowledge_contradictions.md` |
| `evidence-for "claim"` | Sources and findings supporting the claim |
| `evidence-against "claim"` | Sources and findings challenging or contradicting the claim |
| `entities` | All extracted concepts, theories, methods, papers, authors grouped by type |
| `relationships "entity"` | How a concept connects to other entities in the graph |

The `/knowledge` slash command wraps these operations interactively. If the graph does not exist, it offers to build it.

---

## 7. All 35 Slash Commands

### Autonomous pipeline

| Command | Description |
|-|-|
| `/write-paper <topic>` | Full autonomous pipeline: research → outline → writing → figures → QA → finalization. 1-4 hours standard, 3-8 hours deep. |
| `/auto [N]` | Run N improvement iterations on a completed paper (default 1). Use `--continue` to resume. |
| `/preview-pipeline` | Dry run of `/write-paper` — shows each stage, what will RUN vs SKIP, model selections, time estimate. Executes nothing. |
| `/status` | Progress dashboard: word counts per section vs targets, reference count, figure count, pipeline stage, LaTeX compilation status. Also writes `.paper-progress.txt`. |

### Research and references

| Command | Description |
|-|-|
| `/search-literature <query>` | Find relevant papers for a topic using the domain-appropriate skill databases and tool fallback chain. |
| `/add-citation <DOI or title>` | Add a properly formatted BibTeX entry to `references.bib` after verifying the paper exists. |
| `/ingest-papers` | Import PDFs from `attachments/`, extract metadata and content snapshots, generate BibTeX entries, write source extracts. |
| `/cite-network` | Analyze citation patterns: distribution by section and year, temporal coverage, venue diversity, author diversity, orphan detection, gap identification with suggested additions. |
| `/ask <question>` | Query research artifacts to answer questions. Searches `research/sources/`, `research/`, `reviews/`, `main.tex`, `references.bib`, and `research/log.md`, providing the provenance trail for each answer. |
| `/knowledge [operation]` | Interact with the LightRAG knowledge graph: query, contradictions, evidence-for, evidence-against, entities, relationships. Builds the graph if needed. |
| `/export-sources` | Export source extracts and references to the shared knowledge base (`~/.research-agent/shared-sources/`) for reuse across papers. |
| `/import-sources [topic]` | Import relevant sources from the shared knowledge base into the current paper. Uses `.paper.json` topic if omitted. |
| `/audit-sources` | Retroactive source coverage audit: classifies all references by access level, attempts OA resolution for abstract-only sources, generates acquisition list. Standalone version of Stage 1d. |

### Writing

| Command | Description |
|-|-|
| `/init <topic>` | Quick single-pass paper generation without the full multi-stage pipeline. Useful for drafts or shorter documents. |
| `/outline <section>` | Generate a structured outline for a specific section with key arguments, planned citations, and subsection organization. |
| `/revise-section <section>` | Rewrite a section based on provided feedback, maintaining consistency with the rest of the paper. |

### Quality and build

| Command | Description |
|-|-|
| `/review` | Comprehensive manuscript quality review covering technical soundness, writing quality, and citation completeness. |
| `/check-consistency` | Find and fix notation inconsistencies, terminology drift, abbreviations used before definition or defined twice, and reference format inconsistencies. |
| `/audit-claims` | Flag overclaims — "novel"/"first" without evidence, "significantly" without statistical tests, "prove" based only on experiments, unsupported factual claims. |
| `/validate-references` | Verify every citation via CrossRef API or search, fix metadata mismatches, remove fabricated entries, attempt OA resolution for newly verified papers. |
| `/novelty-check [contribution]` | Verify the paper's contribution hasn't been published. Uses multiple databases plus Codex cross-model verification. Returns NOVEL, PARTIALLY NOVEL, or NOT NOVEL. |
| `/de-ai-polish [section]` | Remove AI writing patterns across 7 categories: filler phrases, AI vocabulary, formulaic transitions, redundant phrasing, empty emphasis, em dashes, structural tells. |
| `/reproducibility-checklist` | Check Methods completeness against a structured checklist (general scientific, ML-specific if applicable, ethical considerations). Reports YES/NO/N/A per item with section references. |
| `/codex-review [section]` | On-demand adversarial review from OpenAI Codex via `codex_plan`, `codex_review`, and `codex_ask`. Requires codex-bridge. |
| `/health` | Diagnose pipeline prerequisites and optional integrations (LaTeX, API keys, knowledge graph, Codex, Praxis). Reports status, detail, and impact for each check. |
| `/compile` | Compile LaTeX to PDF via `latexmk -pdf -interaction=nonstopmode main.tex` and report errors. |

### Analysis

| Command | Description |
|-|-|
| `/analyze-data <file>` | Statistical analysis on datasets in `attachments/`, generate publication figures via matplotlib or Praxis. |
| `/praxis-analyze [file or technique]` | Technique-specific analysis via Praxis (auto-detects from data): XRD, DSC, TGA, FTIR, Raman, XPS, EIS, mechanical testing, VSM, UV-Vis, BET, and more. Venue-matched journal figure styles. |

### Provenance

| Command | Description |
|-|-|
| `/provenance [mode]` | Query the provenance ledger. Modes: summary (default), section name, `trace <claim-id>`, `history <target>`, `sources <bibtex-key>`, `gaps`, `timeline [stage]`. |

### Output and submission

| Command | Description |
|-|-|
| `/lay-summary` | Generate a 200+ word plain-language summary, a 2-3 sentence elevator pitch, and (where required by venue) a lay summary for inclusion in the manuscript. |
| `/archive` | Bundle all research artifacts into a browsable `archive/` directory with a README index. Auto-runs at the end of `/write-paper`. |
| `/prepare-submission` | Generate submission package: anonymized version (for blind-review venues), camera-ready version, cover letter, response to reviewers (if reviews exist), and a submission checklist. |
| `/respond-to-reviewers` | Generate a structured point-by-point response to peer reviewer comments with tracked changes in the manuscript. |
| `/prisma-flowchart` | Generate a PRISMA 2020 flowchart from the research log and add it to the manuscript. |
| `/clean` | `latexmk -c` to remove LaTeX build artifacts. Add `all` argument to also remove `research/`, `reviews/`, `archive/`, and pipeline state files (never removes `main.tex`, `references.bib`, `figures/`, `attachments/`, `.paper.json`, `.venue.json`). |

---

## 8. Integrations

### Codex Bridge (optional adversarial AI review)

Install with `npm i -g codex-bridge`. When present, `create-paper` auto-configures it via `codex-bridge init`. All integration is graceful — if not installed, every step that uses it is silently skipped.

Codex (OpenAI) contributes at 10 points in the pipeline:

| Pipeline point | What Codex does |
|-|-|
| Stage 1 (after research agents) | Independent literature contribution — papers Claude may have missed |
| Stage 1c | Cross-checks every research file for inaccurate representations or missing nuances |
| Stage 2 (claims-evidence matrix) | Challenges whether evidence actually supports each claim |
| Stage 2b | Stress-tests the contribution statement and argument structure |
| Stage 3 (Limitations) | Drafts the Limitations subsection from an adversarial perspective |
| Stage 3 (each section) | Quick spot-check after each writing agent; in deep mode, also identifies content gaps |
| Stage 4c | Audits whether figures and surrounding text claims match |
| Stage 5 | Adversarial peer review as a 4th parallel reviewer |
| Post-QA | Independent reference verification of a random sample |
| Post-QA | Risk radar assessment across 5 dimensions |
| Stage 6 | Collaboration statistics report |

**Deliberation protocol:** Codex feedback is never blindly accepted. For every Codex interaction, Claude evaluates each point as AGREE, PARTIALLY AGREE, or DISAGREE, with explicit reasoning. On DISAGREE, Claude sends a rebuttal with specific counterarguments. Codex gets one response. If still unresolved, both perspectives are logged in `reviews/codex_deliberation_log.md` for the user to decide. Neither side silently wins.

### Praxis (domain-specific scientific data analysis)

Auto-cloned as a git submodule at `vendor/praxis/` by `create-paper`. Provides:

- 50+ characterisation techniques: XRD, DSC, TGA, FTIR, Raman, XPS, EIS, mechanical testing (Young's modulus, UTS), AFM, SEM, VSM, BET, UV-Vis, and more
- 9 journal figure styles: Nature, Science, ACS, Elsevier, Wiley, RSC, Springer, IEEE, MDPI — auto-matched to venue from `.venue.json`
- Colourblind-safe palettes by default (Okabe-Ito)
- Technique-aware quantitative outputs: crystallite size from Scherrer equation (XRD), Tg/Tm from DSC, Young's modulus from mechanical curves, coercivity from VSM, etc.

The pipeline auto-detects data files in `attachments/` and uses Praxis at Stage 4. Analysis scripts are saved to `figures/scripts/` for reproducibility. Install dependencies with `pip install -r vendor/praxis/requirements.txt`.

### Claude Scientific Skills (177 skills)

Cloned as a git submodule at `vendor/claude-scientific-skills/` and symlinked to `.claude/skills/`. Skills are markdown files that agents read to guide their behavior. Used throughout the pipeline by naming them in agent prompts (e.g., "invoke the `scientific-writing` skill").

Skill categories include:
- Writing and review: `scientific-writing`, `peer-review`, `scientific-critical-thinking`, `citation-management`
- Database access: `pubmed-database`, `arxiv-database`, `openalex-database`, `chembl-database`, `uniprot-database`, `clinicaltrials-database`, and 30+ more
- Analysis: `statistical-analysis`, `exploratory-data-analysis`, `scikit-learn`, `transformers`, `pytorch-lightning`
- Visualization: `matplotlib`, `seaborn`, `plotly`, `scientific-visualization`
- Domain tools: `rdkit`, `biopython`, `scanpy`, `pymatgen`, `qiskit`, and 100+ more

### Domain detection and skill routing

At the start of Stage 1, the pipeline analyzes the topic to detect its domain. Domain detection matches indicator keywords:

| Domain | Indicators | Priority databases |
|-|-|-|
| Biomedical / Life Sciences | gene, protein, cell, disease, clinical, drug, genomic, cancer | PubMed, bioRxiv, UniProt, KEGG, Reactome, PDB |
| Chemistry / Drug Discovery | molecule, compound, synthesis, binding, SMILES, ADMET | PubChem, ChEMBL, DrugBank, ZINC, BindingDB |
| Computer Science / AI/ML | neural, network, model, training, transformer, LLM, NLP | arXiv, HuggingFace |
| Physics / Quantum | quantum, particle, field, relativity, optics | arXiv, NIST |
| Materials Science | crystal, material, alloy, polymer, semiconductor | arXiv, Materials Project |
| Ecology / Geospatial | ecology, climate, satellite, geographic, biodiversity | GBIF, geospatial databases |
| Economics / Finance | market, economic, stock, GDP | FRED, Alpha Vantage, EDGAR |
| Clinical / Medical | patient, treatment, trial, diagnosis, hospital | ClinicalTrials.gov, FDA databases |
| General (default) | (all others) | arXiv, OpenAlex |

All domains also receive universal skills: `scientific-writing`, `citation-management`, `peer-review`, `statistical-analysis`, `scientific-visualization`, `matplotlib`, `seaborn`, `plotly`.

---

## 9. Writing Rules

These rules are enforced across all agents in the pipeline. Violations are caught in QA review.

1. **Always write in full paragraphs.** Never leave bullet points in the final manuscript. Bullet points in agent outlines are converted to flowing prose.
2. **Two-stage writing process.** Stage 1: research and outline. Stage 2: convert outlines into flowing academic prose with transitions.
3. **IMRAD structure.** Introduction, Methods/Approach, Results/Experiments, Discussion. Adapted for survey and theoretical paper types.
4. **Citations.** Use `\citep{key}` for parenthetical and `\citet{key}` for narrative citations. Keys are in `firstauthorlastnameYear` format.
5. **Figures.** Save to `figures/`, reference with `\includegraphics{figures/filename}`. Prefer vector formats (PDF, EPS). PNG only for photographs.
6. **Tables.** Use `booktabs` package (`\toprule`, `\midrule`, `\bottomrule`). Minimum 2 tables.
7. **Cross-references.** Use `\label{}` and `\ref{}` consistently. All `\ref{}` calls must resolve.
8. **No placeholder text.** Remove all `\lipsum`, TODO, TBD, FIXME before finalizing.
9. **No fabricated references.** Every BibTeX entry must be a real, verifiable publication. The reference validation stage enforces this; fabricated entries are removed.
10. **Claims-Evidence Matrix.** Every major claim must map to specific evidence (experiment, citation, or proof) in `research/claims_matrix.md`. Every claim must reach "Supported" status to pass QA.
11. **No em dashes.** Never use em dashes (—) or en dashes (–) as punctuation. Rewrite using commas, parentheses, colons, or separate sentences. Em dashes are the single most recognizable AI writing pattern.
12. **Provenance logging.** Every agent that writes, revises, or cuts manuscript content appends entries to `research/provenance.jsonl`. Venue-aware length: if `.venue.json` has a page limit, scale section word targets proportionally.

---

## 10. Model Tiers

Three model tiers with 1M context windows are used throughout the pipeline. The `[1m]` suffix is required — the shorthand `"opus"` and `"sonnet"` resolve to standard context models, not the 1M variants.

| Tier | Model ID | Used for |
|-|-|-|
| Opus 1M | `claude-opus-4-6[1m]` | Writing agents, revision agents, expansion agents, gap analysis, de-AI polish, final polish — anything requiring deep reasoning, synthesis, or prose quality |
| Sonnet 1M | `claude-sonnet-4-6[1m]` | Research agents, review agents, data analysis, figures, assessment agents in `/auto`, verification agents — tasks requiring tool use, search, and structured evaluation |
| Haiku | `haiku` | Bibliography building, reference validation, lay summary, reproducibility checklist, per-section literature searches in deep mode, provenance report generation — mechanical lookup and formatting tasks |

The 1M context windows allow agents to read entire manuscripts, all research files, full bibliographies, and all review feedback without hitting context limits.

---

## 11. Project Structure

```
research-agent/                 (this repository)
├── create-paper                Bash script: stamps out new paper projects
├── write-paper                 Bash script: launcher for the autonomous pipeline
├── sync-papers                 Bash script: migrate/update existing projects to use symlinks
├── template/
│   ├── claude/
│   │   ├── CLAUDE.md          Project instructions, writing rules, command reference
│   │   ├── settings.local.json Tool permissions for autonomous operation
│   │   ├── commands/          All 35 slash commands (symlinked into each paper project)
│   │   └── pipeline/          Stage-specific instructions (read on-demand per stage/phase)
│   │       ├── stage-1-research.md through stage-6-finalization.md
│   │       ├── auto-phase-1-assessment.md through auto-phase-4-verification.md
│   │       └── shared-protocols.md
│   ├── scripts/               Utility scripts (knowledge.py, etc.)
│   ├── venues/                Venue configuration JSON files
│   │   ├── generic.json
│   │   ├── ieee.json
│   │   ├── acm.json
│   │   ├── neurips.json
│   │   ├── nature.json
│   │   ├── arxiv.json
│   │   └── apa.json
│   ├── main.tex               LaTeX template (overwritten by venue-specific generation)
│   ├── references.bib         Empty bibliography template
│   └── gitignore              Standard gitignore for paper projects
├── tests/                     Test suite (run_all.sh, test_structure.sh, test_prompts.sh, test_schema.py)
├── .github/workflows/ci.yml  CI via GitHub Actions
└── vendor/                    External dependencies (submodules)
```

**Generated paper project structure:**

```
my-paper/
├── main.tex                   LaTeX document, venue-formatted
├── references.bib             BibTeX bibliography
├── .paper.json                Paper topic, venue, authors, depth, config
├── .venue.json                Venue formatting rules (copied from template)
├── .paper-state.json          Pipeline checkpoint state (created at runtime)
├── .paper-progress.txt        Human-readable progress monitor (tail from another terminal)
├── figures/                   Generated figures (PDF, PNG)
│   └── scripts/               Figure generation scripts (for reproducibility)
├── attachments/               User-provided PDFs, datasets, supplementary materials
├── research/                  Literature research outputs (created by pipeline)
│   ├── sources/               Raw source extracts per cited paper (<bibtexkey>.md)
│   ├── knowledge/             LightRAG knowledge graph (gitignored, rebuilds from sources)
│   ├── log.md                 Complete research provenance log
│   ├── provenance.jsonl       Machine-readable provenance ledger (append-only)
│   ├── provenance_report.md   Human-readable provenance summary (generated at end)
│   ├── survey.md              Field survey (Stage 1, Agent 1)
│   ├── methods.md             Methodology deep dive (Stage 1, Agent 2)
│   ├── empirical.md           Empirical evidence (Stage 1, Agent 3)
│   ├── theory.md              Theoretical foundations (Stage 1, Agent 4)
│   ├── gaps.md                Gap analysis and thesis proposal (Stage 1, Agent 5)
│   ├── thesis.md              Thesis and contribution statement (Stage 2)
│   ├── claims_matrix.md       Claims-evidence matrix (Stage 2)
│   ├── novelty_check.md       Novelty verification report (Stage 2d)
│   ├── source_coverage.md     Source access level audit (Stage 1d)
│   ├── codex_cross_check.md   Codex research cross-check (Stage 1c)
│   ├── codex_thesis_review.md Codex thesis stress-test (Stage 2b)
│   ├── reference_validation.md Reference verification report (Post-QA)
│   ├── reproducibility_checklist.md Reproducibility checklist (Post-QA)
│   └── summaries.md           Lay summary and elevator pitch (Stage 6)
├── reviews/                   Review feedback (created during QA)
│   ├── technical.md           Technical reviewer output
│   ├── writing.md             Writing quality reviewer output
│   ├── completeness.md        Citation and completeness reviewer output
│   ├── codex_adversarial.md   Codex adversarial review
│   ├── codex_risk_radar.md    Codex risk radar assessment
│   ├── consistency.md         Post-QA consistency checker output
│   ├── claims_audit.md        Post-QA claims auditor output
│   └── codex_deliberation_log.md All Claude-Codex deliberations
├── provenance/
│   └── cuts/                  Archived text from all content that was cut
├── archive/                   Browsable research archive (created by /archive)
│   └── README.md              Indexed guide to all archive contents
├── submission/                Submission package (created by /prepare-submission)
├── vendor/
│   ├── claude-scientific-skills/ 177 scientific skills (git submodule)
│   └── praxis/               Scientific data analysis toolkit (git submodule)
└── .claude/
    ├── CLAUDE.md              Project instructions (copied from template)
    ├── settings.local.json    Tool permissions
    ├── commands/              All 35 slash commands
    ├── pipeline/             Stage and phase instructions (symlinked from template)
    └── skills/ -> vendor/    Symlink to scientific skills
```

---

## 12. Configuration Reference

### `.paper.json`

Created by `create-paper`, read by the pipeline and most commands.

```json
{
  "topic": "A survey on large language model reasoning",
  "venue": "arxiv",
  "depth": "standard",
  "model": "claude-opus-4-6",
  "max_revisions": 3,
  "email": "user@example.com",
  "oa_resolution": {
    "unpaywall": true,
    "openalex": true,
    "semantic_scholar": true,
    "core": true,
    "pubmed_central": "auto",
    "web_search": true,
    "repository_search": true
  },
  "authors": [
    {
      "name": "First Author",
      "affiliation": "Department, University",
      "email": "author@example.com",
      "orcid": "0000-0000-0000-0000"
    }
  ],
  "keywords": ["large language models", "reasoning", "chain-of-thought"],
  "funding": "Grant XYZ from Funding Body",
  "conflicts": "None declared",
  "data_availability": "Available at https://github.com/...",
  "code_availability": "https://github.com/..."
}
```

| Field | Description |
|-|-|
| `topic` | Paper topic, used to seed the research pipeline and all agent prompts |
| `venue` | Target venue: `generic`, `ieee`, `acm`, `neurips`, `nature`, `arxiv`, `apa` |
| `depth` | `"standard"` (5 agents, 30-50 refs, 1-4 hrs) or `"deep"` (12 agents, 60-80 refs, 3-8 hrs) |
| `model` | Base model (1M context variants are added automatically per tier) |
| `max_revisions` | Maximum QA iterations (overridden by depth: 5 for standard, 8 for deep) |
| `email` | Email for Unpaywall API auth and OpenAlex rate-limit boost. Also read from `UNPAYWALL_EMAIL` env var. |
| `oa_resolution` | Per-API toggles for the OA resolution chain (see below). All default to `true`. |
| `authors` | Author list for cover letter and author block |
| `keywords` | Keywords for submission metadata |
| `funding` | Funding acknowledgment text |
| `conflicts` | Conflicts of interest declaration |
| `data_availability` | Data availability statement for submission |
| `code_availability` | Code availability statement and URL |

#### `oa_resolution` sub-object

Controls which APIs are tried during source acquisition (Stage 1d), `/audit-sources`, and `/validate-references`. The pipeline tries each enabled API in order and stops on the first successful PDF download.

| Key | Default | Description |
|-|-|-|
| `unpaywall` | `true` | [Unpaywall](https://unpaywall.org) — ~30M OA articles. Requires `email` field or `UNPAYWALL_EMAIL` env var. |
| `openalex` | `true` | [OpenAlex](https://openalex.org) — 250M+ works, no key needed. Also extracts abstracts. |
| `semantic_scholar` | `true` | [Semantic Scholar](https://www.semanticscholar.org) — checks `openAccessPdf` field. |
| `core` | `true` | [CORE](https://core.ac.uk) — 200M+ institutional repository papers. Requires `CORE_API_KEY` env var (free). |
| `pubmed_central` | `"auto"` | [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/) — biomedical full text. `"auto"` enables only for biomedical/clinical domains. Set `true` to force on, `false` to disable. Optional: `NCBI_API_KEY` env var increases rate limit. |
| `web_search` | `true` | Firecrawl search for PDFs (filetype:pdf). |
| `repository_search` | `true` | Search ResearchGate, Academia.edu, SSRN. |

#### Environment variables

| Variable | Required | Description |
|-|-|-|
| `UNPAYWALL_EMAIL` | For Unpaywall | Alternative to `email` in `.paper.json`. Any valid email address. |
| `CORE_API_KEY` | For CORE | Free API key from [core.ac.uk/services/api](https://core.ac.uk/services/api). CORE is skipped if not set. |
| `NCBI_API_KEY` | No | Free key from NCBI. Increases PubMed rate limit from 3/s to 10/s. |
| `OPENROUTER_API_KEY` | For knowledge graph | Required for LightRAG knowledge graph. Graph is skipped if not set. |

### `.venue.json`

Copied from the template venues directory. Read by the pipeline, writing agents, and Praxis for figure styles.

```json
{
  "name": "Generic Journal",
  "id": "generic",
  "documentclass": "\\documentclass[12pt]{article}",
  "packages": ["\\usepackage{natbib}", "..."],
  "bibliography_style": "plainnat",
  "citation_style": "natbib",
  "citation_commands": ["\\citep{}", "\\citet{}"],
  "page_limit": null,
  "abstract_word_limit": 300,
  "blind_review": false,
  "sections": ["Introduction", "Related Work", "Methods", "Results", "Discussion", "Conclusion"],
  "notes": "Standard journal format with natbib citations. No page limit."
}
```

The pipeline reads `page_limit` to scale section word targets proportionally. It reads `blind_review` to know whether `/prepare-submission` should anonymize the author block. It reads `sections` to determine the initial section order in `main.tex`.

### `.paper-state.json`

Written after every stage. Read at startup for resume. Do not edit manually.

```json
{
  "topic": "...",
  "venue": "generic",
  "started_at": "2026-03-24T10:00:00Z",
  "current_stage": "writing",
  "stages": {
    "research":     { "done": true,  "completed_at": "...", "notes": "45 refs found" },
    "codex_cross_check": { "done": true, "completed_at": "..." },
    "source_acquisition": { "done": true, "full_text": 28, "abstract_only": 12, "metadata_only": 5 },
    "knowledge_graph": { "done": true, "entities": 347, "relationships": 891 },
    "outline":      { "done": true,  "completed_at": "..." },
    "codex_thesis": { "done": true,  "completed_at": "..." },
    "novelty_check": { "done": true, "status": "NOVEL" },
    "writing": {
      "done": false,
      "sections": {
        "introduction":  { "done": true,  "words": 1250 },
        "related_work":  { "done": true,  "words": 2100 },
        "methods":       { "done": false, "words": 0 }
      }
    },
    "figures":      { "done": false },
    "qa":           { "done": false },
    "qa_iteration": 2,
    "codex_risk_radar": { "done": false },
    "finalization": { "done": false },
    "auto_iterations": {
      "completed": 0,
      "requested": 0,
      "history": []
    }
  }
}
```

### `.paper-progress.txt`

Human-readable progress file updated at each stage. Intended for monitoring from a second terminal:

```bash
watch cat .paper-progress.txt
```

Updated by `/status` and at each pipeline checkpoint.

---

## Contributing

The template files in `template/claude/commands/` define what each slash command does. Editing them changes the behavior of the pipeline in all new paper projects.

Key files for contributors:
- `template/claude/CLAUDE.md` — project rules and command reference (symlinked into each paper project)
- `template/claude/commands/write-paper.md` — the full pipeline definition (~1500 lines)
- `template/claude/commands/auto.md` — the `/auto` improvement loop
- `template/claude/commands/provenance.md` — the provenance query command
- `create-paper` — the project scaffolding script
- `write-paper` — the pipeline launcher script
- `template/venues/` — venue configuration files

### Testing

Run the test suite with `tests/run_all.sh`. Individual tests: `tests/test_structure.sh` (project structure validation), `tests/test_prompts.sh` (prompt consistency checks), `tests/test_schema.py` (JSON schema validation). CI runs automatically via GitHub Actions (`.github/workflows/ci.yml`).

---

## License

MIT
