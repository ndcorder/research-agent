# Pipeline Quick Reference

Concise reference card for all `/write-paper` pipeline stages and `/auto` phases. For detailed descriptions, see the [README](../README.md) and the stage files in `template/claude/pipeline/`.

## Pipeline Stages

### Research Phase

| Stage | Name | Model | Parallel | Purpose | Key Output |
|-|-|-|-|-|-|
| 1 | Deep Literature Research | Sonnet 1M | 5-12 agents | Comprehensive field survey, methodology, empirical evidence, theory, gap analysis | `research/*.md`, `references.bib` |
| 1b | Citation Snowballing | Sonnet 1M | 2 agents | Backward + forward citation graph traversal | Additional refs in `references.bib` |
| 1b-ii | Co-Citation Analysis | Sonnet 1M | Single | Identify missing papers via bibliometric co-citation patterns | Additional refs |
| 1c | Codex Cross-Check | Codex | Single | Independent verification of research findings (skip if no codex-bridge) | `research/codex_cross_check.md` |
| 1d | Source Acquisition | Sonnet 1M | Sequential (6 phases) | Audit access levels, run 14-resolver OA cascade, pause for paywalled PDFs | `research/source_coverage.md`, PDFs |
| 1e | Deep Source Reading | Sonnet 1M | Parallel agents | Rewrite source extracts from full-text PDFs (replaces thin snapshots) | Updated `research/sources/*.md` |
| 1f | Cross-Source Synthesis | Sonnet 1M | Parallel agents | Synthesize consensus, conflicts, methodology critique, framework taxonomy | Unified synthesis docs |

### Planning Phase

| Stage | Name | Model | Parallel | Purpose | Key Output |
|-|-|-|-|-|-|
| 2 | Thesis & Contribution | Opus 1M | Single | Define thesis, contribution statement, detailed outline, claims-evidence matrix | `research/thesis.md`, `research/claims_matrix.md` |
| 2b | Codex Thesis Stress-Test | Codex | Single | Challenge thesis novelty and argument structure (skip if no codex-bridge) | `research/codex_thesis_review.md` |
| 2c | Targeted Research | Sonnet 1M | 3 agents | Surgical second research pass on specific claims (**deep mode only**) | Additional sources |
| 2d | Novelty Verification | Sonnet 1M | Single | Verify contribution hasn't been published; returns NOVEL / PARTIALLY NOVEL / NOT NOVEL | `research/novelty_check.md` |
| 2e | Assumptions Analysis | Opus 1M | Single | Enumerate methodological assumptions (Standard / Reasonable / Risky / Critical) | `research/assumptions.md` |

### Writing Phase

| Stage | Name | Model | Parallel | Purpose | Key Output |
|-|-|-|-|-|-|
| 3 | Section Writing | Opus 1M | Sequential (per section) | Write each section with evidence, citations, provenance logging | `main.tex` sections |
| 3b | Cross-Section Coherence | Opus 1M | Single | Promise fulfillment, concept consistency, rebuttal threading | Edits to `main.tex` |
| 3c | Reference Integrity | Sonnet 1M | Parallel agents + script | Verify citation artifacts, detect misattributions | `research/reference_integrity.json` |

### Figures & QA Phase

| Stage | Name | Model | Parallel | Purpose | Key Output |
|-|-|-|-|-|-|
| 4 | Figures & Tables | Sonnet 1M | Single | Data-driven figures (Praxis if available, else matplotlib), structural figures, Codex audit | `figures/*.pdf`, `figures/scripts/` |
| 5 | QA Loop | Sonnet 1M | 3-4 parallel reviewers | Technical + Writing + Completeness + Codex adversarial review, up to 5 iterations (8 deep) | `reviews/*.md` |
| 5+ | Post-QA Audits | Sonnet 1M | Parallel | Consistency checker, claims auditor, reproducibility checker, reference validator, Codex risk radar | `reviews/consistency.md`, `reviews/claims_audit.md` |
| 6 | Finalization | Opus 1M | Sequential | Scooping check, final polish, de-AI polish, lay summary, provenance report, archive | `main.pdf`, `research/provenance_report.md` |

