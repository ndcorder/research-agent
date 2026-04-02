# Write Paper — Autonomous Journal-Quality Research Paper Pipeline

You are an autonomous research paper writing system. You will produce a publication-ready, journal-quality research paper by orchestrating specialized agents across multiple stages. This process takes 1-4+ hours. Depth over speed, always.

## Setup

**IMPORTANT — Sister Projects**: This pipeline uses two external tools that you MUST call directly (not via agents) at specific stages:
- **Codex Bridge** (`codex_plan`, `codex_review`, `codex_ask`, `codex_risk_radar`, `codex_stats`): Used throughout the pipeline as a second AI perspective. Call these MCP tools (`mcp__codex-bridge__*`) directly in your session — NOT via agents. Integration points: Stage 1c (research cross-check), Stage 2b (thesis stress-test), Stage 3 (section spot-checks), Stage 4c (figure/claims audit), Stage 5 (adversarial review), Post-QA (risk radar), Stage 6 (collaboration stats).
- **Praxis** (`vendor/praxis/`): Use at Stage 4 if data files exist in `attachments/`. Import via `sys.path.insert(0, "vendor/praxis/scripts")`.

1. Read `.paper.json` for topic, venue, depth, and config. If it doesn't exist, create it from the topic in $ARGUMENTS with `depth: "standard"`.
   - **depth** controls research intensity: `"standard"` (default) or `"deep"` (3× research effort).
   - Store the depth value — it determines behavior at every stage below.
2. Read `.venue.json` if present for venue-specific formatting rules (sections, citation style, page limits).
3. Read `main.tex` and `references.bib` to understand current state.
4. **Preflight check** — verify critical prerequisites before starting the multi-hour pipeline. Run these Bash commands and evaluate results:
   ```bash
   which pdflatex && which latexmk && echo "LATEX_OK" || echo "LATEX_MISSING"
   python3 --version 2>&1 | grep -q "3\.\(1[0-9]\|[2-9][0-9]\)" && echo "PYTHON_OK" || echo "PYTHON_WARN"
   ```
   - If `LATEX_MISSING`: **STOP.** Tell the user: "pdflatex or latexmk not found. Install a LaTeX distribution (e.g., `brew install --cask mactex`) before running the pipeline." Do not proceed.
   - If `PYTHON_WARN`: Print a warning but continue (Python is only needed for knowledge graph and data analysis).

   Then check optional integrations:
   ```bash
   [ -n "$OPENROUTER_API_KEY" ] && echo "OPENROUTER_OK" || echo "OPENROUTER_MISSING"
   python3 -c "import lightrag" 2>/dev/null && echo "LIGHTRAG_OK" || echo "LIGHTRAG_MISSING"
   ```
   - If `OPENROUTER_MISSING`: Print: "OPENROUTER_API_KEY not set — knowledge graph queries will be skipped at all stages. The pipeline still works but evidence verification is weaker. Set the key and re-run, or continue without it."
   - If `OPENROUTER_OK` but `LIGHTRAG_MISSING`: Print: "lightrag not installed — run `pip install lightrag-hku` to enable the knowledge graph. Continuing without it."
   - If both OK: Print "Knowledge graph: ready" and continue.

   This check takes <5 seconds. Do not ask the user for confirmation — just report findings and stop only on fatal issues (missing LaTeX).
5. Run: `mkdir -p research research/sources reviews figures provenance provenance/cuts`
6. Initialize the research log: write a header to `research/log.md`:
   ```markdown
   # Research Log

   Provenance trail of all searches, queries, and sources consulted during the research pipeline.
   Each entry records: timestamp, agent, tool used, query, result summary, and URLs/DOIs found.

   ---
   ```
   Also initialize `reviews/codex_deliberation_log.md`:
   ```markdown
   # Codex Deliberation Log

   Record of all Claude-Codex deliberations: agreements, disagreements, rebuttals, and resolutions.

   ---
   ```
   Also initialize the provenance ledger. Create an empty file `research/provenance.jsonl` (or leave it if it already exists on resume). This is a machine-readable append-only log of every action taken during the pipeline. Every agent will append entries to this file.
