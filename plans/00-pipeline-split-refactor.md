# Pipeline Split Refactor — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the monolithic `write-paper.md` (~1700 lines, ~23K tokens) into a compact orchestrator + stage-specific files that are read fresh from disk before each stage executes, preventing context compression from degrading later-stage instructions.

**Architecture:** The orchestrator (`write-paper.md`) shrinks to ~300 lines containing setup, state management, the pipeline loop, quality criteria, and rules. Each pipeline stage becomes its own file in `template/claude/pipeline/`. Shared protocols (Codex deliberation, provenance logging, tool fallback, source extract format, domain detection) go in a single shared file read once at pipeline start. Before executing each stage, the orchestrator instructs Claude to read the stage file fresh from disk.

**Tech Stack:** Markdown files only. No code changes. Pure content reorganization.

---

### Task 1: Create pipeline directory and shared-protocols.md

**Files:**
- Create: `template/claude/pipeline/shared-protocols.md`

**Step 1: Create the directory**

```bash
mkdir -p template/claude/pipeline
```

**Step 2: Write shared-protocols.md**

Extract these sections from current write-paper.md (lines 99-197) into shared-protocols.md:
- Codex Deliberation Protocol (lines 99-131)
- Provenance Logging Protocol (lines 133-171)
- Domain Detection & Skill Routing (lines 175-197)
- Tool Fallback Chain (lines 208-232 — the reusable boilerplate block)
- Source Extract Format (lines 236-276 — the reusable template)

The file should have a header explaining its purpose:

```markdown
# Shared Protocols

These protocols are referenced across multiple pipeline stages. Read this file once at pipeline start and apply these protocols wherever indicated.

---
```

**Step 3: Verify**

Confirm the file exists and contains all 5 protocol sections.

**Step 4: Commit**

```bash
git add template/claude/pipeline/shared-protocols.md
git commit -m "refactor: extract shared protocols from write-paper.md"
```

---

### Task 2: Create stage-1-research.md

**Files:**
- Create: `template/claude/pipeline/stage-1-research.md`

**Step 1: Write stage-1-research.md**

Extract lines 200-563 from current write-paper.md. This includes:
- Stage 1 header and goal
- Agents 1-5 (standard mode)
- Agents 6-12 (deep mode)
- Standard vs deep mode agent dispatch instructions
- Codex Independent Literature Contribution
- Bibliography Builder agent
- Reference count checkpoint

Replace the inline copies of Tool Fallback Chain, Research Log format, Source Extract format, and Provenance instructions with references:

```markdown
**Before reading this stage, ensure you have read `pipeline/shared-protocols.md`.** Use the Tool Fallback Chain, Research Log format, Source Extract format, and Provenance Logging Protocol from that file in every agent prompt below.
```

Keep agent prompts self-contained (they're sent to subagents that can't read other files), but the ORCHESTRATOR instructions at the top of each stage reference shared-protocols.md.

**Step 2: Verify line count is ~360 lines, substantially smaller than the original**

**Step 3: Commit**

```bash
git add template/claude/pipeline/stage-1-research.md
git commit -m "refactor: extract Stage 1 research into pipeline/stage-1-research.md"
```

---

### Task 3: Create stage-1b-snowballing.md

**Files:**
- Create: `template/claude/pipeline/stage-1b-snowballing.md`

**Step 1: Write stage-1b-snowballing.md**

Extract lines 567-674 from current write-paper.md. This includes:
- Stage 1b header and goal
- Seed selection logic
- Backward Snowballing Agent prompt
- Forward Snowballing Agent prompt
- Snowball Bibliography Builder
- Depth mode differences table
- Rate limiting notes
- Checkpoint

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-1b-snowballing.md
git commit -m "refactor: extract Stage 1b snowballing into pipeline/stage-1b-snowballing.md"
```

---

### Task 4: Create stage-1c-codex-crosscheck.md

**Files:**
- Create: `template/claude/pipeline/stage-1c-codex-crosscheck.md`

**Step 1: Write stage-1c-codex-crosscheck.md**

Extract lines 675-700 from current write-paper.md. Short stage — the Codex cross-check. Add reference to shared-protocols.md for the Codex Deliberation Protocol.

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-1c-codex-crosscheck.md
git commit -m "refactor: extract Stage 1c codex crosscheck into pipeline/"
```

---

### Task 5: Create stage-1d-source-acquisition.md

**Files:**
- Create: `template/claude/pipeline/stage-1d-source-acquisition.md`

