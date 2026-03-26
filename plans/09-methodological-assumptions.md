# Plan 09: Structured Methodological Assumptions Handling

## Problem

The pipeline writes a Methods section and reviews it for completeness, but never explicitly enumerates the assumptions underlying the chosen methodology. Reviewers systematically attack unstated assumptions — "This approach assumes X, but what if X doesn't hold?" If the paper never acknowledges the assumption, the reviewer perceives it as an oversight. If the paper states the assumption explicitly and discusses its validity, the reviewer sees rigor.

Currently, assumptions surface only if a QA reviewer happens to notice them. There's no systematic step to identify, categorize, and address them.

## Goal

Add an assumptions enumeration step between planning (Stage 2) and writing (Stage 3), producing `research/assumptions.md` that feeds into Methods writing and Discussion limitations.

## Design

### New Step: Stage 2e — Assumptions Analysis

Runs after novelty verification (Stage 2d), before writing begins.

#### Assumptions Agent (model: claude-opus-4-6[1m])

```
You are a methodological critic analyzing the assumptions behind a proposed research approach.
Read research/thesis.md for the contribution statement.
Read main.tex for the outline, especially the Methods section plan.
Read research/methods.md for the methodological landscape.
Read research/claims_matrix.md for the claims and their evidence.

Systematically enumerate EVERY assumption the proposed methodology relies on. For each assumption:

1. STATE the assumption clearly and precisely
2. CATEGORIZE it:
   - STANDARD: Widely accepted in the field. Cite 2-3 papers that use this assumption. → Mention briefly in Methods.
   - REASONABLE: Defensible but should be stated explicitly. Cite precedent if available. → State in Methods, discuss validity.
   - RISKY: Could be challenged by reviewers. Evidence for/against is mixed. → State in Methods, discuss extensively in Discussion/Limitations. Consider sensitivity analysis.
   - CRITICAL: If this assumption is wrong, the entire contribution may be invalid. → Must be thoroughly justified in Methods and tested/bounded if possible.
3. JUSTIFY: Why is this assumption appropriate for this specific context?
4. CONSEQUENCE: What happens if this assumption is violated? How would results change?
5. MITIGATION: How does the paper address or bound the impact of this assumption?
6. PRIOR ART: Do other papers in this field make the same assumption? What alternatives exist?

Also identify IMPLICIT assumptions — things the methodology takes for granted without stating them. These are the most dangerous because reviewers will flag them as oversights.

Categories of assumptions to check:
- Data assumptions (distribution, sampling, independence, missing data mechanism)
- Model assumptions (functional form, parameter space, convergence)
- Evaluation assumptions (benchmark representativeness, metric validity, baseline fairness)
- Scope assumptions (generalizability, domain transfer, temporal stability)
- Resource assumptions (compute, data availability, reproducibility)

Write to research/assumptions.md in this format:

# Methodological Assumptions Analysis

## Summary
- Total assumptions identified: N
- Standard: N | Reasonable: N | Risky: N | Critical: N

## Critical Assumptions
### A1: [assumption statement]
- **Category**: CRITICAL
- **Justification**: [why it's appropriate here]
- **If violated**: [consequences]
- **Mitigation**: [how the paper addresses this]
- **Prior art**: [papers making same assumption]
- **Where to address**: Methods (Sec 3.1) + Discussion (Sec 6.2)

## Risky Assumptions
### A2: [assumption statement]
...

## Reasonable Assumptions
...

## Standard Assumptions
...

## Implicit Assumptions Found
[assumptions that were not in the outline but are inherent in the methodology]
```

### Knowledge Graph Integration

If available, query the knowledge graph to find evidence for/against each risky assumption:

```bash
python scripts/knowledge.py evidence-for "[assumption] is valid"
python scripts/knowledge.py evidence-against "[assumption] is valid"
```

### Integration into Writing

#### Methods Section (Stage 3, Order 3)

Add to the Methods writing agent prompt:

