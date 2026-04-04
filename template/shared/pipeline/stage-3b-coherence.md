# Stage 3b: Cross-Section Coherence Check

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol.

---

This stage runs after section writing (Stage 3) and before figures (Stage 4). Its purpose is to verify that the manuscript reads as a unified argument, not a collection of disconnected sections. A single holistic agent performs the analysis because coherence is inherently a whole-manuscript property.

## Coherence Analysis

Spawn a **single coherence analysis agent** (model: `claude-opus-4-6[1m]`):

```
You are an expert scientific editor performing a cross-section coherence audit. Your job is to read the entire manuscript and verify that it functions as one unified argument, not a set of independently written sections stitched together.

Read ALL of the following files completely:
- main.tex (the full manuscript)
- research/claims_matrix.md (claims, evidence, warrants, qualifiers, rebuttals)
- research/thesis.md (thesis statement and contribution)
- research/assumptions.md (methodological assumptions analysis)
- research/literature_synthesis.md (if it exists — skip silently if not)

Then perform the five checks below. For every issue found, classify its severity:
- CRITICAL — must be fixed before proceeding to Stage 4. The paper has a structural contradiction, broken promise, or missing argument that would confuse or mislead a reader.
- MAJOR — should be fixed; likely to be caught by reviewers. Deferred to Stage 5 QA if not critical.
- MINOR — note for later. Does not block progress.

---

### Check 1: Promise Fulfillment

Read the Abstract and Introduction carefully. List every explicit promise made to the reader:
- Contributions claimed
- Findings previewed
- Scope stated ("we focus on X", "we show that Y")
- Structure previews ("Section 3 describes...", "we evaluate on...")

For each promise, locate the section and paragraph where it is fulfilled. Record whether the fulfillment is:
- COMPLETE — the promise is fully delivered
- PARTIAL — some aspect is addressed but not the full claim
- MISSING — no corresponding content found in the paper

Specific checks:
- Does Results actually present evidence for every claim made in the Abstract?
- Does Discussion address every limitation mentioned or implied in Methods?
- If the Introduction says "we make N contributions", are exactly N contributions demonstrably present?

Severity: MISSING promise = CRITICAL. PARTIAL fulfillment = MAJOR.

### Check 2: Concept Consistency

Build a concept registry: every key term, method name, framework, acronym, and technical concept introduced in the paper. For each concept, record:
- Where it is first defined or introduced
- Every subsequent use (section and approximate location)
- Whether the definition is consistent across all uses

Flag these issues:
- A concept used before it is introduced or defined: MAJOR.
- A term defined in one section but used with a subtly different meaning elsewhere: MAJOR.
- An acronym used without prior expansion: MINOR (unless the acronym is ambiguous, then MAJOR).
- If Related Work criticizes approach X, but Methods uses approach X without acknowledging or addressing the criticism: CRITICAL.
- If two different terms are used interchangeably for the same concept without noting the equivalence: MINOR.

### Check 3: Rebuttal Threading

Read the Rebuttal column in research/claims_matrix.md. For each rebuttal listed:
1. Find the cited location in the paper where the rebuttal is supposedly addressed.
2. Verify the rebuttal is actually present and substantive at that location.
3. Check that the rebuttal is responsive to the counterargument (not a tangential deflection).

Additional checks:
- Do counterarguments raised in Related Work get answered in Discussion?
- Do limitations flagged in research/assumptions.md (especially RISKY and CRITICAL assumptions) appear in the Discussion limitations subsection?
- Are there counterarguments obvious to a domain expert that are neither in claims_matrix.md nor addressed in the paper?

Severity:
- Rebuttal listed in claims matrix but missing from the paper entirely: MAJOR.
- Rebuttal references the wrong section or paragraph: MINOR.
- RISKY/CRITICAL assumption from assumptions.md absent from Discussion limitations: MAJOR.

### Check 4: Narrative Arc

Evaluate the paper's flow as a single argument:
- Does the paper build coherently from problem statement -> approach -> evidence -> interpretation -> conclusion?
- Are there abrupt topic shifts between sections? (A section ending on topic A while the next begins on unrelated topic B with no transition.)
- Does each section's opening paragraph connect to the previous section's closing?
- Does the Discussion explain WHY the results matter, not just restate what they are? Is there a clear "so what?" moment?
- Does the Conclusion introduce any new information, arguments, or citations not present earlier? (It should not.)
- Is there unnecessary repetition — the same point made in Introduction, Related Work, AND Discussion without adding new perspective each time?

Severity:
- Missing "so what?" in Discussion (results restated but not interpreted): CRITICAL.
- Abrupt topic shift with no transition between major sections: MAJOR.
- Conclusion introduces new claims or evidence: MAJOR.
- Excessive repetition without added perspective: MINOR.

### Check 5: Forward/Backward Reference Integrity

Find every internal cross-reference in the manuscript:
- "as we show in Section X" / "as discussed in Section Y"
- "see Table Z" / "see Figure N"
- "described above" / "as noted earlier" / "we return to this in Section X"

For each reference, verify:
1. The target section, table, or figure exists.
2. The target actually contains the content the reference claims. ("As we show in Section 4" should point to Section 4 content that demonstrates the stated claim.)
3. \ref{} and \label{} pairs resolve correctly.

Severity:
- Reference to a section/figure/table that does not exist: MAJOR.
- Reference exists but does not contain the claimed content: MAJOR.
- Vague backward reference ("as noted earlier") where the antecedent is ambiguous: MINOR.

---

Write your complete analysis to reviews/coherence_check.md using this format:

# Coherence Check Report

## Summary
- Total issues: [N]
- CRITICAL: [N]
- MAJOR: [N]
- MINOR: [N]

## Check 1: Promise Fulfillment
### Promises Found
1. [Promise text] — Source: [Abstract/Introduction, location] — Status: [COMPLETE/PARTIAL/MISSING] — Fulfilled at: [section/paragraph or "not found"] — Severity: [if not COMPLETE]

### Issues
- [SEVERITY] [description]

## Check 2: Concept Consistency
### Concept Registry
| Concept | First defined | Subsequent uses | Consistent? |
|-|-|-|-|

### Issues
- [SEVERITY] [description]

## Check 3: Rebuttal Threading
### Rebuttal Verification
| Claim | Rebuttal (from matrix) | Cited location | Actually present? | Substantive? |
|-|-|-|-|-|

### Issues
- [SEVERITY] [description]

## Check 4: Narrative Arc
### Issues
- [SEVERITY] [description]

## Check 5: Forward/Backward Reference Integrity
### References Found
| Reference text | Source location | Target | Target exists? | Content matches? |
|-|-|-|-|-|

### Issues
- [SEVERITY] [description]
```

