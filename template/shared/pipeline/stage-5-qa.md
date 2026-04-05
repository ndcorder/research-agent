# Stage 5: Quality Assurance Loop

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Codex Deliberation Protocol.

---

**This stage LOOPS until all quality criteria pass or convergence is detected.** Initial maximum: 5 iterations (or 8 if depth is `"deep"`). The adaptive iteration system may adjust this after iteration 1 (see Step 5d).

Track `QA_ITERATION` starting at 1, incrementing each time the loop repeats from Step 5d back to Step 5a.

Initialize convergence tracking in `.paper-state.json` at the start of the QA stage (if not already present):
```json
"qa": {
  "done": false,
  "max_iterations": 5,
  "converged_at": null,
  "convergence_reason": null,
  "iterations": []
}
```
Set `max_iterations` to 5 (standard) or 8 (deep). This value may be adjusted after iteration 1.

#### Step 5a: Parallel Review

**Load QA iteration context (iterations 2+):** If `QA_ITERATION > 1`, read the context file from the previous iteration:
- For iterations 2-3: read `reviews/qa_iter[QA_ITERATION-1]_context.md`
- For iterations 4+: read `reviews/qa_cumulative_context.md`

Store the contents as `QA_CONTEXT`. If the context file doesn't exist, skip — agents run without context as before. Prepend the following block to EVERY review agent prompt below:

```
QA ITERATION CONTEXT — This is QA iteration [QA_ITERATION]. The paper has been revised [QA_ITERATION-1] times in this QA stage.
[paste QA_CONTEXT here]

Rules:
1. Do NOT re-flag issues listed in "Deliberate Decisions" unless you have NEW reasoning
2. Focus on "Sections Modified" for regressions — did the last revision's fixes hold up?
3. Quick-scan "Sections Unchanged" — focus your attention on modified sections and deferred issues
4. Escalate any issues from "Deferred Issues" that are still present
```

**Before spawning review agents**, run knowledge graph analysis if `research/knowledge/` exists:
```bash
python scripts/knowledge.py contradictions
python scripts/knowledge.py entities
python scripts/knowledge.py coverage main.tex
```
Read `research/knowledge_contradictions.md` and pass its content to the review agents as additional context. Contradictions should be addressed in the Discussion section or flagged for the author. The entity coverage report identifies key graph entities missing from the manuscript.

**If the knowledge graph is NOT available**: Log `"⚠ Knowledge graph not available for QA — review agents will perform manual contradiction and entity coverage checks per Knowledge Graph Availability Protocol."` Add the following compensating instructions to the Technical Reviewer prompt (in addition to its existing instructions):
```
## Mandatory Compensation: Knowledge Graph Unavailable

The knowledge graph was not available for this paper. You MUST perform these checks manually:

### Manual Contradiction Check
Read the top 10 most-cited source extracts in research/sources/. For each major claim in the manuscript:
1. Does any source report a finding that conflicts with or contradicts this claim?
2. Are there methodological differences between sources that could explain differing results?
3. Does the Discussion section acknowledge known disagreements in the field?
List every contradiction found. Classify as CRITICAL if the manuscript states as fact something that sources disagree on.

### Manual Entity Coverage Check
Compile a list of all methods, theories, datasets, and key concepts mentioned in 3+ source extracts. For each:
1. Is it discussed in the manuscript where appropriate?
2. If a frequently-mentioned concept is absent, is the omission justified or an oversight?
List coverage gaps. Classify as MAJOR if a core concept from the literature is missing.

### Evidence Cross-Reference
For every WEAK or MODERATE claim in research/claims_matrix.md (especially those flagged "KG-unverified"):
1. Re-read the cited source extract
2. Verify the source actually supports the claim as written
3. Flag any overclaims — places where the manuscript goes beyond what the source evidence shows

Append to your review: "Note: Knowledge graph was not available. Contradiction detection and entity
coverage checks were performed manually from source extracts. Some cross-source conflicts may have
been missed."
```

Also add to the Technical Reviewer's existing entity coverage and contradiction placeholders:
- Replace `[paste content of research/knowledge_contradictions.md]` with `"Knowledge graph contradictions not available — see Manual Contradiction Check section above for compensating analysis."`
- Replace `[paste entity coverage report]` with `"Entity coverage report not available — see Manual Entity Coverage Check section above."`