**Step 1: Write stage-1d-source-acquisition.md**

Extract lines 701-863 from current write-paper.md. This includes:
- Phase 1: Audit
- Phase 2: Automated OA Resolution
- Phase 3: Human Acquisition (MANDATORY pause)
- Phase 4: Update Coverage Report
- Knowledge Graph Build
- Evidence Score Recomputation

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-1d-source-acquisition.md
git commit -m "refactor: extract Stage 1d source acquisition into pipeline/"
```

---

### Task 6: Create stage-2-planning.md

**Files:**
- Create: `template/claude/pipeline/stage-2-planning.md`

**Step 1: Write stage-2-planning.md**

Extract lines 864-962 from current write-paper.md. This includes:
- Thesis and contribution definition
- Paper structure determination
- Detailed outline creation
- Claims-Evidence Matrix building
- Evidence density scoring model and thresholds
- Codex reviews the matrix
- Planning provenance logging
- Checkpoint

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-2-planning.md
git commit -m "refactor: extract Stage 2 planning into pipeline/"
```

---

### Task 7: Create stage-2b-codex-thesis.md

**Files:**
- Create: `template/claude/pipeline/stage-2b-codex-thesis.md`

**Step 1: Write stage-2b-codex-thesis.md**

Extract lines 963-987. Short stage. Add reference to Codex Deliberation Protocol in shared-protocols.md.

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-2b-codex-thesis.md
git commit -m "refactor: extract Stage 2b codex thesis into pipeline/"
```

---

### Task 8: Create stage-2c-targeted-research.md

**Files:**
- Create: `template/claude/pipeline/stage-2c-targeted-research.md`

**Step 1: Write stage-2c-targeted-research.md**

Extract lines 988-1056. Deep mode only. Agents A, B, C with prompts.

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-2c-targeted-research.md
git commit -m "refactor: extract Stage 2c targeted research into pipeline/"
```

---

### Task 9: Create stage-2d-novelty-check.md

**Files:**
- Create: `template/claude/pipeline/stage-2d-novelty-check.md`

**Step 1: Write stage-2d-novelty-check.md**

Extract lines 1057-1091. Novelty verification with search strategy and Codex.

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-2d-novelty-check.md
git commit -m "refactor: extract Stage 2d novelty check into pipeline/"
```

---

### Task 10: Create stage-3-writing.md

**Files:**
- Create: `template/claude/pipeline/stage-3-writing.md`

**Step 1: Write stage-3-writing.md**

Extract lines 1092-1201. This includes:
- Per-section lit searches (deep mode)
- Writing agent requirements (what every prompt MUST include)
- Section writing order table
- Provenance per section
- Codex Limitations Draft
- Section expansion logic
- Codex spot-checks per section
- Deep mode Codex expansion

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-3-writing.md
git commit -m "refactor: extract Stage 3 writing into pipeline/"
```

---

### Task 11: Create stage-4-figures.md

**Files:**
- Create: `template/claude/pipeline/stage-4-figures.md`

**Step 1: Write stage-4-figures.md**

Extract lines 1202-1272. Steps 4a (Praxis), 4b (structural figures), 4c (Codex audit).

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-4-figures.md
git commit -m "refactor: extract Stage 4 figures into pipeline/"
```

---

### Task 12: Create stage-5-qa.md

**Files:**
- Create: `template/claude/pipeline/stage-5-qa.md`

**Step 1: Write stage-5-qa.md**

Extract lines 1273-1427. The QA loop:
- Step 5a: Parallel Review (3 agents + Codex adversarial)
- Step 5b: Synthesize Reviews
- Step 5c: Revision Agent
- Step 5d: Quality Gate Check
- Deep mode final Codex review

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-5-qa.md
git commit -m "refactor: extract Stage 5 QA into pipeline/"
```

---

### Task 13: Create stage-5-post-qa.md

**Files:**
- Create: `template/claude/pipeline/stage-5-post-qa.md`

**Step 1: Write stage-5-post-qa.md**

