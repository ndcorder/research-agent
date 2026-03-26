# Auto Phase 4: Verification & Post-Iteration

> **Prerequisites**: Read `pipeline/shared-protocols.md` first. Use its Provenance Logging Protocol throughout this phase.

---

## Phase 4: Verify

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

## Post-Iteration

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
5. **Generate iteration context file** — write `reviews/auto_iter[N]_context.md` for use by the next iteration's assessment agents. Build it from the plan (`reviews/auto_iter[N]_plan.md`), verification report (`reviews/auto_iter[N]_verify.md`), and provenance entries (`research/provenance.jsonl` filtered to `iteration: N`):
   ```markdown
   # Iteration [N] Context

   ## Changes Made
   1. [section/paragraph] — [action: strengthen/cut/rewrite/merge] — [one-line summary]
   2. ...

   ## Deliberate Decisions (kept as-is)
   1. [section/paragraph] — [what was flagged] — [why it was kept]
   2. ...
   [Derive from issues in assessments that were NOT selected for action in the plan, plus any "Deferred" items with explicit reasoning.]

   ## Sections Modified
   - [Section]: [which paragraphs changed]
   - ...

   ## Sections Unchanged Since Last Review
   - [Section] (unchanged since iteration [M])
   - ...

   ## Deferred Issues
   [Copy from reviews/auto_iter[N]_plan.md "Deferred to Next Iteration" section]
   ```
   Keep the file compact — under 500 words. Use bullet points, not prose.
6. **Generate cumulative context (iterations 3+ only)** — if `CURRENT_ITERATION >= 3`, generate `reviews/auto_cumulative_context.md` by merging all individual context files. For iterations 4+, this file replaces individual context files in agent prompts (to keep prompt size manageable):
   ```markdown
   # Cumulative Iteration History

   ## All Deliberate Decisions (across all iterations)
   [Merged from all previous context files. Only keep decisions from the last 2 iterations — older decisions that weren't re-flagged are considered resolved.]

   ## Section Stability
   | Section | Last Modified | Iterations Since Change |
   |-|-|-|
   | Introduction | Iteration 2 | 1 |
   | Related Work | Initial pipeline | 3 (stable) |
   | ... | ... | ... |

   ## Current Deferred Issues
   [Only from the most recent iteration — older deferred issues not re-flagged are considered resolved]
   ```
   Keep the cumulative file under 800 words.
7. **Early stop check** — stop iterations if ANY of these conditions are met:
   - **Low change count**: `changes_made < 3` (existing criterion)
   - **No new issues**: all assessment agents reported no issues beyond those already listed in "Deliberate Decisions" from previous iterations (i.e., nothing genuinely new was found)
   - **Persistent low-priority only**: the only issues found appear in "Deferred Issues" from 2+ consecutive iterations and were deprioritized each time

   When stopping, report:
   ```
   Stopping after iteration [N] — [reason: diminishing returns / no new issues / only persistent low-priority items].
   The paper has stabilized. Remaining minor issues from the assessment are in reviews/auto_iter[N]_plan.md under "Deferred".
   [If persistent low-priority: "Persistent low-priority issues that were never addressed: [list]. These are unlikely to be worth further iteration."]
   ```

## After All Iterations Complete

1. Regenerate the provenance report — spawn a report agent (model: claude-sonnet-4-6[1m]):
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