## Revision of CRITICAL Issues

If the coherence analysis found any CRITICAL issues, spawn a **targeted revision agent** (model: `claude-opus-4-6[1m]`):

```
You are revising a research paper to fix CRITICAL coherence issues found during a cross-section coherence check.
Invoke the `scientific-writing` skill.

Read the following files:
- reviews/coherence_check.md (the coherence analysis — focus ONLY on CRITICAL issues)
- main.tex (the manuscript to edit)
- research/claims_matrix.md (for claim-evidence relationships)
- research/thesis.md (for the paper's thesis and contribution statement)

Fix EVERY CRITICAL issue listed in the coherence check. For each fix:
1. Locate the problem in main.tex
2. Make the minimal edit that resolves the issue while maintaining consistency with surrounding text
3. If a promise in the Abstract/Introduction has no fulfillment, either add the fulfillment in the appropriate section OR remove the promise — do not leave it dangling
4. If Related Work criticizes an approach that Methods uses, add an explicit acknowledgment and justification in Methods
5. If Discussion merely restates results without interpretation, add substantive interpretation explaining why the results matter

Do NOT fix MAJOR or MINOR issues — those are deferred to Stage 5 QA where reviewers will catch them in full context.

Edit main.tex directly.

PROVENANCE — After EACH revision, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"3b","agent":"coherence-revision","action":"revise","target":"[section/pN]","reasoning":"[why — reference the specific coherence check issue]","feedback_ref":"reviews/coherence_check.md#[issue]","diff_summary":"[what changed]","sources":["keys"],"iteration":0}
For any content cuts, save removed text to provenance/cuts/[section]-[pN]-coherence.tex and record in archived_to field.
```

## Verification of Fixes

After the revision agent completes, re-run **only the specific checks that had CRITICAL issues**. Do NOT re-run all five checks.

Spawn a **verification agent** (model: `claude-sonnet-4-6[1m]`):

```
You are verifying that CRITICAL coherence issues were fixed.

Read:
- reviews/coherence_check.md (the original coherence analysis)
- main.tex (the revised manuscript)

The following checks had CRITICAL issues: [LIST ONLY THE CHECK NUMBERS THAT HAD CRITICAL ISSUES]

For each CRITICAL issue from those checks:
1. Locate where the fix should be in main.tex
2. Verify the issue is resolved
3. Verify the fix did not introduce new problems (e.g., fixing a promise by adding content that contradicts another section)

Write your verification to reviews/coherence_verification.md:
- For each CRITICAL issue: RESOLVED / UNRESOLVED / PARTIALLY RESOLVED
- Any new issues introduced by the fixes

If any CRITICAL issue remains UNRESOLVED, flag it clearly — the orchestrator will need to address it before proceeding.
```

If verification finds UNRESOLVED CRITICAL issues, the orchestrator must fix them manually before proceeding to Stage 4. Do not loop — a single revision pass plus verification is sufficient. Persistent issues indicate a structural problem that requires orchestrator judgment.

## Checkpoint

Update `.paper-state.json`:

```json
"stages": {
  "coherence": {
    "done": true,
    "completed_at": "[ISO-8601 timestamp]",
    "issues_found": {
      "critical": 0,
      "major": 0,
      "minor": 0,
      "total": 0
    },
    "critical_fixed": 0,
    "verification_passed": true
  }
}
```

Set `done: false` while the stage is in progress. Set `verification_passed` to `true` if no CRITICAL issues were found OR if all CRITICAL issues were verified as RESOLVED. Set to `false` if any CRITICAL issues remain UNRESOLVED after verification.

---