Spawn **3 review agents in parallel** (model: claude-sonnet-4-6[1m]), plus a 4th regression detection agent for iterations 2+ (see below):

**Technical Reviewer:**
```
You are a rigorous peer reviewer. Invoke the `peer-review` skill for structured evaluation.
Also invoke `scientific-critical-thinking` for evidence assessment.
Read main.tex, references.bib, and research/claims_matrix.md completely.

Evaluate:
- Claims supported by evidence or citations?
- Methodology sound and reproducible?
- Results properly analyzed with appropriate statistics?
- Limitations honestly discussed?
- Argument logically coherent Introduction → Conclusion?
- Mathematical notation defined and consistent?
- Appropriate use of domain-specific terminology?
- **Evidence density**: Check the scored claims-evidence matrix. Any WEAK (score 1-2.9) or CRITICAL (score < 1) claims that appear in the manuscript MUST use appropriately hedged language. Flag any WEAK/CRITICAL claims written with unjustified confidence as CRITICAL issues. Flag any CRITICAL claims that survived to Stage 5 without being addressed as mandatory fix items.
- **Assumptions coverage** — Read `research/assumptions.md` (if it exists). Verify:
  1. Every RISKY and CRITICAL assumption is explicitly stated in Methods
  2. Every CRITICAL assumption is discussed in the Limitations subsection of Discussion
  3. No new assumptions were introduced during writing that aren't in the analysis
  4. The paper doesn't inadvertently claim broader validity than the assumptions allow
  Flag missing CRITICAL assumptions as CRITICAL issues. Flag missing RISKY assumptions as MAJOR issues.
- **Argument structure** — for each major claim, verify:
  1. Is there an explicit **WARRANT** (reasoning connecting evidence to claim)? A claim with citations but no warrant is a "citation dump" — the reader is left to figure out the connection. Flag as CRITICAL if missing.
  2. Is the warrant **VALID**? Does the evidence actually support the claim through the stated reasoning? Flag invalid warrants (logical fallacies, factual errors) as CRITICAL.
  3. Are **QUALIFIERS** appropriate? Is the claim scoped to what the evidence can actually show? Flag overclaims (qualifier too weak) as MAJOR and underclaims (qualifier too strong) as MINOR.
  4. Are known **REBUTTALS** addressed somewhere in the paper? Check the Rebuttal column in claims_matrix.md and verify each one is handled.
  No claim may pass QA with a Missing warrant.

The knowledge graph identified these contradictions across sources:
[paste content of research/knowledge_contradictions.md]
Check whether the paper addresses these contradictions in the Discussion.

Also verify that these key entities from the graph are discussed where appropriate:
[paste entity coverage report — focus on missing entities with high connection counts]

Write a detailed review to reviews/technical.md:
- CRITICAL issues (list with line references and specific fixes)
- MAJOR issues (list with line references and specific fixes)
- MINOR issues (list)
- Evidence density heatmap: list all claims by strength (STRONG/MODERATE/WEAK/CRITICAL) with their scores
- Warrant quality assessment: list each claim's warrant quality (Sound/Reasonable/Weak/Missing/Invalid) with issues
- Entity coverage gaps: list important graph entities not discussed in the manuscript
```

**Writing Quality Reviewer:**
```
You are a scientific writing editor. Invoke the `scientific-writing` skill.
Read main.tex completely.

Check:
- Any bullet points in body text? (MUST be full paragraphs)
- Every paragraph has topic sentence, development, conclusion?
- Transitions between sections smooth and logical?
- Terminology consistent throughout (same term for same concept)?
- Tense correct (past for methods/results, present for established facts)?
- Vague words ("various", "some", "interesting", "several")?
- Passive voice overused?
- Each section meets its minimum word count?

Compute word counts per section and report them.
Write review to reviews/writing.md with specific issues and suggested rewrites.
```

