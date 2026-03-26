# Plan 08: QA Iteration Memory

## Problem

In the `/auto` improvement loop, each iteration spawns fresh assessment agents that re-read the whole paper without context about what previous iterations changed or decided. This causes three problems:

1. **Re-flagging resolved issues** — An agent flags something that was deliberately kept after deliberation in a previous iteration
2. **Missing regressions** — Agents don't know what changed, so they can't specifically check if previous fixes held
3. **Wasted effort on stable sections** — Agents spend time on sections that haven't changed and were already validated

## Goal

Give each `/auto` iteration's assessment agents context about previous iterations: what was changed, what was deliberately kept, and which sections were modified, so they can focus on new issues and regression detection.

## Design

### Iteration Context File

After each `/auto` iteration completes, generate `reviews/auto_iter[N]_context.md` — a compact summary of what happened:

```markdown
# Iteration [N] Context

## Changes Made
1. [section/paragraph] — [action: strengthen/cut/rewrite/merge] — [one-line summary]
2. ...

## Deliberate Decisions (kept as-is)
1. [section/paragraph] — [what was flagged] — [why it was kept: e.g., "Codex suggested removing but reasoning was sound"]
2. ...

## Sections Modified
- Introduction: paragraphs 2, 5
- Methods: paragraph 3 (new subsection added)
- Discussion: paragraph 7 (cut), paragraph 8 (rewritten)

## Sections Unchanged Since Last Review
- Related Work (unchanged since iteration [N-1])
- Results (unchanged since iteration [N-2])
- Conclusion (unchanged since initial pipeline)

## Deferred Issues
[From reviews/auto_iter[N]_plan.md "Deferred to Next Iteration" section]
```

This file is generated from:
- `reviews/auto_iter[N]_plan.md` (what was planned)
- `reviews/auto_iter[N]_verify.md` (what was verified)
- `research/provenance.jsonl` (what actually changed, filtered by `iteration: N`)

### Assessment Agent Changes

Each assessment agent in iteration N+1 receives the context file from iteration N:

```
ITERATION CONTEXT — This paper has been through [N] improvement iterations.
Read reviews/auto_iter[N]_context.md for what was changed and decided in the last iteration.

Rules:
1. Do NOT re-flag issues that appear in "Deliberate Decisions" unless you have NEW reasoning
2. DO check "Sections Modified" for regressions — did the changes hold up? Did they break anything?
3. SKIP "Sections Unchanged" for deep analysis — do a quick scan only, focus your attention on modified sections and any issues from "Deferred Issues"
4. If something from "Deferred Issues" is still present, escalate its priority
```

### Regression Detection

Add a new lightweight agent to each iteration (model: haiku) that specifically checks regressions:

```
You are a regression detector for iteration [N+1].
Read reviews/auto_iter[N]_context.md for what changed in the last iteration.
Read main.tex.

For each change listed in "Changes Made":
1. Read the modified section/paragraph
2. Check: does the change still make sense in context? Did it break transitions with surrounding text?
3. Check: did the change introduce any new issues (AI patterns, citation errors, logical gaps)?
4. Check: is the change consistent with changes made elsewhere in the same iteration?

Report only REGRESSIONS — things that got worse because of the last iteration's changes.
Write to reviews/auto_iter[N+1]_regressions.md (empty file if no regressions).
```

This runs in parallel with the 4 assessment agents and feeds into the prioritization phase.

### Cumulative Context (for iterations 3+)

By iteration 3+, context from a single previous iteration isn't enough. Generate a cumulative summary:

```markdown
# Cumulative Iteration History

## All Deliberate Decisions (across all iterations)
[merged from all previous context files — these are decisions the pipeline has already considered and rejected changing]

## Section Stability
| Section | Last Modified | Iterations Since Change |
|-|-|-|
| Introduction | Iteration 2 | 1 |
| Related Work | Initial pipeline | 3 (stable) |
| Methods | Iteration 1 | 2 |
| Results | Iteration 3 | 0 (just changed) |

## Current Deferred Issues
[only from the most recent iteration — older deferred issues that weren't re-flagged are considered resolved]
```

For iterations 4+, this cumulative context replaces individual iteration contexts (to keep prompt size manageable).

### Early Stop Enhancement

The current early stop triggers when `changes_made < 3`. Enhance with context awareness:
- If all assessment agents report "no new issues beyond previous deliberate decisions" → early stop
- If the only issues found are in "Deferred Issues" from 2+ iterations ago and they were deprioritized each time → early stop with a note about persistent low-priority issues

## Files to Modify

1. `template/claude/commands/auto.md`:
   - Post-iteration: generate `reviews/auto_iter[N]_context.md`
   - Assessment agents: add iteration context to prompts
   - Add regression detection agent (parallel with assessment)
   - For iterations 3+: generate cumulative context
   - Enhanced early stop criteria
2. `template/claude/pipeline/stage-5-qa.md`:
   - QA loop: similar context passing between QA iterations (the QA loop has the same problem, just less severe because it's max 5-8 iterations)

## Files to Create

None — context files are generated per-iteration at runtime.

## Risks

- Context files add to prompt length. Mitigation: keep them compact (bullet points, not prose). Cap at 500 words for individual context, 800 for cumulative.
- "Deliberate decisions" may become stale as the paper evolves. Mitigation: cumulative context only keeps decisions from the last 2 iterations.
- Agents may over-rely on "skip unchanged sections" and miss latent issues. Mitigation: "quick scan" not "skip entirely" — they still read the sections, just don't deep-analyze them.

## Acceptance Criteria

- [ ] Each `/auto` iteration generates a context file
- [ ] Assessment agents receive and respect the context file
- [ ] Agents don't re-flag deliberate decisions without new reasoning
- [ ] Regression detection agent runs each iteration
- [ ] Cumulative context generated for iterations 3+
- [ ] Enhanced early stop criteria using context awareness
- [ ] Context files are compact (< 800 words for cumulative)
- [ ] Same approach applied to Stage 5 QA loop iterations