7. Create a task for each pipeline stage using TaskCreate.
8. **Resume check**: Read `.paper-state.json` if it exists. It tracks completed stages and section word counts. Skip any stage marked `"done": true`. If no state file exists but `research/` has files or `main.tex` has content, infer progress and build the state file from what exists.
   - **Partial Stage 1 resume**: If `stages.research` has `agents_completed` with entries but `done: false`, only spawn agents NOT already in the `agents_completed` list. Before trusting the list, verify each completed agent's output file exists in `research/` and has non-trivial content (>100 bytes). If a file is missing or empty, remove that agent from `agents_completed` and re-run it. Agents still in `agents_pending` (or not in either list) must be spawned. After all agents finish, proceed to the bibliography builder as normal.
   - **Partial Stage 3 resume**: If `stages.writing.sections` has per-section tracking, skip any section marked `"done": true`. Resume from the first section where `done` is false. If a section has `done: false` but `current_substep` is set (e.g., `"expansion"`, `"evidence_check"`, `"micro_research"`), skip sub-steps that precede the recorded `current_substep` in the pipeline flow (write → expansion → spot_check → evidence_check → micro_research → patch). Verify that `main.tex` actually contains content for sections marked done — if a section is marked done but has no content in the LaTeX file, reset it to `done: false`.
   - **Special case — Source Acquisition pause**: If `source_acquisition` exists but `"done": false`, the pipeline was paused waiting for the user to provide PDFs. Check `attachments/` for any new PDF files (compare against `research/source_coverage.md` to identify new additions). If new PDFs found, ingest them (same as `/ingest-papers` logic), update source extracts, then mark `source_acquisition` as done and continue to Stage 2. If no new PDFs, re-present the acquisition list from `research/source_coverage.md` and ask the user again.

## Checkpoint Persistence

After completing EACH stage or section, update `.paper-state.json`:

```json
{
  "topic": "...",
  "venue": "generic",
  "started_at": "2026-03-21T14:00:00Z",
  "current_stage": "writing",
  "stages": {
    "research":     { "done": true,  "completed_at": "...", "agents_completed": ["survey", "methods", "empirical", "theory", "gaps"], "agents_pending": [], "notes": "45 refs found" },
    "snowballing":  { "done": false, "seeds": 0, "backward_found": 0, "forward_found": 0, "added_to_bib": 0 },
    "cocitation":   { "done": false, "references_analyzed": 0, "high_confidence_found": 0, "medium_confidence_found": 0, "auto_added": 0 },
    "outline":      { "done": true,  "completed_at": "..." },
    "codex_cross_check": { "done": true, "completed_at": "...", "file": "research/codex_cross_check.md" },
    "source_acquisition": { "done": false, "full_text": 0, "abstract_only": 0, "metadata_only": 0 },
    "deep_read": { "done": false, "sources_read": 0, "agents_completed": [], "agents_pending": [] },
    "literature_synthesis": { "done": false, "completed_at": null, "agents_completed": [], "agents_pending": [] },
    "codex_thesis": { "done": true,  "completed_at": "...", "file": "research/codex_thesis_review.md" },
    "novelty_check": { "done": true, "completed_at": "...", "file": "research/novelty_check.md", "status": "NOVEL" },
    "assumptions": { "done": true, "completed_at": "...", "file": "research/assumptions.md", "total": 12, "critical": 1, "risky": 3 },
    "writing": {
      "done": false,
      "current_substep": "evidence_check",
      "sections": {
        "introduction":  { "done": true,  "words": 1250, "current_substep": null },
        "related_work":  { "done": true,  "words": 2100, "current_substep": null },
        "methods":       { "done": false, "words": 0, "current_substep": "expansion" }
      }
    },
    "coherence":    { "done": false, "issues_found": 0, "critical_fixed": 0 },
    "figures":      { "done": false },
    "qa_iteration": 0,
    "qa":           { "done": false },
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

Write this file using the Write tool after every stage completion. On resume, read it first and skip completed work. Also write current progress to `.paper-progress.txt` (human-readable summary) so users can monitor from another terminal via `cat .paper-progress.txt`.

## Depth Mode

Read `depth` from `.paper.json` (default: `"standard"`). This controls research intensity across all stages.

| Setting | standard | deep |
|-|-|-|
| Stage 1 research agents | 5 | 12 (7 additional specialized agents) |
| Stage 1b snowball seeds | 10 | 20 |
| Stage 1d acquisition list | top 5 by evidence impact (or citation count if no matrix yet) | ALL abstract-only papers |
| Reference target | 30-50 | 60-80 |
| Stage 2c targeted research | skip | thesis-informed second pass (3-4 agents) |
| Stage 3 per-section lit search | skip | research agent before each writing agent |
| Stage 3 Codex expansion | fix critical issues only | also ask "what's missing?" and expand |
| Max QA iterations | 5 | 8 |
| Codex rounds per checkpoint | 1 | 2 (early + late in QA loop) |

When `depth` is `"deep"`, follow ALL deep-mode instructions marked with **[DEEP]** below. When `depth` is `"standard"`, skip them.

## Pipeline Execution

**CRITICAL**: Before each stage, read its instructions fresh from disk using the Read tool. Do NOT rely on memory of instructions read earlier in the session. This ensures you follow the latest, complete instructions even in long-running sessions where earlier context may be compressed.

### Startup

1. Complete all Setup steps above
2. Read `pipeline/shared-protocols.md` — it contains the Codex Deliberation Protocol, Provenance Logging Protocol, Domain Detection & Skill Routing table, Tool Fallback Chain, and Source Extract Format. These are referenced throughout the pipeline. Internalize these protocols now.
3. Detect the paper's domain using the Domain Detection table in shared-protocols.md. Store the domain and skill list.
4. Check `.paper-state.json` for resume state

### Stage Execution

For each stage in order:
1. Check `.paper-state.json` — skip if stage is marked `"done": true`
2. **Read the stage file** from `pipeline/` using the Read tool (fresh from disk)
3. Execute the instructions in the stage file
4. Update `.paper-state.json` with completion status
5. Update `.paper-progress.txt` with human-readable progress
6. Proceed to next stage

### Pipeline Stages

| Order | Stage | File to Read | Skip Condition |
|-|-|-|-|
| 1 | Deep Literature Research | `pipeline/stage-1-research.md` | `stages.research.done` |
| 2 | Citation Snowballing | `pipeline/stage-1b-snowballing.md` | `stages.snowballing.done` |
| 3 | Co-Citation Analysis | `pipeline/stage-1b2-cocitation.md` | `stages.cocitation.done` |
| 4 | Codex Cross-Check | `pipeline/stage-1c-codex-crosscheck.md` | `stages.codex_cross_check.done` |
| 5 | Source Acquisition | `pipeline/stage-1d-source-acquisition.md` | `stages.source_acquisition.done` |
| 6 | Deep Source Reading | `pipeline/stage-1e-deep-read.md` | `stages.deep_read.done` |
| 7 | Literature Synthesis | `pipeline/stage-1f-synthesis.md` | `stages.literature_synthesis.done` |
| 8 | Planning | `pipeline/stage-2-planning.md` | `stages.outline.done` |
| 9 | Codex Thesis Stress-Test | `pipeline/stage-2b-codex-thesis.md` | `stages.codex_thesis.done` |
| 10 | Targeted Research [DEEP] | `pipeline/stage-2c-targeted-research.md` | `stages.targeted_research.done` OR depth ≠ "deep" |
| 11 | Novelty Verification | `pipeline/stage-2d-novelty-check.md` | `stages.novelty_check.done` |
| 12 | Assumptions Analysis | `pipeline/stage-2e-assumptions.md` | `stages.assumptions.done` |
| 13 | Section Writing | `pipeline/stage-3-writing.md` | `stages.writing.done` |
| 14 | Cross-Section Coherence | `pipeline/stage-3b-coherence.md` | `stages.coherence.done` |
| 15 | Figures & Tables | `pipeline/stage-4-figures.md` | `stages.figures.done` |
| 16 | QA Loop | `pipeline/stage-5-qa.md` | `stages.qa.done` |
| 17 | Post-QA Audits | `pipeline/stage-5-post-qa.md` | `stages.post_qa.done` |
| 18 | Finalization | `pipeline/stage-6-finalization.md` | `stages.finalization.done` |

**Important**: The QA Loop (Stage 16) reads `pipeline/stage-5-qa.md` which contains an internal loop with reference spot-checks at each iteration. After the QA loop completes, proceed to Post-QA (Stage 17). The quality criteria table below defines the gate for exiting the QA loop.

---

## Quality Criteria

ALL must pass to exit Stage 5. Note: writing targets in Stage 3 are intentionally higher than these minimums — aim high, gate at the floor. Scale all targets proportionally if venue has page limits (Rule 12).

| Criterion | Requirement |
|-|-|
| Sections substantively complete | No obvious gaps, thin arguments, or missing depth |
| Introduction | Sets up the problem, contribution, and paper structure clearly |
| Related Work / Background | Covers the field thoroughly — no major omissions a reviewer would flag |
| Methods / Approach | Detailed enough for reproduction by an independent researcher |
| Results / Experiments | All claims supported by presented evidence |
| Discussion | Honest limitations, meaningful comparisons with prior work |
| Conclusion | Concise summary with specific results |
| Abstract | Self-contained, specific, quantitative where possible |
| Claims-Evidence Matrix | Every claim in research/claims_matrix.md has status "Supported" |
| Evidence Density | No CRITICAL-strength claims (score < 1) in the manuscript. WEAK claims (1-2.9) use hedged language. |
| References in .bib | 25+ verified entries |
| Placeholder text | 0 (no TODO/TBD/FIXME/lipsum/mbox{}) |
| LaTeX compilation | No errors |
| Tables | 2+ with booktabs |
| \ref{} cross-references | All resolve |
| \citep{}/\citet{} keys | All exist in references.bib |
| Body text format | Full paragraphs only (no bullet points) |

---

## Error Handling & Robustness

- **Agent failure**: If an agent fails or produces no output, log the error and retry ONCE with a simplified prompt. If it fails again, skip and note in the task list what was missed.
- **Empty research results**: If a research agent returns no papers, try alternative search tools (different MCP servers, web search, etc.). If still empty, note the gap and continue — other agents may cover it.
- **Compilation errors**: After any edit to main.tex, compile. If errors appear, fix them immediately before proceeding.
- **Word count under target after expansion**: If a section remains under target after 2 expansion attempts, accept it and flag for manual review.
- **Session interruption**: All progress is written to files (research/, reviews/, main.tex). On resume, check existing files and skip completed stages. Use TaskList to see prior progress.
- **Reference verification failures**: If a reference cannot be verified as real, REMOVE it rather than keeping a potentially fabricated citation.

## Rules

1. **Never fabricate references.** Every BibTeX entry must be a real, verifiable publication.
2. **Never leave bullet points in manuscript body.** All content must be flowing paragraphs.
3. **Write exhaustively.** More depth is always better. 2000 thorough words beats 500 concise ones.
4. **How to use skills.** When an agent prompt says "use the `scientific-writing` skill", the agent should read the file `.claude/skills/scientific-writing/SKILL.md` and follow its guidance. Skills are markdown files at `.claude/skills/<skill-name>/SKILL.md`. The `scientific-writing` skill is mandatory for all writing agents.
5. **Sequential writing, parallel research/review.** Writing agents one at a time. Research and review agents in parallel.
6. **Assess completeness after every writing agent.** If the section lacks depth, is missing citations, or leaves obvious gaps, expand immediately. The expansion agent should use `model: "claude-opus-4-6[1m]"`.
7. **Model selection.** Three tiers — use 1M context variants (`[1m]` suffix) for opus and sonnet so agents can read entire manuscripts + all research files + full bibliographies without hitting context limits:
   - **Opus 1M** (`model: "claude-opus-4-6[1m]"`): Writing, revision, expansion, final polish, gap analysis, de-AI polish — anything requiring deep reasoning, synthesis, or prose quality.
   - **Sonnet 1M** (`model: "claude-sonnet-4-6[1m]"`): Research agents, review agents, data analysis, figures — tasks requiring tool use, search, and structured evaluation.
   **IMPORTANT**: The shorthand `"opus"` and `"sonnet"` resolve to the standard context models, NOT the 1M variants. You MUST use the full model IDs above for all agents. Never use Haiku — all tasks use either Opus 1M or Sonnet 1M.
8. **Track progress.** Use TaskCreate/TaskUpdate for every stage. Naming: `"Stage 1: Research"`, `"Stage 3: Write Introduction"`, etc. Set status to `in_progress` when starting, `completed` when done.
9. **Be patient.** This pipeline runs 1-4+ hours. Every stage matters. Do not rush or skip.
10. **Domain awareness.** Use the detected domain to choose appropriate skills and databases for each agent.
11. **Clear stale reviews.** Before each QA loop iteration (Stage 5a), delete old review files: `rm -f reviews/technical.md reviews/writing.md reviews/completeness.md` so reviewers evaluate the latest version.
12. **Venue-aware length.** If `.venue.json` has a `page_limit`, respect it. An 8-page IEEE paper must be concise — prioritize depth over breadth and cut less critical content. Read the venue config and adjust scope accordingly.
13. **Use provided scripts, never write custom ones.** This pipeline has purpose-built scripts (`scripts/parse-pdf.py`, `scripts/knowledge.py`, `scripts/pdf-cache.sh`, `scripts/format_sentences.py`, `scripts/update-manifest.py`) and stage instructions designed to work together. Do NOT write one-off Python or shell scripts to replace, bypass, or "optimize" them. If a provided script or tool exists for a task, use it exactly as documented. The system is architected this way deliberately: scripts are shared across all paper projects via symlinks, tested in CI, and maintained centrally. Custom scripts bypass this and cannot benefit other projects.

## Topic

$ARGUMENTS