**Citation & Completeness Reviewer:**
```
You are a publication readiness auditor. Invoke the `citation-management` skill.
Read main.tex and references.bib.

Verify:
- All \citep{} and \citet{} keys exist in references.bib
- Claims that need citations but lack them (flag with suggested refs)
- All references.bib entries actually cited in text (flag uncited)
- No duplicate BibTeX entries
- No TODO, TBD, FIXME, \lipsum, placeholder text
- All \ref{} cross-references resolve
- Compile: latexmk -pdf -interaction=nonstopmode main.tex — report errors/warnings

Write review to reviews/completeness.md with every issue found.
```

**QA Regression Detector (iterations 2+ only, parallel with review agents above)**

Only spawn this agent if `QA_ITERATION > 1`. Model: claude-sonnet-4-6[1m].

```
You are a regression detector for QA iteration [QA_ITERATION].
Read reviews/qa_iter[QA_ITERATION-1]_context.md (or reviews/qa_cumulative_context.md for iterations 4+) for what changed in the last QA iteration.
Read main.tex completely.

For each change listed in "Changes Made":
1. Find the modified section/paragraph in main.tex
2. Check: does the change still make sense in context? Did it break transitions with surrounding text?
3. Check: did the change introduce any new issues (AI patterns, citation errors, logical gaps)?
4. Check: is the change consistent with changes made elsewhere in the same iteration?

Report ONLY regressions — things that got worse because of the last iteration's changes.
If no regressions found, write an empty report (just "No regressions detected.").
Write to reviews/qa_iter[QA_ITERATION]_regressions.md.
```

**LaTeX Quality Checks** (every QA iteration):

After the review agents complete, check for these LaTeX anti-patterns in `main.tex`. This can run in parallel with the Codex adversarial review (Step 5a-ii).

1. **Float placement**: Any `[H]` specifiers? Any `[h]` without `tbp`? Floats referenced after their appearance?
2. **Caption order**: Captions below tables or above figures? (Both are wrong.)
3. **Cross-reference issues**: `\label` before `\caption`? Manual "Figure 1" instead of `\ref`/`\cref`?
4. **Non-breaking spaces**: Missing `~` before `\cite`/`\ref`/`\cref`? After `e.g.`/`i.e.`/`Fig.`/`Eq.`?
5. **Table formatting**: Any `|` column separators or `\hline`? Should use booktabs.
6. **Math issues**: `$$...$$` instead of `\[...\]`? `eqnarray` instead of `align`? Unpunctuated display math? Italic multi-letter names (`$loss$`)?
7. **Typography**: `\vspace`/`\hspace` layout hacks? `{\bf ...}` or `{\it ...}` instead of `\textbf`/`\emph`? `\sloppy`?
8. **Forbidden packages**: Any `\usepackage` in the document that's in `.venue.json` `forbidden_packages`?
9. **Overfull boxes**: After compilation, check log for overfull hbox warnings > 1pt.

Write findings to `reviews/latex_quality.md`. Grade the manuscript:
- **CLEAN**: 0 issues found
- **MINOR**: 1-3 cosmetic issues (e.g., missing `~` before `\cite`)
- **MAJOR**: 4+ issues, or any structural issue like `[H]` abuse, `$$...$$`, or forbidden packages

The revision agent (Step 5c) must fix all MAJOR LaTeX issues. MINOR issues should be fixed if iteration budget allows. Include the grade in the review synthesis (Step 5b).

#### Step 5a-ii: Codex Adversarial Review

**This is a separate step. Do NOT skip it. Do NOT merge it with the agent reviews above.**

After spawning the 3 review agents, IMMEDIATELY call Codex directly in your main session (this runs in parallel while agents work):

1. Read `main.tex` completely
2. Call the Codex MCP tool:

```
mcp__codex-bridge__codex_review({
  prompt: "You are an adversarial peer reviewer. Find the weakest points in this manuscript: (1) Claims that exceed the evidence (2) Logical gaps in the argument chain (3) Methodological shortcuts (4) Missing baselines or unfair comparisons (5) Conclusions that don't follow from results. Be specific — cite sections and sentences.",
  context: "[paste the full content of main.tex]",
  evidence_mode: true
})
```

