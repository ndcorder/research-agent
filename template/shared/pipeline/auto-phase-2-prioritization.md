# Auto Phase 2: Prioritization

> **Prerequisites**: Read `pipeline/shared-protocols.md` first. Use its Provenance Logging Protocol throughout this phase.

---

## Phase 2: Prioritize

After all assessment agents complete, read ALL assessment files for this iteration. Build a **prioritized action list**:

1. Read all `reviews/auto_iter[N]_*.md` files (including `_regressions.md` if it exists) and `research/claims_matrix.md` (for evidence density scores)
2. Collect all issues across reviewers, deduplicate similar findings. **Regressions from Agent E get automatic HIGH priority** — fixes that undo damage from the last iteration come before new improvements
3. Rank by impact, using evidence density scores as a tiebreaker: regressions first, then actions that strengthen WEAK/CRITICAL claims (moving them toward MODERATE/STRONG), then polish actions on sections with all STRONG claims
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

**Evidence-impact prioritization**: When ranking improvements:
1. CRITICAL claims (score < 1) that survived to this point -> P0 (find evidence or remove)
2. WEAK claims (score 1-2.9) backing central thesis claims -> P1 (targeted research)
3. WEAK claims in non-central sections -> P2 (hedge language fix)
4. Missing/Invalid warrants -> P1 (structural argument fix)
5. Prose quality on STRONG claims -> P3 (polish only after evidence issues resolved)

Run `python scripts/quality.py score --project .` before and after each /auto iteration. Log the delta in `.paper-state.json` under `auto_iterations.history[N].score_delta`.

If 3 or fewer meaningful actions were identified across ALL reviewers, trigger **early stop**: skip execution, log the reason, and end the iteration loop.
