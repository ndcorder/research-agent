# Plan 02: Evidence Density Scoring

## Problem

The claims-evidence matrix tracks *which* evidence backs each claim but not *how strong* that support is. A claim backed by three full-text primary sources with quantitative data is fundamentally different from one backed by a single abstract-only mention, yet the current pipeline treats both as "Supported." This means QA reviewers can't efficiently identify the weakest links in the argument, and source acquisition can't prioritize by evidence impact.

## Goal

Add a numerical evidence strength score to every claim in the claims-evidence matrix, creating a vulnerability heatmap that drives source acquisition priority, writing depth, and QA focus.

## Design

### Scoring Model

Each piece of evidence supporting a claim gets a base score based on source access level, then modifiers:

**Base Score (per source)**:
| Access Level | Score | Rationale |
|-|-|-|
| FULL-TEXT, primary data | 3 | You read the actual results |
| FULL-TEXT, secondary/review | 2 | You read the full argument but it's not primary evidence |
| ABSTRACT-ONLY | 1 | You have a summary, not the real content |
| METADATA-ONLY | 0 | You know the paper exists, nothing more |

**Modifiers** (applied per source):
- Paper is highly cited (>100 citations): +0.5
- Paper is from 2024-2026 (recent): +0.5
- Paper's finding directly matches the claim (not tangential): +1
- Paper is from the same domain/methodology: +0.5

**Claim Score** = sum of all supporting source scores

**Thresholds**:
| Score | Label | Meaning |
|-|-|-|
| >= 6 | STRONG | Well-supported, multiple strong sources |
| 3-5.9 | MODERATE | Adequately supported but could be stronger |
| 1-2.9 | WEAK | Under-supported, needs more evidence or hedging |
| 0-0.9 | CRITICAL | Essentially unsupported, must be addressed |

### Changes to Claims-Evidence Matrix

Current format:
```
| # | Claim | Evidence Type | Evidence Source | Source Access | Section | Status |
```

New format:
```
| # | Claim | Evidence Type | Evidence Sources | Score | Strength | Section | Status |
```

Each evidence source entry includes: `key (access_level, relevance: direct/tangential) = N pts`

Example:
```
| 1 | Our method improves X by 15% | Experiment + Citation | Own experiments (N/A, direct) = 3, smith2024 (FULL-TEXT, direct) = 4, jones2023 (ABSTRACT-ONLY, tangential) = 1 | 8.0 | STRONG | Results | Supported |
| 2 | Prior approaches fail on Y | Citation | davis2022 (ABSTRACT-ONLY, direct) = 2, lee2021 (METADATA-ONLY, tangential) = 0 | 2.0 | WEAK | Related Work | ⚠ Needs upgrade |
```

### Integration Points

**Stage 1d (Source Acquisition)**: Currently prioritizes papers by citation frequency in the research files. Change to prioritize by evidence impact: papers that support WEAK or CRITICAL claims get highest acquisition priority, regardless of how often they're cited.

**Stage 2 (Planning)**: After building the claims matrix, compute scores and flag WEAK/CRITICAL claims. These should either:
- Be targeted in Stage 2c (deep mode) for additional evidence
- Have their language hedged ("suggests" vs "demonstrates")
- Be removed if they can't be supported

**Stage 3 (Writing)**: Writing agents receive the scored matrix. For STRONG claims, they write with confidence. For WEAK claims, they must use hedged language and explicitly note the limitation.

**Stage 5 (QA)**: Reviewers get the heatmap. A paper where all claims score MODERATE or above is in good shape. Any WEAK/CRITICAL claims that survived to QA are mandatory fix items.

**`/auto` iterations**: Assessment agents use scores to identify the highest-impact improvements. Strengthening a WEAK claim from 2.0 to 6.0 is higher priority than polishing prose in a section with all STRONG claims.

### Scoring Agent

A lightweight scoring step (not a separate agent spawn — just logic in the main pipeline) that runs:
1. After Stage 2 builds the claims matrix
2. After Stage 1d updates source access levels
3. After any `/auto` iteration adds new evidence

The scoring reads `research/claims_matrix.md` and `research/sources/*.md` (for access levels), computes scores, and rewrites the matrix with scores.

## Files to Modify

1. Pipeline stage files:
   - `template/claude/pipeline/stage-2-planning.md` — Add scoring step after claims matrix creation
   - `template/claude/pipeline/stage-1d-source-acquisition.md` — Change acquisition priority from citation-count to evidence-impact
   - `template/claude/pipeline/stage-3-writing.md` — Add scored matrix to writing agent context
   - `template/claude/pipeline/stage-5-qa.md` — Add scored matrix to reviewer agent context
2. `template/claude/commands/auto.md`:
   - Assessment agents receive scored matrix
   - Prioritization uses scores
3. `template/claude/commands/audit-sources.md`:
   - Phase 5 (update claims matrix) now includes score recomputation
4. `template/claude/CLAUDE.md`:
   - Document evidence scoring in claims-evidence matrix section

## Files to Create

None.

## Risks

- Scoring is inherently subjective (what counts as "direct" relevance?). Mitigation: the scores are guidance, not gates. No claim is auto-rejected based on score alone.
- Adding columns to the matrix increases its width. Mitigation: use compact notation for the sources column.

## Acceptance Criteria

- [ ] Claims-evidence matrix includes per-claim scores and strength labels
- [ ] Source acquisition in Stage 1d prioritizes by evidence impact
- [ ] Writing agents receive scored matrix and adjust confidence language accordingly
- [ ] QA reviewers receive the heatmap and flag WEAK/CRITICAL claims
- [ ] `/auto` assessment agents use scores for prioritization
- [ ] Scores recompute after source access level changes