3. Write the Codex response to `reviews/codex_adversarial.md`

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"5","tool":"codex_review","purpose":"adversarial peer review","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"reviews/codex_adversarial.md","resolution_summary":"[one-line]"}
```

**Checkpoint**: Before proceeding to Step 5a-iii, verify ALL 4 review files exist:
- `reviews/technical.md` (from agent)
- `reviews/writing.md` (from agent)
- `reviews/completeness.md` (from agent)
- `reviews/codex_adversarial.md` (from Codex call above)

If `reviews/codex_adversarial.md` is missing, you skipped the Codex review — go back and do it.

#### Step 5a-iii: Reference Spot-Check

**Fabricated references are the #1 risk in AI-assisted writing.** Catch them inside the QA loop, not after.

Spawn a **reference spot-check agent** (model: claude-sonnet-4-6[1m]):
```
You are a reference verification specialist running a targeted spot-check.
Read references.bib.

Select 10-15 references to verify, prioritizing:
1. References added or modified since the last QA iteration (check provenance.jsonl for recent "add" actions with citations)
2. References cited in sections that were revised in the last QA iteration
3. If QA_ITERATION == 1, select a random sample weighted toward references supporting WEAK or MODERATE claims (from research/claims_matrix.md)

For each selected reference:
1. If DOI present: verify via CrossRef API (curl -s "https://api.crossref.org/works/DOI")
2. If no DOI: search for exact title using Perplexity or web search
3. Classify: VERIFIED, METADATA_MISMATCH, SUSPICIOUS, or FABRICATED

For FABRICATED references:
- REMOVE from references.bib immediately
- REMOVE all \citep{} and \citet{} references to it from main.tex
- Flag the claim that relied on it — it now has NO evidence support

For METADATA_MISMATCH:
- Fix metadata directly in references.bib

Write results to reviews/ref_spotcheck_iter[QA_ITERATION].md.
Track which references were checked so post-QA validation can skip them.
Append checked keys to research/verified_refs.jsonl (one JSON object per ref: {"key": "smith2024", "status": "VERIFIED", "qa_iteration": N, "method": "crossref_doi"}).
```

**Action on results:**
- If ANY fabricated references found: the revision agent (Step 5c) must address the claims that lost their citations — either find replacement evidence, hedge the claims, or remove them.
- Pass the spot-check results to the review synthesis (Step 5b) so the revision agent knows which claims need attention.

#### Step 5b: Synthesize Reviews

Read ALL files in `reviews/` including `codex_adversarial.md` and `qa_iter[QA_ITERATION]_regressions.md` (if it exists). Also read `research/claims_matrix.md` for the evidence density heatmap. **Regressions get automatic HIGH priority** — fixes that undo damage from the last iteration come before new improvements. Build a prioritized fix list:
1. All CRITICAL issues (must fix) — including any CRITICAL-strength claims that must be removed, supported, or heavily hedged
2. All MAJOR issues (should fix) — including WEAK claims written with unjustified confidence
3. Word count shortfalls
4. Missing citations
5. Evidence density upgrades — actions that would move WEAK claims toward MODERATE (e.g., finding additional sources, strengthening evidence descriptions)

#### Step 5b-ii: Issue Severity Tracking

After synthesizing reviews, count and classify all issues from the consolidated fix list:

```
QA_METRICS for iteration [QA_ITERATION]:
- CRITICAL issues: [count]
- MAJOR issues: [count]
- MINOR issues: [count]
- Total severity score: (CRITICAL × 10) + (MAJOR × 3) + (MINOR × 1)
```

Compare against previous iterations to identify recurring vs new issues:
- **Recurring**: An issue that matches (same section + same category) an issue from a prior iteration
- **New**: An issue not present in any prior iteration

Record metrics in `.paper-state.json` under `stages.qa.iterations`:
```json
{
  "iteration": QA_ITERATION,
  "critical": 0,
  "major": 2,
  "minor": 5,
  "severity_score": 11,
  "new_issues": 1,
  "recurring_issues": 4,
  "sections_modified": ["methods", "discussion"]
}
```

**Adaptive Max Iterations (iteration 1 only):** After recording iteration 1 metrics, adjust `max_iterations`:
- If `severity_score < 10` (paper is already in good shape): reduce `max_iterations` to 3 (standard) or 5 (deep)
- If `severity_score > 50` (many issues): increase `max_iterations` by 2 (e.g., 7 for standard, 10 for deep)
- Otherwise: keep the original max

Update `stages.qa.max_iterations` in `.paper-state.json` and log: `"Adaptive QA: iteration 1 severity [X] → max iterations adjusted to [Y]"`

**Pre-QA scoring baseline:** On the first QA iteration, run the quality scorer and heatmap to establish a baseline:
```bash
python scripts/quality.py score --format json --project . > .paper-quality-pre-qa.json
python scripts/quality.py save --project . --checkpoint pre_qa
python scripts/quality.py heatmap --project .
```
Store the JSON output in `.paper-state.json` under `stages.quality_scores.pre_qa`. The heatmap (`research/evidence_heatmap.md`) gives QA reviewers the current evidence state. After QA fixes, re-run to measure improvement.

#### Step 5c: Revision Agent

Spawn a revision agent (model: claude-opus-4-6[1m]):
```
You are revising a research paper based on peer review feedback.
Invoke the `scientific-writing` skill.

