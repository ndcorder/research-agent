# Auto-Iterate — Autonomous Paper Improvement

Run N autonomous improvement iterations on a completed paper. Each iteration assesses the paper from multiple angles, prioritizes the highest-impact changes, executes them (including cuts), and verifies no regressions.

**This command is for papers that have already completed the `/write-paper` pipeline (or are otherwise complete).** It does NOT re-run the pipeline — it improves the existing paper.

## Instructions

### Setup

1. Parse $ARGUMENTS:
   - No arguments → run 1 iteration
   - A number (e.g., `3`) → run that many iterations
   - `--continue` → resume from last completed iteration (read `.paper-state.json`)
2. Read `.paper.json` for topic, venue, depth
3. Read `.paper-state.json` for current state. Add `auto_iterations` tracking if not present:
   ```json
   "auto_iterations": {
     "completed": 0,
     "requested": N,
     "history": [
       {
         "iteration": 1,
         "started_at": "...",
         "completed_at": "...",
         "changes_made": 7,
         "cuts_made": 2,
         "research_queries": 1,
         "summary": "Strengthened methods justification, cut redundant discussion paragraph, improved related work positioning"
       }
     ]
   }
   ```
4. Read `main.tex`, `references.bib`, `research/provenance.jsonl`, `research/claims_matrix.md`
5. Run: `mkdir -p provenance/cuts` (in case it doesn't exist)
6. Set `CURRENT_ITERATION` = last completed iteration + 1

### Iteration Loop

For each iteration from `CURRENT_ITERATION` to requested count:

#### Phase 1: Assessment (parallel agents)

Spawn **4 assessment agents in parallel** (model: claude-sonnet-4-6[1m]). Each reads main.tex and writes an assessment to `reviews/auto_iter[N]_[type].md`.

**Agent A — "Depth & Evidence Reviewer"**
```
You are a domain expert assessing the depth and evidence quality of a research paper.
Read main.tex, references.bib, and research/claims_matrix.md completely.
ITERATION: [N] (this paper has already been through the main pipeline + [N-1] improvement iterations)

The claims matrix includes evidence density scores and strength labels (STRONG >= 6, MODERATE 3-5.9, WEAK 1-2.9, CRITICAL < 1). Use these scores to focus your assessment.

Assess:
1. **WEAK and CRITICAL claims first** — these are the highest-priority targets. For each: is the language appropriately hedged? Could evidence be strengthened by finding additional sources or upgrading abstract-only sources to full-text?
2. Which arguments are THIN — stated but not well-supported? Rank by impact on the paper's overall strength.
3. Which claims need STRONGER evidence — additional citations, deeper analysis, more precise data?
4. Are there logical leaps — places where the argument jumps from A to C without establishing B?
5. What would a skeptical expert in this field push back on hardest?
6. Which paragraphs are REDUNDANT or DILUTING stronger surrounding content? Explicitly recommend cuts.
7. Are there paragraphs that restate what's already been said without adding new insight?

For each issue, specify: section, paragraph (approximate), severity (HIGH/MEDIUM/LOW), evidence density score (if claim-related), and suggested action (strengthen/cut/rewrite/merge).

IMPORTANT: Cutting weak content is as valuable as adding strong content. Recommend cuts explicitly.
IMPORTANT: Strengthening a WEAK claim from 2.0 to 6.0 is higher priority than polishing prose in a section with all STRONG claims.

Write assessment to reviews/auto_iter[N]_depth.md.
```

**Agent B — "Structure & Flow Reviewer"**
```
You are a senior editor assessing the structural quality of a research paper.
Read main.tex completely.
ITERATION: [N]

Assess:
1. Does the argument flow logically from section to section? Are there jarring transitions?
2. Is any section disproportionately long or short relative to its importance?
3. Are subsections well-organized? Would reordering improve readability?
4. Does the Introduction adequately set up what the paper delivers? Does the Conclusion match?
5. Is the paper front-loaded with the most important information, or does the key insight come too late?
6. Are there sections or paragraphs that could be MERGED to eliminate redundancy?
7. Are there places where SPLITTING a dense paragraph would improve readability?

For each issue, specify: location, severity, and concrete suggestion.

Write assessment to reviews/auto_iter[N]_structure.md.
```

**Agent C — "Competitive Positioning Reviewer"**
```
You are a peer reviewer assessing how well this paper positions itself against prior work.
Read main.tex and references.bib completely.
ITERATION: [N]

Assess:
1. Is the contribution clearly differentiated from the closest prior work?
2. Are comparisons with baselines fair and comprehensive?
3. Is the Related Work section current — any important recent papers (2024-2026) missing?
4. Does the paper acknowledge limitations of its own approach relative to alternatives?
5. Would a reviewer familiar with [TOPIC] feel the authors know the field well?

If you identify missing recent work, note the gap but do NOT fabricate citations.
Suggest at most 3 targeted searches that might fill identified gaps.

Write assessment to reviews/auto_iter[N]_positioning.md.
```

**Agent D — "Writing & Polish Reviewer"**
```
You are a prose quality editor reviewing a research paper.
Read main.tex completely.
ITERATION: [N]

Assess:
1. Are there em dashes (— or –) used as punctuation? Flag ALL of them — they must be replaced.
2. Are there remaining AI writing patterns? (See de-AI polish categories: filler phrases, AI vocabulary, formulaic transitions, redundant phrasing, empty emphasis, structural tells)
3. Is the prose engaging or monotonous? Are sentence lengths varied?
4. Are there vague statements that could be made precise?
5. Is there unnecessary hedging that weakens claims the evidence supports?
6. Are there places where the writing is MORE cautious than the evidence warrants? (Under-claiming is also a problem.)
7. Can any sentences be CUT entirely without losing information?

For each issue, provide the exact text and a suggested rewrite or cut.

Write assessment to reviews/auto_iter[N]_writing.md.
```

**Codex Assessment (parallel with agents above)**

If codex-bridge is available, also call Codex directly:

```
mcp__codex-bridge__codex_review({
  prompt: "This paper has completed its initial pipeline and is now in iteration [N] of autonomous improvement. Read it with fresh eyes. What are the 5 highest-impact improvements that would make this paper more publishable? Consider: argument strength, evidence gaps, structural issues, prose quality, and content that should be CUT. Be specific and prioritize ruthlessly — we can only make 3-5 changes per iteration.",
  context: "[paste full main.tex]",
  evidence_mode: true
})
```

Write to `reviews/auto_iter[N]_codex.md`. Apply the Codex Deliberation Protocol.

#### Phase 2: Prioritize

After all assessment agents complete, read ALL assessment files for this iteration. Build a **prioritized action list**:

1. Read all `reviews/auto_iter[N]_*.md` files and `research/claims_matrix.md` (for evidence density scores)
2. Collect all issues across reviewers, deduplicate similar findings
3. Rank by impact, using evidence density scores as a tiebreaker: actions that strengthen WEAK/CRITICAL claims (moving them toward MODERATE/STRONG) outrank polish actions on sections with all STRONG claims
4. Select the **top 5 actions** for this iteration. Mix of:
   - Strengthening (rewrite, expand, add evidence — prioritize WEAK/CRITICAL claims)
   - Cutting (remove redundant/weak content)
   - Structural (reorder, merge, split)
   - Polish (prose improvements, em dash removal)
5. Write the action plan to `reviews/auto_iter[N]_plan.md`:
   ```markdown
   # Iteration [N] Action Plan

   ## Selected Actions (ranked by impact)

   ### Action 1: [title]
   - **Type**: strengthen / cut / restructure / polish
   - **Target**: [section/paragraph]
   - **From reviewers**: [which assessment(s) flagged this]
   - **What to do**: [specific instruction]
   - **Research needed**: yes/no (if yes, what to search for)

   ### Action 2: ...

   ## Deferred to Next Iteration
   [List MEDIUM issues not selected — these feed into the next iteration's assessment]
   ```

If 3 or fewer meaningful actions were identified across ALL reviewers, trigger **early stop**: skip execution, log the reason, and end the iteration loop.

#### Phase 3: Execute

**Research phase (if needed, max 3 queries)**

If any selected action requires new evidence, spawn a targeted research agent (model: claude-sonnet-4-6[1m]):
```
You are a targeted research agent for iteration [N] of paper improvement.
TOPIC: [TOPIC]
DOMAIN: [DOMAIN]
TOOL FALLBACK: domain databases → Perplexity → WebSearch → Firecrawl → research-lookup. Try at least 3 tools.

Search for SPECIFIC evidence to support these improvements:
[paste only the actions that need research]

You have a budget of 3 searches maximum. Be precise — we know exactly what we need.
Write findings to research/auto_iter[N]_research.md.
Add any new references to references.bib.
RESEARCH LOG: Append entries to research/log.md.
Create source extracts in research/sources/ for any new papers.
```

**Revision phase**

Spawn a revision agent (model: claude-opus-4-6[1m]):
```
You are improving a research paper in iteration [N] of autonomous improvement.
Invoke the `scientific-writing` skill.
Read main.tex, references.bib, and the action plan at reviews/auto_iter[N]_plan.md.
[If research was done: Also read research/auto_iter[N]_research.md]

Execute EVERY action in the plan. For each action:
1. Make the change in main.tex (and references.bib if needed)
2. For CUTS: save removed text to provenance/cuts/[section]-[pN]-auto[N].tex BEFORE deleting
3. Maintain consistency with surrounding text — update transitions, cross-references

Writing rules:
- No em dashes (—) or en dashes (–) as punctuation. Use commas, parentheses, colons, or separate sentences.
- No AI writing patterns (delve, tapestry, realm, multifaceted, furthermore/moreover at sentence starts)
- Full paragraphs only, flowing academic prose
- Do NOT add filler to compensate for cuts — if you remove a paragraph, the surrounding text should still flow

After all changes, compile: latexmk -pdf -interaction=nonstopmode main.tex
Fix any LaTeX errors.

PROVENANCE — After EACH change, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"auto","agent":"auto-revision","action":"[revise|cut|add|expand|reorder]","target":"[section/pN]","reasoning":"[why — reference the action plan item]","feedback_ref":"reviews/auto_iter[N]_plan.md#action-[M]","diff_summary":"[what changed]","sources":["keys"],"iteration":[N]}
For cuts: set archived_to to the path where you saved the removed text.
```

#### Phase 4: Verify

After the revision agent completes, run a lightweight verification (model: claude-sonnet-4-6[1m]):

```
You are a verification agent checking that iteration [N] improvements didn't introduce regressions.
Read main.tex and references.bib.
Also read reviews/auto_iter[N]_plan.md to know what was changed.

Quick checks:
1. LaTeX compiles without errors: latexmk -pdf -interaction=nonstopmode main.tex
2. All \citep{}/\citet{} keys exist in references.bib
3. All \ref{} cross-references resolve
4. No placeholder text (TODO, TBD, FIXME)
5. No bullet points in body text
6. No em dashes used as punctuation
7. The changes didn't break surrounding context (read paragraphs before/after each changed location)
8. No new AI writing patterns introduced

Report any issues found. If CRITICAL issues exist (broken references, compilation errors), fix them directly in main.tex.
Write verification report to reviews/auto_iter[N]_verify.md.
```

#### Post-Iteration

1. **Recompute evidence density scores** — if any actions added new evidence, upgraded source access levels, or changed claims, recompute scores in `research/claims_matrix.md` using the scoring model from Stage 2 step 5 of `/write-paper`. This keeps the heatmap current for the next iteration's assessment.
2. Count the changes made in this iteration (from the provenance ledger entries with `iteration: N`)
3. Update `.paper-state.json`:
   ```json
   "auto_iterations": {
     "completed": N,
     "requested": [original request],
     "history": [..., {"iteration": N, "started_at": "...", "completed_at": "...", "changes_made": X, "cuts_made": Y, "research_queries": Z, "summary": "..."}]
   }
   ```
4. Update `.paper-progress.txt`: "Auto iteration [N]/[total] complete: [summary of changes]"
5. **Early stop check**: if `changes_made < 3`, stop iterations and report:
   ```
   Stopping after iteration [N] — diminishing returns (only [X] meaningful changes found).
   The paper has stabilized. Remaining minor issues from the assessment are in reviews/auto_iter[N]_plan.md under "Deferred".
   ```

### After All Iterations Complete

1. Regenerate the provenance report — spawn a report agent (model: haiku):
   ```
   Read research/provenance.jsonl completely. Generate an updated research/provenance_report.md
   covering ALL actions including auto-iterations. Group the report by stage, with auto-iterations
   as a separate section showing what changed in each iteration and why.
   ```

2. Run a final compile: `latexmk -pdf -interaction=nonstopmode main.tex`

3. Report to the user:
   ```
   Completed [N] improvement iterations.

   Iteration 1: [summary] ([X] changes, [Y] cuts)
   Iteration 2: [summary] ([X] changes, [Y] cuts)
   ...

   Total changes: [sum]
   Total cuts: [sum]
   New references added: [count]

   The provenance report has been updated: research/provenance_report.md
   Cut content is archived in: provenance/cuts/
   ```

## Rules

1. **Never touch the thesis.** The contribution statement in research/thesis.md is fixed. Improve execution, not the research question.
2. **Cuts are first-class.** Every assessment agent must explicitly consider what to remove. A paper that says less but says it better is an improvement.
3. **Cap research.** Maximum 3 targeted searches per iteration. This is about improving what exists, not starting new research threads.
4. **No em dashes.** Enforce Writing Rule #11 in every agent prompt.
5. **Log everything.** Every change gets a provenance entry. Every cut gets archived.
6. **Early stop is good.** Stopping because the paper is strong is a success, not a failure.
7. **Model selection.** Assessment and verification: claude-sonnet-4-6[1m]. Revision: claude-opus-4-6[1m]. Report generation: haiku.
8. **Don't fight the last war.** Each iteration's assessment is fresh — don't just re-check what the last iteration changed. Read the whole paper with fresh eyes.

## Arguments

$ARGUMENTS