Extract lines 1428-1528. Post-QA steps that run once:
- Consistency & Claims Audit (parallel)
- Reproducibility Checker
- Reference Validation (+ Codex independent verification)
- Codex Risk Radar

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-5-post-qa.md
git commit -m "refactor: extract Stage 5 post-QA into pipeline/"
```

---

### Task 14: Create stage-6-finalization.md

**Files:**
- Create: `template/claude/pipeline/stage-6-finalization.md`

**Step 1: Write stage-6-finalization.md**

Extract lines 1529-1648. Finalization:
- Final polish agent
- Lay summary
- De-AI Polish
- Final compile
- Provenance Report generation
- Archive command
- Codex collaboration stats

**Step 2: Commit**

```bash
git add template/claude/pipeline/stage-6-finalization.md
git commit -m "refactor: extract Stage 6 finalization into pipeline/"
```

---

### Task 15: Rewrite write-paper.md as orchestrator

**Files:**
- Modify: `template/claude/commands/write-paper.md`

**Step 1: Rewrite write-paper.md**

Replace the entire 1709-line file with a compact orchestrator (~250-300 lines) containing:

1. **Header** — same opening paragraph about autonomous research paper writing
2. **Setup** — same setup steps (read .paper.json, .venue.json, main.tex, mkdir, init logs, init provenance, create tasks, resume check). Mostly unchanged from lines 1-37.
3. **Checkpoint Persistence** — same state file format (lines 39-79). Unchanged.
4. **Depth Mode** — same table (lines 82-97). Unchanged.
5. **Pipeline Execution Instructions** — NEW content:

```markdown
## Pipeline Execution

**CRITICAL**: Before each stage, read its instructions fresh from disk using the Read tool. Do NOT rely on memory of instructions read earlier in the session. This ensures you follow the latest instructions even in long-running sessions where earlier context may be compressed.

At pipeline start, read `pipeline/shared-protocols.md` once. It contains the Codex Deliberation Protocol, Provenance Logging Protocol, Domain Detection & Skill Routing, Tool Fallback Chain, and Source Extract Format. These are referenced throughout the pipeline.

### Stage execution order:

| Stage | File | Skip condition |
|-|-|-|
| 1: Deep Literature Research | `pipeline/stage-1-research.md` | `stages.research.done` |
| 1b: Citation Snowballing | `pipeline/stage-1b-snowballing.md` | `stages.snowballing.done` |
| 1c: Codex Cross-Check | `pipeline/stage-1c-codex-crosscheck.md` | `stages.codex_cross_check.done` |
| 1d: Source Acquisition | `pipeline/stage-1d-source-acquisition.md` | `stages.source_acquisition.done` |
| 2: Planning | `pipeline/stage-2-planning.md` | `stages.outline.done` |
| 2b: Codex Thesis | `pipeline/stage-2b-codex-thesis.md` | `stages.codex_thesis.done` |
| 2c: Targeted Research [DEEP] | `pipeline/stage-2c-targeted-research.md` | `stages.targeted_research.done` OR depth != "deep" |
| 2d: Novelty Check | `pipeline/stage-2d-novelty-check.md` | `stages.novelty_check.done` |
| 3: Writing | `pipeline/stage-3-writing.md` | `stages.writing.done` |
| 4: Figures | `pipeline/stage-4-figures.md` | `stages.figures.done` |
| 5: QA Loop | `pipeline/stage-5-qa.md` | `stages.qa.done` |
| 5-post: Post-QA | `pipeline/stage-5-post-qa.md` | `stages.post_qa.done` |
| 6: Finalization | `pipeline/stage-6-finalization.md` | `stages.finalization.done` |

For each stage:
1. Check `.paper-state.json` — skip if stage is marked done
2. Read the stage file using the Read tool
3. Execute the instructions in the stage file
4. Update `.paper-state.json` with completion status
5. Update `.paper-progress.txt` with human-readable progress
6. Proceed to next stage
```

6. **Quality Criteria** — same table (lines 1651-1674). Unchanged.
7. **Error Handling** — same section (lines 1677-1685). Unchanged.
8. **Rules** — same section (lines 1687-1704). Unchanged.
9. **Topic** — `$ARGUMENTS`

**Step 2: Count lines — target ~250-300 lines**

**Step 3: Verify the orchestrator references every stage file and the file exists**

**Step 4: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "refactor: rewrite write-paper.md as compact orchestrator"
```

---

### Task 16: Update CLAUDE.md

**Files:**
- Modify: `template/claude/CLAUDE.md`

**Step 1: Add pipeline directory to project structure**

Add `pipeline/` to the project structure section in CLAUDE.md:

```
.claude/
  commands/     # Slash commands (30 commands)
  pipeline/     # Stage-specific instructions for /write-paper (read on-demand)
    shared-protocols.md
    stage-1-research.md
    stage-1b-snowballing.md
    ...
  skills/       # -> vendor/claude-scientific-skills (177 scientific skills)
```

**Step 2: Update the pipeline overview**