## `/auto` Improvement Phases

Each `/auto` iteration runs four phases:

| Phase | Name | Model | Parallel | Purpose | Key Output |
|-|-|-|-|-|-|
| 1 | Assessment | Sonnet 1M | 4-5 agents | Depth/evidence, structure/flow, competitive positioning, writing quality, regression detection | `reviews/auto_iter[N]_*.md` |
| 2 | Prioritization | Opus 1M | Single | Deduplicate findings, rank top 5 actions by impact (regressions first). Early stop if < 3 actions. | `reviews/auto_iter[N]_plan.md` |
| 3 | Execution | Opus 1M | Single | Targeted research (max 3 queries) + revision agent executes action plan | Edits to `main.tex`, `references.bib` |
| 4 | Verification | Sonnet 1M | Single | LaTeX compile, citation keys, cross-refs, no placeholders, no em dashes, no regressions | Pass/fail gate |

## Quality Gate Criteria (Stage 5)

All must pass to exit the QA loop:

| Criterion | Requirement |
|-|-|
| Sections complete | No obvious gaps, thin arguments, or missing depth |
| Claims-Evidence Matrix | Every claim status = "Supported" |
| References | 25+ verified BibTeX entries |
| Placeholders | Zero (no TODO/TBD/FIXME/lipsum) |
| LaTeX compilation | No errors |
| Tables | 2+ with booktabs |
| Cross-references | All `\ref{}` resolve |
| Citation keys | All `\citep{}`/`\citet{}` exist in `.bib` |
| Body text | Full paragraphs only, no bullet points |

## Checkpoint & Resume

Every stage writes completion status to `.paper-state.json`. On restart, completed stages are skipped. The writing stage tracks per-section completion.

```
research → snowballing → cocitation → codex_cross_check → source_acquisition
→ deep_read → synthesis → outline → codex_thesis → targeted_research (deep only)
→ novelty_check → assumptions → writing → coherence → reference_integrity
→ figures → qa (loop) → post_qa → finalization
```

Monitor progress from a second terminal:

```bash
watch cat .paper-progress.txt
```

## Model Tier Summary

| Tier | Model ID | Role |
|-|-|-|
| Opus 1M | `claude-opus-4-6[1m]` | Writing, revision, expansion, de-AI polish, final polish, gap analysis |
| Sonnet 1M | `claude-sonnet-4-6[1m]` | Research, review, data analysis, figures, assessment, verification |
| Haiku | `haiku` | Bibliography, reference validation, lay summary, reproducibility checklist, provenance report |
| Codex | `codex-bridge` (external) | Adversarial review, cross-check, thesis stress-test, risk radar (optional) |

## Shared Protocols

Cross-cutting concerns loaded once from `pipeline/shared-protocols.md` and injected into agent prompts:

| Protocol | Purpose |
|-|-|
| Codex Deliberation | AGREE / PARTIALLY AGREE / DISAGREE with one rebuttal round; unresolved items logged for user |
| Provenance Logging | JSON format for `provenance.jsonl` entries with paragraph-level targeting |
| Tool Fallback Chain | Domain Skills → Perplexity → WebSearch → Firecrawl → WebFetch → research-lookup → log gap |
| Source Extract Format | Template for `research/sources/*.md` with access level, content snapshot, provenance |
| Knowledge Graph Availability | How agents query the graph when it exists; graceful skip when it doesn't |
| Semantic Scholar Rate Limiting | API pacing rules to avoid 429s |
| Domain Detection & Skill Routing | Maps topic keywords to priority databases and skills |
| Bash Timeout Protocol | Timeout handling for long-running shell commands |