Read the following review feedback and fix EVERY critical and major issue in main.tex:
[PASTE CONSOLIDATED REVIEW FINDINGS]

For each issue:
1. Locate the problem in main.tex
2. Fix it with careful edits that maintain consistency with the rest of the paper
3. If a section needs more words, add substantive content (not filler)
4. If citations are needed, find appropriate ones from references.bib
5. If new citations are needed, add verified entries to references.bib
6. If content should be REMOVED (redundant, weak, or diluting stronger arguments), cut it

After all fixes, compile: latexmk -pdf -interaction=nonstopmode main.tex
Fix any LaTeX errors.
Edit main.tex and references.bib directly.

PROVENANCE — After EACH revision, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"5","agent":"qa-revision","action":"revise|cut|add","target":"[section/pN]","reasoning":"[why — reference the specific review issue]","feedback_ref":"[reviews/file.md#issue-number]","diff_summary":"[what changed]","sources":["keys"],"qa_iteration":[QA_ITERATION]}
For cuts: save removed text to provenance/cuts/[section]-[pN]-qa[QA_ITERATION].tex and set archived_to.
```

**Score regression check**: After applying QA fixes, re-run:

```bash
python scripts/quality.py score --format json --project .
python scripts/quality.py heatmap --project .
```

Compare with the baseline (`.paper-quality-pre-qa.json`). If the overall evidence score DECREASED:
- A QA fix may have removed well-supported content or weakened language below evidence level
- Flag as a regression and investigate before declaring convergence

#### Step 5c-ii: Generate QA Iteration Context

After the revision agent completes, generate `reviews/qa_iter[QA_ITERATION]_context.md` for use by the next QA iteration's review agents (if the loop repeats). Build from the review files and provenance entries for this QA iteration:

```markdown
# QA Iteration [QA_ITERATION] Context

## Changes Made
1. [section/paragraph] — [action] — [one-line summary]

## Deliberate Decisions (kept as-is)
1. [section/paragraph] — [what was flagged] — [why it was kept or deferred]

## Sections Modified
- [Section]: [which paragraphs changed]

## Sections Unchanged
- [Section] (unchanged since QA iteration [M] or initial pipeline)

## Quality Trend
| Iteration | Critical | Major | Minor | Score | Δ |
|-|-|-|-|-|-|
[For each completed iteration, add a row from stages.qa.iterations in .paper-state.json]
Example:
| 1 | 2 | 5 | 8 | 43 | — |
| 2 | 0 | 3 | 6 | 15 | -28 |

## Deferred Issues
[MEDIUM/MINOR issues not addressed in this iteration]
```

Keep under 600 words (increased from 500 to accommodate the quality trend table).

**Generate cumulative QA context (iterations 3+ only):** If `QA_ITERATION >= 3`, generate `reviews/qa_cumulative_context.md` by merging all individual QA context files. For iterations 4+, this file replaces individual context files in review agent and regression detector prompts (to keep prompt size manageable):

```markdown
# Cumulative QA Iteration History

