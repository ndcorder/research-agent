# Expand Codex Bridge Integration Across All Pipeline Stages

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Weave Codex Bridge (`codex_ask`, `codex_review`, `codex_plan`, `codex_risk_radar`, `codex_stats`) into every stage of the write-paper pipeline — not just Stages 2b and 5.

**Architecture:** Add Codex calls at 5 new integration points in write-paper.md. All calls are made directly by the orchestrator (not by subagents) so they run in parallel with agent work. Each new Codex step writes its output to a file in `research/` or `reviews/` and has a checkpoint assertion. The setup header is updated to list all tools/stages.

**Tech Stack:** Markdown command files (Claude Code slash commands). MCP tools: `mcp__codex-bridge__codex_ask`, `mcp__codex-bridge__codex_review`, `mcp__codex-bridge__codex_plan`, `mcp__codex-bridge__codex_risk_radar`, `mcp__codex-bridge__codex_stats`.

---

### Task 1: Update Setup header to list all Codex integration points

**Files:**
- Modify: `template/claude/commands/write-paper.md:7-8`

**Step 1: Replace the Codex Bridge line in the Setup section**

Find (line 8):
```
- **Codex Bridge** (`mcp__codex-bridge__codex_plan`, `mcp__codex-bridge__codex_review`): Call at Stage 2 (thesis stress-test) and Stage 5 (adversarial review). These are MCP tools — call them directly in your session.
```

Replace with:
```
- **Codex Bridge** (`codex_plan`, `codex_review`, `codex_ask`, `codex_risk_radar`, `codex_stats`): Used throughout the pipeline as a second AI perspective. Call these MCP tools (`mcp__codex-bridge__*`) directly in your session — NOT via agents. Integration points: Stage 1 (research cross-check), Stage 2b (thesis stress-test), Stage 3 (section spot-checks), Stage 4 (figure/claims audit), Stage 5 (adversarial review), Post-QA (risk radar), Stage 6 (collaboration stats).
```

**Step 2: Verify**

Run: `grep -n "codex_risk_radar\|codex_stats\|codex_ask" template/claude/commands/write-paper.md | head -5`
Expected: line 8 match.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Update Codex Bridge setup header to list all integration points"
```

---

### Task 2: Add Stage 1c — Codex Research Cross-Check

**Files:**
- Modify: `template/claude/commands/write-paper.md` — insert after the Bibliography Builder checkpoint (after line ~283 `---`)

**Step 1: Insert new stage between Stage 1 checkpoint and Stage 2**

Find the line:
```
**Checkpoint**: Count entries in `references.bib`. If fewer than 25, report which research areas are underrepresented and spawn additional targeted research agents for those areas.

---

### Stage 2: Thesis, Contribution & Outline
```

Replace with:
```
**Checkpoint**: Count entries in `references.bib`. If fewer than 25, report which research areas are underrepresented and spawn additional targeted research agents for those areas.

---

### Stage 1c: Codex Research Cross-Check

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

After all research agents and bibliography building are complete, use Codex to cross-check the key findings.

1. Read `research/survey.md` and `research/gaps.md` for the main claims and findings
2. Call Codex directly:

```
mcp__codex-bridge__codex_ask({
  prompt: "Cross-check these research findings. For each major claim below, assess: (1) Is it accurately represented based on your knowledge? (2) Are there important contradicting studies or nuances missing? (3) Are there key papers or perspectives that were overlooked? (4) Flag any claims that seem exaggerated or out of context.\n\nResearch findings:\n[paste key claims from survey.md and gaps.md]",
  context: "[paste content of research/survey.md and research/gaps.md]"
})
```

3. Write the Codex response to `research/codex_cross_check.md`
4. If Codex identifies missing perspectives or inaccurate claims, spawn a **targeted follow-up research agent** (model: sonnet) to investigate those specific gaps. The agent should update the relevant research files and add any new references to `references.bib`.

**Checkpoint**: Verify `research/codex_cross_check.md` exists. If it does not exist, you skipped this stage — go back and do it.

Update `.paper-state.json`: mark `codex_cross_check` as done.

---

### Stage 2: Thesis, Contribution & Outline
```

**Step 2: Verify**

Run: `grep -n "Stage 1c\|codex_cross_check\|codex_ask" template/claude/commands/write-paper.md | head -10`
Expected: Stage 1c header, codex_cross_check file references, codex_ask call.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add Stage 1c: Codex research cross-check after literature review"
```

---

### Task 3: Add Stage 3 — Codex Section Spot-Checks

**Files:**
- Modify: `template/claude/commands/write-paper.md` — insert into Stage 3, after the expansion agent block

**Step 1: Add Codex spot-check after each section**

Find the block that ends with:
```
Target: [TARGET]+ words total for this section.
Edit main.tex directly.
```

After that closing ``` and before the `---` that starts Stage 4, add:

```

