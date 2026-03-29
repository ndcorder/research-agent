# Stage 2e: Methodological Assumptions Analysis

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Codex Deliberation Protocol.

---

**This stage runs after novelty verification (Stage 2d), before writing begins (Stage 3).**

Spawn an assumptions analysis agent (model: claude-opus-4-6[1m]):

```
You are a methodological critic analyzing the assumptions behind a proposed research approach.
Read research/thesis.md for the contribution statement.
Read main.tex for the outline, especially the Methods section plan.
Read research/methods.md for the methodological landscape (if it exists).
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

After the agent produces `research/assumptions.md`, query the knowledge graph for evidence on risky and critical assumptions (run if `research/knowledge/` exists — if not, log `"⚠ Knowledge graph not available — assumption evidence will be verified from source extracts only"` and for each RISKY/CRITICAL assumption, manually search `research/sources/` for evidence supporting or contradicting the assumption):

```bash
python scripts/knowledge.py evidence-for "[assumption] is valid"
python scripts/knowledge.py evidence-against "[assumption] is valid"
```

Run these for every RISKY and CRITICAL assumption. Update `research/assumptions.md` with any evidence the graph surfaces (add to the Prior Art and Justification fields).

### Codex Assumptions Review

After the assumptions agent completes and knowledge graph queries are done, call Codex directly in your main session:

```
mcp__codex-bridge__codex_ask({
  prompt: "Review these methodological assumptions for a research paper. For each assumption: (1) Is the categorization correct? (e.g., is anything marked STANDARD that should be RISKY, or REASONABLE that should be CRITICAL?) (2) Are any assumptions MISSING that a reviewer would flag? (3) Are the proposed mitigations adequate? (4) Are there implicit assumptions not yet identified?",
  context: "[paste content of research/assumptions.md]"
})
```

Apply the **Codex Deliberation Protocol**. Update `research/assumptions.md` based on agreed feedback (e.g., recategorize assumptions, add missing ones). Log deliberation to `reviews/codex_deliberation_log.md`.

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"2e","tool":"codex_ask","purpose":"assumptions categorization review","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"research/assumptions.md","resolution_summary":"[one-line]"}
```

### Provenance

Append a provenance entry to `research/provenance.jsonl`:
```json
{"ts":"[timestamp]","stage":"2e","agent":"assumptions-analysis","action":"plan","target":"assumptions","reasoning":"[summary of assumptions found and their categories]","sources":["thesis.md","claims_matrix.md","main.tex"]}
```

**Checkpoint**: Verify `research/assumptions.md` exists and contains categorized assumptions. If it does not exist, the agent failed — retry once with a simplified prompt focusing only on CRITICAL and RISKY assumptions.

Update `.paper-state.json`: mark `assumptions` as done.