The "Autonomous Pipeline: /write-paper" section should note that stages are in separate files read on-demand. Brief mention, not a full architectural description.

**Step 3: Commit**

```bash
git add template/claude/CLAUDE.md
git commit -m "docs: update CLAUDE.md with pipeline directory structure"
```

---

### Task 17: Verify integrity

**Step 1: Diff check**

Every line from the original write-paper.md should exist in either:
- The new write-paper.md orchestrator
- One of the pipeline/*.md files
- shared-protocols.md

No content should be lost. Run a rough word count comparison:

```bash
wc -w template/claude/commands/write-paper.md template/claude/pipeline/*.md
```

The sum should be roughly equal to the original (~12K words), possibly slightly more due to cross-reference headers added to each stage file.

**Step 2: Check that every stage file referenced in the orchestrator exists**

```bash
for f in template/claude/pipeline/stage-*.md template/claude/pipeline/shared-protocols.md; do
  [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
```

**Step 3: Commit (if any fixups needed)**

---

### Task 18: Update plan files 01-10

**Files:**
- Modify: `plans/01-citation-snowballing.md`
- Modify: `plans/02-evidence-density-scoring.md`
- Modify: `plans/03-enhanced-source-acquisition.md`
- Modify: `plans/04-knowledge-graph-deep-integration.md`
- Modify: `plans/05-argumentation-framework.md`
- Modify: `plans/06-iterative-research-writing-loop.md`
- Modify: `plans/07-co-citation-analysis.md`
- Modify: `plans/08-qa-iteration-memory.md`
- Modify: `plans/09-methodological-assumptions.md`
- Modify: `plans/10-smaller-improvements.md`

**Step 1: Update "Files to Modify" sections**

In every plan, replace references to `template/claude/commands/write-paper.md` with the specific pipeline stage file(s). Map:

| Plan | Old target | New target(s) |
|-|-|-|
| 01 (Snowballing) | write-paper.md | Already done (Stage 1b exists). Just update CLAUDE.md ref. |
| 02 (Evidence Scoring) | write-paper.md Stage 1d, Stage 2, Stage 3, Stage 5 | `pipeline/stage-1d-source-acquisition.md`, `pipeline/stage-2-planning.md`, `pipeline/stage-3-writing.md`, `pipeline/stage-5-qa.md` |
| 03 (Source Acquisition) | write-paper.md Stage 1d | `pipeline/stage-1d-source-acquisition.md` |
| 04 (Knowledge Graph) | write-paper.md Stages 2, 3, 5, 2c | `pipeline/stage-2-planning.md`, `pipeline/stage-3-writing.md`, `pipeline/stage-5-qa.md`, `pipeline/stage-2c-targeted-research.md` |
| 05 (Argumentation) | write-paper.md Stages 2, 3, 5 | `pipeline/stage-2-planning.md`, `pipeline/stage-3-writing.md`, `pipeline/stage-5-qa.md` |
| 06 (Research-Writing Loop) | write-paper.md Stage 3 | `pipeline/stage-3-writing.md` |
| 07 (Co-Citation) | write-paper.md Stage 1 post | `pipeline/stage-1b-snowballing.md` (add after snowballing) or new `pipeline/stage-1b2-cocitation.md` |
| 08 (QA Memory) | auto.md, write-paper.md Stage 5 | `auto.md`, `pipeline/stage-5-qa.md` |
| 09 (Assumptions) | write-paper.md Stages 2, 3, 5 | `pipeline/stage-2-planning.md` (add 2e), `pipeline/stage-3-writing.md`, `pipeline/stage-5-qa.md` |
| 10 (Smaller) | write-paper.md various | Various pipeline files based on sub-improvement |

**Step 2: Update each plan file's "Files to Modify" and any inline references to write-paper.md**

**Step 3: Commit**

```bash
git add plans/
git commit -m "docs: update plan files with new pipeline file paths"
```

---

## Execution Notes

- This is a pure refactor — no behavior changes. The pipeline should produce identical results before and after.
- The key invariant: every agent prompt (the text inside ``` blocks) must remain identical. Only the orchestrator-level instructions around them change.
- Agent prompts are self-contained (agents can't read files they aren't told to read). The orchestrator instructions reference shared-protocols.md, but agent prompts contain their full instructions inline.
- The shared-protocols.md is read ONCE at pipeline start. It's ~2K tokens and stays in context.
- Each stage file is read fresh before execution. At any point, only ~3K (orchestrator) + ~2K (shared) + ~2-5K (current stage) = ~7-10K tokens of instructions are in active context.