## All Deliberate Decisions (across all QA iterations)
[Merged from all previous QA context files. Only keep decisions from the last 2 iterations — older decisions that weren't re-flagged are considered resolved.]

## Section Stability
| Section | Last Modified | Iterations Since Change |
|-|-|-|
| Introduction | QA iteration 2 | 1 |
| Related Work | Initial pipeline | 3 (stable) |
| ... | ... | ... |

## Quality Trend
| Iteration | Critical | Major | Minor | Score | Δ |
|-|-|-|-|-|-|
[Copy from the latest individual context file]

## Current Deferred Issues
[Only from the most recent QA iteration — older deferred issues not re-flagged are considered resolved]
```

Keep the cumulative file under 800 words.

#### Step 5d: Quality Gate Check

After revision, check ALL criteria from the table below. If all pass, proceed to Stage 6.

**If any criteria fail, evaluate convergence BEFORE deciding whether to loop:**

Read `stages.qa.iterations` from `.paper-state.json` and apply these checks in order:

1. **Divergence Detection**: If `QA_ITERATION >= 2` and the severity_score INCREASED from iteration N-1 to N:
   - Log: `"⚠ QA iteration [N] introduced more issues than it fixed (score: [prev] → [curr])"`
   - If this happened in BOTH of the last two consecutive iterations (sustained divergence), STOP and ask the user:
     ```
     ⚠ QA is diverging — the last 2 iterations introduced more issues than they fixed.
     Severity trend: [list scores]. Remaining issues: [summary].
     Options: (1) Continue iterating anyway, (2) Proceed to finalization with current state.
     ```
   - Update `.paper-state.json`: `stages.qa.convergence_reason = "diverging_stopped"`

2. **Plateau Detection**: If `QA_ITERATION >= 3` and the severity_score has not decreased for 3 consecutive iterations (each score within ±1 of the previous):
   - Ask the user:
     ```
     QA appears to have plateaued at severity [X] after [N] iterations.
     Remaining issues: [list]. Continue iterating (may not improve) or proceed to finalization?
     ```
   - If user chooses to proceed, update `.paper-state.json`: `stages.qa.convergence_reason = "plateau_accepted"`

3. **Convergence (Early Exit)**: If `QA_ITERATION >= 2` and the last 2 iterations BOTH have `severity_score` at or below the threshold AND the score did not increase between them:
   - Threshold: 5 (standard mode), 3 (deep mode)
   - Early exit with message: `"QA converged after [N] iterations (severity score: [X] → [Y]). Proceeding to post-QA."`
   - Update `.paper-state.json`: `stages.qa.converged_at = QA_ITERATION`, `stages.qa.convergence_reason = "converged"`, `stages.qa.done = true`
   - **Skip** to Stage 6 (post-QA audits). Do NOT run the exhaustion handler.

4. **No New Issues (context-aware)**: If `QA_ITERATION >= 2` and QA_CONTEXT was loaded: check whether all review agents reported no issues beyond those already listed in "Deliberate Decisions" from the previous context file. If nothing genuinely new was found:
   - Early exit with message: `"QA converged after [N] iterations — no new issues beyond previous deliberate decisions. Proceeding to post-QA."`
   - Update `.paper-state.json`: `stages.qa.converged_at = QA_ITERATION`, `stages.qa.convergence_reason = "no_new_issues"`, `stages.qa.done = true`
   - **Skip** to Stage 6 (post-QA audits). Do NOT run the exhaustion handler.

5. **Persistent Low-Priority Only (context-aware)**: If `QA_ITERATION >= 3` and QA_CONTEXT was loaded: check whether the only issues found appear in "Deferred Issues" from 2+ consecutive QA iterations and were deprioritized each time. If so:
   - Early exit with message: `"QA converged after [N] iterations — only persistent low-priority issues remain. Proceeding to post-QA."`
   - Log: `"Persistent low-priority issues that were never addressed: [list]. These are unlikely to be worth further iteration."`
   - Update `.paper-state.json`: `stages.qa.converged_at = QA_ITERATION`, `stages.qa.convergence_reason = "persistent_low_priority_only"`, `stages.qa.done = true`
   - **Skip** to Stage 6 (post-QA audits). Do NOT run the exhaustion handler.

6. **Continue or Exhaust**: If none of the above triggered and `QA_ITERATION < MAX_ITERATIONS`, loop back to Step 5a with fresh reviewers. If `QA_ITERATION == MAX_ITERATIONS`, fall through to the exhaustion handler below.

**If any fail and `QA_ITERATION == MAX_ITERATIONS` (iterations exhausted):**

The pipeline does NOT silently proceed. Run the following triage:

1. **Read `research/claims_matrix.md`** and identify all claims with evidence density score < 1 (CRITICAL) or 1-2.9 (WEAK).

2. **CRITICAL claims (score < 1) → HARD STOP.** These represent claims with essentially no supporting evidence. The pipeline MUST NOT finalize with CRITICAL claims in the manuscript. Use `AskUserQuestion` to escalate:

   ```
   ⚠ QA loop exhausted ([MAX_ITERATIONS] iterations) with unresolved CRITICAL issues:

   CRITICAL claims (score < 1, no adequate evidence):
   - [Claim text] — score [X], section [Y], current evidence: [summary]
   - ...

   [Any other unresolved CRITICAL quality failures, e.g. fabricated refs still present]

   Options:
   1. Remove these claims from the manuscript (I'll excise them and adjust surrounding text)
   2. Provide additional evidence or sources for me to incorporate
   3. Downgrade to clearly hedged speculation (e.g., "It is conceivable that..." / "One possibility is...")
   4. Abort finalization — I'll save current state for manual revision

   Which option for each claim? (You can mix, e.g., "1 for claim A, 3 for claim B")
   ```

   Wait for user response and execute their choice before proceeding. Log each action to `research/provenance.jsonl` with `"reasoning": "QA exhaustion triage — user directed"`.

3. **WEAK claims (score 1-2.9) → AUTO-HEDGE.** Spawn a revision agent (`claude-opus-4-6[1m]`) to:
   - Find every paragraph containing a WEAK claim (cross-reference `research/claims_matrix.md` with `main.tex`)
   - Replace confident language with appropriately hedged alternatives: "suggests" instead of "demonstrates", "may" instead of "will", "preliminary evidence indicates" instead of "evidence shows", add qualifiers like "under certain conditions" or "in the studies reviewed"
   - Ensure each hedged claim retains its citation — hedging does not mean removing evidence
   - Log each change to `research/provenance.jsonl` with `"action": "hedge"` and `"reasoning": "QA exhaustion — auto-downgrade WEAK claim"`

4. **Other unresolved issues → USER SUMMARY.** After handling CRITICAL and WEAK claims, if other quality criteria still fail (e.g., missing cross-references, compilation warnings, thin sections), present a concise summary:

   ```
   ℹ QA loop completed with [N] non-critical issues remaining after [MAX_ITERATIONS] iterations:

   - [Issue category]: [specific details]
   - ...

   These are flagged in reviews/qa_iter[MAX]_context.md. Proceeding to post-QA audits.
   ```

   These non-critical issues do NOT block finalization but are logged clearly.

5. **Re-compile** after any triage changes: `latexmk -pdf -interaction=nonstopmode main.tex`. Verify no new errors.

**[DEEP]** If depth is `"deep"` and this is the FINAL QA iteration (all criteria pass), run one additional Codex review before exiting:

```
mcp__codex-bridge__codex_review({
  prompt: "Final deep review of this manuscript. This paper has already passed multiple rounds of QA. Look for subtle issues that earlier reviews missed: (1) Implicit assumptions never made explicit (2) Logical leaps that seem fine on first read but don't hold up (3) Claims that are technically true but misleading (4) Missing qualifications or edge cases (5) Opportunities to strengthen the argument that were overlooked.",
  context: "[paste the full content of main.tex]",
  evidence_mode: true
})
```

Write to `reviews/codex_final_deep.md`. If this surfaces CRITICAL issues, do one more fix-and-review cycle. Otherwise, proceed.

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"5","tool":"codex_review","purpose":"final deep review","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"reviews/codex_final_deep.md","resolution_summary":"[one-line]"}
```

---
