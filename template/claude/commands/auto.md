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

**CRITICAL**: Before each phase, read its instructions fresh from disk using the Read tool. Do NOT rely on memory of instructions read earlier in the session. This ensures you follow the latest, complete instructions even in long-running sessions where earlier context may be compressed.

For each iteration from `CURRENT_ITERATION` to requested count, execute the phases in order:

| Order | Phase | File to Read |
|-|-|-|
| 1 | Assessment | `pipeline/auto-phase-1-assessment.md` |
| 2 | Prioritization | `pipeline/auto-phase-2-prioritization.md` |
| 3 | Execution | `pipeline/auto-phase-3-execution.md` |
| 4 | Verification & Post-Iteration | `pipeline/auto-phase-4-verification.md` |

For each phase:
1. **Read the phase file** from `pipeline/` using the Read tool (fresh from disk)
2. Execute the instructions in the phase file, substituting `[N]` with the current iteration number
3. After Phase 2: if early stop was triggered (3 or fewer meaningful actions), skip Phases 3-4 and end the loop
4. After Phase 4: check the early stop conditions in the post-iteration section; if met, end the loop

After all iterations complete (or early stop), execute the "After All Iterations Complete" section from Phase 4.

## Rules

1. **Never touch the thesis.** The contribution statement in research/thesis.md is fixed. Improve execution, not the research question.
2. **Cuts are first-class.** Every assessment agent must explicitly consider what to remove. A paper that says less but says it better is an improvement.
3. **Cap research.** Maximum 3 targeted searches per iteration. This is about improving what exists, not starting new research threads.
4. **No em dashes.** Enforce Writing Rule #11 in every agent prompt.
5. **Log everything.** Every change gets a provenance entry. Every cut gets archived.
6. **Early stop is good.** Stopping because the paper is strong is a success, not a failure.
7. **Model selection.** Assessment, verification, and report generation: claude-sonnet-4-6[1m]. Revision: claude-opus-4-6[1m]. Never use Haiku.
8. **Fresh eyes, informed by context.** Each iteration's assessment reads the whole paper — the iteration context helps agents avoid re-litigating settled decisions and focus on regressions, but it does NOT replace reading the full manuscript. Agents should still find new issues, not just check the last iteration's work.

## Arguments

$ARGUMENTS
