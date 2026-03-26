# Plan 05: Argumentation Framework for Writing Agents

## Problem

Writing agents get detailed instructions about what content to produce but no explicit guidance on how to structure arguments. Academic papers succeed or fail on argument quality — not just whether claims have citations, but whether the reasoning chain from evidence to claim is logically sound. The current pipeline checks for evidence *existence* (claims-evidence matrix) but not evidence *sufficiency* (does the evidence actually warrant the claim?).

## Goal

Integrate a lightweight Toulmin argumentation model into the planning and writing stages, so every major claim has explicit warrant and rebuttal reasoning, and writing agents produce structurally sound arguments rather than just well-cited prose.

## Design

### The Toulmin Model (adapted for academic papers)

For each major claim in the paper:

| Component | What it is | Example |
|-|-|-|
| **Claim** | The assertion being made | "Our method improves accuracy by 15% on benchmark X" |
| **Evidence** | Data, citations, experiments supporting the claim | "Table 2 shows 87.3% vs baseline 75.8%; smith2024 reports similar improvements" |
| **Warrant** | WHY the evidence supports the claim — the logical bridge | "Benchmark X is the standard evaluation for this task, and 15% improvement exceeds the typical 3-5% incremental gains in recent work" |
| **Qualifier** | Scope limitations, conditions under which the claim holds | "On English-language data with the default hyperparameters" |
| **Rebuttal** | Anticipated counterarguments and how they're addressed | "This improvement may not generalize to low-resource languages (addressed in Section 6.2)" |

### Changes to Claims-Evidence Matrix

Expand from the current format to include Warrant and Rebuttal columns. New format:

```markdown
| # | Claim | Evidence | Warrant | Qualifier | Rebuttal | Score | Section | Status |
|-|-|-|-|-|-|-|-|-|
| C1 | Method improves X by 15% | Table 2, smith2024 (FULL) | Standard benchmark, exceeds typical gains | English data, default params | May not generalize to low-resource (Sec 6.2) | 8.0 | Results | Supported |
| C2 | Prior approaches fail on Y | davis2022 (ABS), lee2021 (META) | [MISSING — needs explicit reasoning] | | | 2.0 | Related Work | ⚠ Weak |
```

A claim with empty Warrant is a structural red flag — it means the pipeline knows WHAT evidence exists but hasn't articulated WHY it's sufficient.

### Integration into Pipeline Stages

#### Stage 2 — Planning

After building the initial claims-evidence matrix, add a **Warrant Development** step. For each claim:

1. If the warrant is obvious (direct experimental result supporting an empirical claim), state it briefly
2. If the warrant requires reasoning (e.g., "this theoretical framework applies because..."), develop it fully
3. If no clear warrant exists, the claim is unsupported even with citations — flag it

Also develop rebuttals:
1. For each claim, identify the most likely reviewer objection
2. Determine whether the rebuttal is addressed in the paper (and where) or needs to be added

Use the knowledge graph (if available) to find rebuttals:
```bash
python scripts/knowledge.py evidence-against "[claim]"
```

#### Stage 3 — Writing

Add to every writing agent prompt:

```
ARGUMENTATION — For each major claim in your section, ensure the paragraph contains:
1. The CLAIM stated clearly
2. EVIDENCE supporting it (with citations)
3. A WARRANT explaining why the evidence is sufficient (the logical bridge)
4. A QUALIFIER if the claim has scope limitations
5. Reference to where REBUTTALS are addressed (if not in this section)

Do NOT just cite papers and state conclusions. Explain WHY the cited evidence supports YOUR specific claim. This is the difference between a literature dump and an argument.

The claims for your section (from research/claims_matrix.md):
[paste relevant claims with their warrant/rebuttal columns]
```

#### Stage 5 — QA Review

Add to the Technical Reviewer prompt:

```
ARGUMENT STRUCTURE — For each major claim, verify:
1. Is there explicit WARRANT (reasoning connecting evidence to claim)?
   A claim with citations but no warrant is a "citation dump" — the reader is left to figure out the connection.
2. Is the warrant VALID? Does the evidence actually support the claim through the stated reasoning?
3. Are QUALIFIERS appropriate? Is the claim scoped to what the evidence can actually show?
4. Are known REBUTTALS addressed somewhere in the paper?

Flag claims where the warrant is missing, invalid, or where qualifiers are too weak (overclaim) or too strong (underclaim).
```

#### `/auto` Iterations — Depth & Evidence Reviewer

Add to the assessment agent prompt:

```
ARGUMENTATION — Check the warrant quality for the paper's 5 strongest claims:
1. Is the logical bridge from evidence to claim explicit and sound?
2. Are there hidden assumptions in the warrant that should be stated?
3. Would a domain expert accept this warrant, or would they say "that doesn't follow"?

Weak warrants are higher priority than missing citations — a well-cited claim with bad reasoning is worse than a lightly-cited claim with sound logic.
```

### Warrant Quality Categories

To make assessment concrete:

| Quality | Description | Action |
|-|-|-|
| **Sound** | Evidence logically necessitates the claim | None needed |
| **Reasonable** | Evidence supports the claim given stated assumptions | State assumptions explicitly |
| **Weak** | Evidence is consistent with the claim but doesn't strongly support it | Hedge the claim or find stronger evidence |
| **Missing** | No warrant articulated — claim and evidence are just juxtaposed | Develop warrant or remove claim |
| **Invalid** | The warrant contains a logical fallacy or factual error | Fix immediately |

## Files to Modify

1. Pipeline stage files:
   - `template/claude/pipeline/stage-2-planning.md` — Add warrant and rebuttal development step after claims matrix
   - `template/claude/pipeline/stage-3-writing.md` — Add argumentation instructions to every writing agent prompt
   - `template/claude/pipeline/stage-5-qa.md` — Add argument structure check to Technical Reviewer prompt
2. `template/claude/commands/auto.md`:
   - Depth & Evidence Reviewer: Add warrant quality assessment
3. `template/claude/CLAUDE.md`:
   - Document expanded claims matrix format with Warrant/Rebuttal columns
   - Add argumentation framework reference

## Files to Create

None.

## Risks

- Adding Warrant/Rebuttal columns makes the claims matrix wider and harder to read. Mitigation: keep Warrant entries brief (one sentence). Full reasoning goes in the Discussion/Methods text.
- Writing agents may produce formulaic warrant language ("This is important because..."). Mitigation: the de-AI polish step catches this.
- Over-qualifying claims can make the paper read as uncertain. Mitigation: Qualifier should reflect the actual evidence scope, not defensive hedging.

## Acceptance Criteria

- [ ] Claims-evidence matrix includes Warrant, Qualifier, and Rebuttal columns
- [ ] Stage 2 includes explicit warrant development step
- [ ] All writing agent prompts include argumentation instructions
- [ ] Technical Reviewer checks warrant validity
- [ ] `/auto` Depth Reviewer assesses warrant quality
- [ ] Knowledge graph `evidence-against` queries feed rebuttal development
- [ ] No claim passes QA with a "Missing" warrant