**After each major section completes (Introduction, Methods, Results, Discussion)**, also call Codex for a quick spot-check. Do NOT do this for Related Work, Conclusion, or Abstract — only the 4 core argument sections.

```
mcp__codex-bridge__codex_review({
  prompt: "Quick review of the [SECTION] section of a research paper. Check: (1) Are the claims proportionate to the evidence presented? (2) Is the logic sound — does each paragraph follow from the previous? (3) Are there any obvious gaps a reviewer would flag? (4) Is the technical depth appropriate? Keep your review focused and concise — this is a section check, not a full paper review.",
  context: "[paste the section content from main.tex]",
  evidence_mode: true
})
```

Write each spot-check to `reviews/codex_section_[SECTION].md` (e.g., `reviews/codex_section_introduction.md`). If Codex finds CRITICAL issues, fix them in main.tex before moving to the next section. MAJOR issues can wait for Stage 5.
```

**Step 2: Verify**

Run: `grep -n "codex_section\|spot-check" template/claude/commands/write-paper.md | head -5`
Expected: matches in Stage 3.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add Codex section spot-checks during Stage 3 writing"
```

---

### Task 4: Add Stage 4c — Codex Figure/Claims Audit

**Files:**
- Modify: `template/claude/commands/write-paper.md` — insert after Step 4b, before the `---` divider to Stage 5

**Step 1: Add Codex figure/claims audit**

Find the lines:
```
Add any new figures to main.tex with proper \includegraphics{} and \caption{}.
Edit main.tex directly.
```

After that closing ```, add:

```

**Step 4c: Codex Figure & Claims Audit**

After figures and tables are in place, call Codex to sanity-check the visual claims:

```
mcp__codex-bridge__codex_ask({
  prompt: "Audit the figures, tables, and their associated claims in this manuscript. For each figure/table: (1) Does the caption accurately describe what is shown? (2) Do the claims in the surrounding text match what the data actually shows? (3) Are there misleading axis scales, cherry-picked comparisons, or missing error bars/confidence intervals? (4) Are any figures redundant or better presented as tables (or vice versa)?",
  context: "[paste the Results and Discussion sections from main.tex, including all figure/table environments]"
})
```

Write the response to `reviews/codex_figures_audit.md`. Fix any critical mismatches between figures and claims in main.tex immediately.
```

**Step 2: Verify**

Run: `grep -n "Step 4c\|codex_figures_audit" template/claude/commands/write-paper.md | head -5`
Expected: matches for the new step.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add Step 4c: Codex figure and claims audit after visual elements"
```

---

### Task 5: Add Post-QA — Codex Risk Radar

**Files:**
- Modify: `template/claude/commands/write-paper.md` — insert after the reference validation section, before Stage 6

**Step 1: Add Codex risk radar step**

Find:
```
**This is non-negotiable.** Fabricated references are the #1 risk in AI-assisted writing. Every reference must be verified before the paper is finalized. Update `.paper-state.json` with validation results.

---

### Stage 6: Finalization
```

Replace with:
```
**This is non-negotiable.** Fabricated references are the #1 risk in AI-assisted writing. Every reference must be verified before the paper is finalized. Update `.paper-state.json` with validation results.

---

### Post-QA: Codex Risk Radar

**Run this ONCE after reference validation, before finalization.**

Use Codex's risk radar tool to get a final risk assessment of the complete manuscript:

```
mcp__codex-bridge__codex_risk_radar({
  prompt: "Final risk assessment of this research manuscript before submission. Evaluate across these dimensions: (1) SCIENTIFIC RISK — are there claims that could be proven wrong or are unfalsifiable? (2) ETHICAL RISK — any issues with data handling, consent, bias, or dual-use concerns? (3) REPUTATIONAL RISK — anything that could embarrass the authors if scrutinized? (4) REPRODUCIBILITY RISK — could an independent team reproduce these results from the description? (5) NOVELTY RISK — is the contribution incremental enough that reviewers might desk-reject? Rate each dimension: LOW / MEDIUM / HIGH with specific evidence.",
  context: "[paste the full content of main.tex]"
})
```

Write the response to `reviews/codex_risk_radar.md`.

**Action on results:**
- Any HIGH risk item → must be addressed before finalization. Edit main.tex to mitigate (add caveats, strengthen methods, etc.)
- MEDIUM risk items → flag for the user's attention in the final report but don't block finalization
- LOW risk items → note and move on

**Checkpoint**: Verify `reviews/codex_risk_radar.md` exists.

Update `.paper-state.json`: mark `codex_risk_radar` as done.

---

### Stage 6: Finalization
```

**Step 2: Verify**

