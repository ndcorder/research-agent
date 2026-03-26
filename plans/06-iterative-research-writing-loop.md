# Plan 06: Iterative Research-Writing Loop

## Problem

The pipeline is strictly sequential: research (Stage 1) → plan (Stage 2) → write (Stage 3) → QA (Stage 5). Writing never triggers new research except in deep mode's per-section lit searches. But writing reveals gaps that weren't visible during planning — a paragraph about a specific technique may need a citation that no research agent thought to find, or a comparison table may need data points from papers not yet in the bibliography.

Currently these gaps are caught in Stage 5 QA, which triggers revision but not new research. The revision agent either hedges the claim, removes it, or hopes an existing reference covers it. This is a missed opportunity.

## Goal

Add a lightweight evidence-check loop between section writing and the next section, so under-supported claims trigger targeted micro-research before the gap compounds across sections.

## Design

### The Loop

After each section writing agent completes (Stage 3), before moving to the next section:

1. **Evidence Check** — A fast agent (model: haiku) reads the just-written section and cross-references it against the claims-evidence matrix and source extracts:

```
You are an evidence gap detector. Read the [SECTION] section that was just written in main.tex.
Also read research/claims_matrix.md and the source extracts in research/sources/.

For each claim or factual statement in this section:
1. Is it supported by a citation? If not, flag it.
2. If cited, does the source extract for that citation actually contain content supporting this specific claim? (Check research/sources/<key>.md)
3. Are there claims that go BEYOND what the source extract says? (e.g., claiming "X shows that..." when the source extract only contains an abstract)

Output a list of evidence gaps:
- GAP: [section/paragraph] — [claim text] — [what's missing: citation needed / source is abstract-only / claim exceeds source content]
- OK: [section/paragraph] — [claim text] — [supported by: key (access level)]

Write to reviews/evidence_gaps_[SECTION].md
```

2. **Decision Gate** — If gaps are found:
   - **0 gaps**: Proceed to next section immediately
   - **1-2 gaps, minor** (missing citation for a well-known fact): The next writing agent can note these, or they'll be caught in QA. Proceed.
   - **3+ gaps OR any gap where a claim exceeds source content**: Trigger a micro-research step before the next section.

3. **Micro-Research** (when triggered) — A targeted agent (model: sonnet) gets exactly the gaps to fill:

```
You are a targeted research agent filling evidence gaps found during writing.
TOPIC: [TOPIC]
TOOL FALLBACK: [standard chain]

Fill these specific gaps:
[paste gap list]

For each gap:
1. Search for a paper that directly supports the claim
2. If found: add to references.bib, create source extract in research/sources/, note the BibTeX key
3. If NOT found: report that the claim may need to be hedged or removed

Budget: maximum 2 search queries per gap. Be precise.
Write findings to research/section_gaps_[SECTION].md.
Add new references to references.bib.
RESEARCH LOG: Append entries to research/log.md.
```

4. **Patch** — After micro-research, the NEXT section's writing agent is told about the new references so it can use them. Also, if gaps in the just-written section were filled with new citations, a quick edit pass adds the citations to main.tex.

### Depth Mode Behavior

| Setting | Standard | Deep |
|-|-|-|
| Evidence check | After every section | After every section |
| Gap threshold for micro-research | 3+ gaps | 1+ gap |
| Max search queries per gap | 2 | 4 |
| Also re-check after micro-research | No | Yes (verify gaps were filled) |

In standard mode, the evidence check is cheap (haiku) and micro-research is rare. In deep mode, it's more aggressive but still bounded.

### Integration with Knowledge Graph

If the knowledge graph is available, the evidence check agent also queries it:

```bash
python scripts/knowledge.py evidence-for "[claim from gap]"
```

Sometimes the evidence exists in the graph (from a source that the writing agent didn't think to cite) and no new research is needed — just add the citation.

### Pipeline Flow Change

Current Stage 3:
```
Write Intro → Write Related Work → Write Methods → Write Results → Write Discussion → Write Conclusion → Write Abstract
```

New Stage 3:
```
Write Intro → Evidence Check → [Micro-Research if needed] →
Write Related Work → Evidence Check → [Micro-Research if needed] →
Write Methods → Evidence Check → [Micro-Research if needed] →
Write Results → Evidence Check → [Micro-Research if needed] →
Write Discussion → Evidence Check → [Micro-Research if needed] →
Write Conclusion → Evidence Check →
Write Abstract
```

The Conclusion and Abstract don't trigger micro-research (they summarize, not introduce new claims).

### State Tracking

Add to `.paper-state.json` under the writing stage:
```json
"writing": {
  "sections": {
    "introduction": { "done": true, "words": 1250, "evidence_gaps": 1, "micro_research": false },
    "related_work": { "done": true, "words": 2100, "evidence_gaps": 4, "micro_research": true, "new_refs": 3 },
    "methods": { "done": true, "words": 1800, "evidence_gaps": 0, "micro_research": false }
  }
}
```

## Files to Modify

1. `template/claude/pipeline/stage-3-writing.md`:
   - Add evidence check step after each section writing agent
   - Add micro-research trigger logic
   - Update state tracking format

## Files to Create

None.

## Risks

- Evidence check after every section adds latency. Mitigation: uses haiku (fast), and micro-research only triggers when gaps exceed threshold.
- Micro-research could add low-quality references. Mitigation: all new references go through the same verification as Stage 1 bibliography builder.
- Could create an infinite loop if gaps keep appearing. Mitigation: micro-research runs at most once per section — if gaps remain after research, they're deferred to QA.
- The evidence check may be overly strict (flagging common knowledge that doesn't need a citation). Mitigation: the agent is instructed to only flag claims that would raise a reviewer's eyebrow if uncited.

## Acceptance Criteria

- [ ] Evidence check runs after each section in Stage 3
- [ ] Gap detection cross-references claims matrix and source extracts
- [ ] Micro-research triggers when gap threshold is exceeded
- [ ] New references from micro-research are verified and added to references.bib
- [ ] Source extracts created for all new papers
- [ ] Knowledge graph queried for existing evidence before triggering new research
- [ ] State tracking records gaps and micro-research per section
- [ ] Conclusion and Abstract skip micro-research
- [ ] Micro-research runs at most once per section (no infinite loops)