```
ASSUMPTIONS — Read research/assumptions.md. For each assumption categorized as REASONABLE, RISKY, or CRITICAL:
1. State it explicitly in the Methods section at the point where it's introduced
2. For RISKY and CRITICAL: briefly justify why it's appropriate (cite prior art if available)
3. Forward-reference the Discussion/Limitations section for detailed analysis of RISKY and CRITICAL assumptions

Do NOT bury assumptions — state them near the methodological choice they relate to. A reviewer should be able to find every assumption by reading Methods.
```

#### Discussion Section (Stage 3, Order 5)

Add to the Discussion writing agent prompt:

```
ASSUMPTIONS — Read research/assumptions.md. The Limitations subsection MUST address:
1. Every CRITICAL assumption: what happens if it doesn't hold, how bounded is the impact
2. Every RISKY assumption: evidence for and against, alternative approaches if assumption fails
3. Group assumptions by theme (data, model, evaluation) for readability

Frame limitations honestly but constructively — "We acknowledge X; however, prior work [cite] demonstrates Y, suggesting this assumption is reasonable in the context of Z."
```

### Integration into QA

Add to the Technical Reviewer prompt (Stage 5):

```
ASSUMPTIONS — Read research/assumptions.md. Verify:
1. Every RISKY and CRITICAL assumption is explicitly stated in Methods
2. Every CRITICAL assumption is discussed in Limitations
3. No new assumptions were introduced during writing that aren't in the analysis
4. The paper doesn't inadvertently claim broader validity than the assumptions allow
```

### Integration into Codex

The Codex thesis stress-test (Stage 2b) should also receive the assumptions analysis:

```
mcp__codex-bridge__codex_ask({
  prompt: "Review these methodological assumptions. Are any miscategorized (e.g., marked STANDARD but actually RISKY)? Are any assumptions MISSING that a reviewer would flag? Are the proposed mitigations adequate?",
  context: "[paste research/assumptions.md]"
})
```

## Files to Modify

1. Pipeline stage files:
   - `template/claude/pipeline/stage-2-planning.md` — Add Stage 2e hook after novelty verification
   - `template/claude/pipeline/stage-3-writing.md` — Methods writing: add assumptions instructions; Discussion writing: add assumptions to limitations
   - `template/claude/pipeline/stage-5-qa.md` — Technical Reviewer: add assumptions verification
   - `template/claude/pipeline/stage-2b-codex-thesis.md` — Codex thesis stress-test: add assumptions context
   - `template/claude/commands/write-paper.md` — Update orchestrator stage table to include Stage 2e
2. `template/claude/CLAUDE.md`:
   - Document assumptions analysis in pipeline overview
   - Reference research/assumptions.md in file conventions

## Files to Create

1. `template/claude/pipeline/stage-2e-assumptions.md` — New pipeline stage file for assumptions analysis

Note: `research/assumptions.md` is generated at runtime.

## Risks

- The assumptions agent may be overly cautious, listing too many trivial assumptions. Mitigation: the STANDARD category absorbs well-known assumptions with minimal overhead.
- Writing agents may produce defensive, over-hedged text. Mitigation: the prompt explicitly says "honestly but constructively" — acknowledge, don't apologize.
- Some assumptions may be domain-specific and hard for a general model to identify. Mitigation: domain skills provide expertise, and the knowledge graph surfaces contradictory evidence.

## Acceptance Criteria

- [ ] Stage 2e produces research/assumptions.md with categorized assumptions
- [ ] Every assumption has justification, consequence, mitigation, and prior art
- [ ] Implicit assumptions are identified separately
- [ ] Methods writing agent states REASONABLE/RISKY/CRITICAL assumptions explicitly
- [ ] Discussion writing agent addresses all RISKY and CRITICAL assumptions in Limitations
- [ ] Technical Reviewer verifies assumption coverage
- [ ] Codex reviews assumption categorization
- [ ] Knowledge graph queries inform evidence for/against risky assumptions