Run: `grep -n "Risk Radar\|codex_risk_radar" template/claude/commands/write-paper.md | head -5`
Expected: header and file references.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add Post-QA Codex Risk Radar assessment before finalization"
```

---

### Task 6: Add Codex Stats to Stage 6 Finalization

**Files:**
- Modify: `template/claude/commands/write-paper.md` — insert into Stage 6, after the archive step

**Step 1: Add codex_stats call**

Find the line:
```
Finally, **archive all research artifacts** by running the `/archive` command. This creates a self-contained `archive/` directory with all research notes, reviews, figures, data, and metadata organized for easy browsing, with a README index. This allows the user to browse through all research findings, downloaded materials, and intermediate outputs after the pipeline completes.
```

After it, add:

```

**Report Codex collaboration metrics:**

```
mcp__codex-bridge__codex_stats({})
```

Include the Codex stats in the final completion report to show how the two AI systems collaborated throughout the pipeline.
```

**Step 2: Verify**

Run: `grep -n "codex_stats" template/claude/commands/write-paper.md | head -5`
Expected: match in Stage 6 and in the setup header.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add Codex collaboration stats to Stage 6 finalization"
```

---

### Task 7: Update checkpoint state schema

**Files:**
- Modify: `template/claude/commands/write-paper.md:31-52` — the `.paper-state.json` example

**Step 1: Add new Codex stage fields to the JSON example**

Find the JSON block in the Checkpoint Persistence section. Replace the `stages` object with an updated version that includes the new Codex stages:

Find:
```json
    "codex_thesis": { "done": true,  "completed_at": "...", "file": "research/codex_thesis_review.md" },
    "writing": {
```

Replace with:
```json
    "codex_cross_check": { "done": true, "completed_at": "...", "file": "research/codex_cross_check.md" },
    "codex_thesis": { "done": true,  "completed_at": "...", "file": "research/codex_thesis_review.md" },
    "writing": {
```

Then find:
```json
    "qa":           { "done": false },
```

Replace with:
```json
    "qa":           { "done": false },
    "codex_risk_radar": { "done": false },
```

**Step 2: Verify**

Run: `grep -n "codex_cross_check\|codex_risk_radar" template/claude/commands/write-paper.md | head -5`
Expected: matches in the JSON block.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add new Codex stages to checkpoint state schema"
```

---

### Task 8: Update CLAUDE.md Codex Bridge documentation

**Files:**
- Modify: `template/claude/CLAUDE.md`

**Step 1: Update the Codex Bridge Integration section**

Find:
```
## Codex Bridge Integration

If `codex-bridge` is installed (`npm i -g codex-bridge`), it provides adversarial AI review via OpenAI Codex:

- **Thesis stress-testing** (Stage 2): `codex_plan` challenges your contribution statement before you write
- **Adversarial review** (Stage 5): `codex_review` runs alongside the 3 agent reviewers as a 4th perspective
- **On-demand critique**: `/codex-review` for manual review of any section
```

Replace with:
```
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
```

**Step 2: Verify**

Run: `grep -c "codex" template/claude/CLAUDE.md`
Expected: higher count than before (was ~10, should now be ~15+).

**Step 3: Commit**

```bash
git add template/claude/CLAUDE.md
git commit -m "Update CLAUDE.md with expanded Codex Bridge integration points"
```

---

### Task 9: Update /archive to include new Codex review files

**Files:**
- Modify: `template/claude/commands/archive.md`

**Step 1: The archive already copies all files from `reviews/` and `research/`**

Read the archive command and verify that the existing copy instructions (`Copy all files from reviews/` and `Copy all files from research/`) will automatically pick up the new files:
- `research/codex_cross_check.md`
- `reviews/codex_section_*.md`
- `reviews/codex_figures_audit.md`
- `reviews/codex_risk_radar.md`

Since archive.md already says "Copy all files from `research/` → `archive/research/`" and "Copy all files from `reviews/` → `archive/reviews/`", the new Codex files will be included automatically. **No changes needed.**

**Step 2: Verify**

Run: `grep "Copy all files from" template/claude/commands/archive.md`
Expected: shows the research/ and reviews/ copy-all lines.

**Step 3: Skip commit — no changes.**

---

### Task 10: Final Verification

**Step 1: Count all Codex integration points in write-paper.md**

Run:
```bash
echo "=== Codex tool calls ===" && grep -c "mcp__codex-bridge" template/claude/commands/write-paper.md && echo "=== Stage headers with Codex ===" && grep -n "Codex\|codex" template/claude/commands/write-paper.md | grep -i "stage\|step\|post-qa" | head -20
```

Expected: 7+ MCP tool calls (setup list doesn't count). Stage/step references at: 1c, 2b, 3, 4c, 5a-ii, Post-QA risk radar, 6.

**Step 2: Verify all output files are referenced**

Run:
```bash
grep -n "codex_cross_check\|codex_section_\|codex_figures_audit\|codex_risk_radar\|codex_stats\|codex_thesis_review\|codex_adversarial" template/claude/commands/write-paper.md | head -20
```

Expected: all 7 file types referenced.

**Step 3: Verify CLAUDE.md lists all integration points**

Run: `grep -c "Stage\|stage" template/claude/CLAUDE.md`
Expected: increased from baseline.
