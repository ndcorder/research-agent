# Auto Phase 1: Assessment

> **Prerequisites**: Read `pipeline/shared-protocols.md` first. Use its Provenance Logging Protocol, Tool Fallback Chain, and Domain Detection table throughout this phase.

---

## Phase 0: Knowledge Graph Refresh

Before assessment, refresh contradiction analysis if the knowledge graph exists (`research/knowledge/` directory present — skip silently if not):
```bash
python scripts/knowledge.py contradictions
```
Read `research/knowledge_contradictions.md` and pass any new contradictions to the Depth & Evidence Reviewer (Agent A) below.

## Phase 0b: Load Iteration Context (iterations 2+)

If `CURRENT_ITERATION > 1`, read the context file from the previous iteration:
- For iterations 2-3: read `reviews/auto_iter[CURRENT_ITERATION-1]_context.md`
- For iterations 4+: read `reviews/auto_cumulative_context.md` (see Post-Iteration step 5b)

Store the contents as `ITERATION_CONTEXT`. This is passed to all assessment agents below.

If the context file doesn't exist (e.g., first run after this feature was added), skip — agents run without context as before.

## Phase 1: Assessment (parallel agents)

Spawn assessment agents in parallel (model: claude-sonnet-4-6[1m]). Each reads main.tex and writes an assessment to `reviews/auto_iter[N]_[type].md`.

**If CURRENT_ITERATION > 1**, prepend the following block to EVERY assessment agent prompt:

```
ITERATION CONTEXT — This paper has been through [N-1] improvement iterations.
[paste ITERATION_CONTEXT here]

Rules:
1. Do NOT re-flag issues listed in "Deliberate Decisions" unless you have NEW reasoning not already considered
2. DO check "Sections Modified" for regressions — did the changes hold up? Did they break anything?
3. For "Sections Unchanged Since Last Review": quick scan only — focus your attention on modified sections and deferred issues
4. If something from "Deferred Issues" is still present, escalate its priority
```

Spawn **4 assessment agents in parallel** (plus a 5th regression detection agent — see below).

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

8. **ARGUMENTATION** — Check the warrant quality for the paper's 5 strongest claims:
   a. Is the logical bridge from evidence to claim explicit and sound? Or is the claim just juxtaposed with citations?
   b. Are there hidden assumptions in the warrant that should be stated as explicit qualifiers?
   c. Would a domain expert accept this warrant, or would they say "that doesn't follow"?
   d. Are rebuttals from the claims matrix actually addressed in the manuscript text?
   Weak warrants are higher priority than missing citations — a well-cited claim with bad reasoning is worse than a lightly-cited claim with sound logic. For each warrant issue, specify: claim number, current warrant quality (Sound/Reasonable/Weak/Missing/Invalid), and suggested fix.

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

**Agent E — "Regression Detector" (iterations 2+ only, parallel with agents above)**

Only spawn this agent if `CURRENT_ITERATION > 1`. Model: claude-sonnet-4-6[1m].

```
You are a regression detector for iteration [N] of autonomous paper improvement.
Read reviews/auto_iter[N-1]_context.md (or reviews/auto_cumulative_context.md for iterations 4+) for what changed in the last iteration.
Read main.tex completely.

For each change listed in "Changes Made":
1. Find the modified section/paragraph in main.tex
2. Check: does the change still make sense in context? Did it break transitions with surrounding text?
3. Check: did the change introduce any new issues (AI patterns, citation errors, logical gaps)?
4. Check: is the change consistent with changes made elsewhere in the same iteration?

Report ONLY regressions — things that got worse because of the last iteration's changes.
If no regressions found, write an empty report (just "No regressions detected.").
Write to reviews/auto_iter[N]_regressions.md.
```
