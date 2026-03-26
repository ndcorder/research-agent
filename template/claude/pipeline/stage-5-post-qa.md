# Stage 5 Post-QA: Audits, Validation & Risk Assessment

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Codex Deliberation Protocol.

These steps run ONCE after the QA loop exits (all quality criteria met). They are NOT inside the loop.

---

## Consistency & Claims Audit

**These steps run ONCE after the QA loop exits (all quality criteria met).** They are NOT inside the loop.

Run two final audits **in parallel** (model: claude-sonnet-4-6[1m]):

**Consistency Checker:**
```
Read main.tex completely. Check for:
- Notation inconsistencies (same concept, different symbols)
- Terminology drift (same thing called different names)
- Abbreviations used before definition or defined twice
- Tense inconsistencies within sections
- Reference format inconsistencies (Figure vs Fig., Section vs Sec.)
Fix all issues directly in main.tex.
Write report to reviews/consistency.md.

PROVENANCE — For each fix applied, append a provenance entry to research/provenance.jsonl with action "revise", stage "post-qa", agent "consistency-checker", and reasoning explaining the inconsistency fixed.
```

**Claims Auditor:**
```
Read main.tex completely. For every claim, check:
- "novel"/"first" — is it actually, given the Related Work?
- "significantly" — is there a statistical test?
- "prove"/"demonstrate" — is there formal proof or only experiments?
- Unsupported factual claims missing citations
- Overclaims from limited experiments ("generalizes" from 2 datasets)
Fix Critical and Major overclaims in main.tex (soften language, add hedging, note missing tests).
Write report to reviews/claims_audit.md.

PROVENANCE — For each overclaim softened or hedging added, append a provenance entry to research/provenance.jsonl with action "revise", stage "post-qa", agent "claims-auditor", target "[section/pN]", and reasoning explaining what was overclaimed and how it was fixed.
```

After both complete, also spawn a **reproducibility checker** (model: claude-sonnet-4-6[1m]):
```
Read main.tex. Check if Methods section includes: all hyperparameters, training details, compute resources, dataset descriptions, evaluation metric definitions, random seed/variance info.
For each missing item, add it to the appropriate section in main.tex.
Write checklist to research/reproducibility_checklist.md.
```

---

## Reference Validation (mandatory before finalization)

Spawn a **reference validation agent** (model: claude-sonnet-4-6[1m]):
```
You are a reference verification specialist. Your job is to ensure every citation is real.
Read references.bib. For EACH entry:
1. If DOI present: verify via CrossRef API (curl -s "https://api.crossref.org/works/DOI")
2. If no DOI: search for exact title using Perplexity or web search
3. Classify: VERIFIED, METADATA MISMATCH, SUSPICIOUS, or FABRICATED
4. Fix metadata mismatches directly in references.bib
5. REMOVE fabricated entries from references.bib AND their citations from main.tex

Write validation report to research/reference_validation.md.
After fixes, compile: latexmk -pdf -interaction=nonstopmode main.tex
```

**This is non-negotiable.** Fabricated references are the #1 risk in AI-assisted writing. Every reference must be verified before the paper is finalized. Update `.paper-state.json` with validation results.

**Codex Independent Reference Verification**

In parallel with Claude's reference validation, have Codex independently verify a random sample of 10-15 references:

```
mcp__codex-bridge__codex_ask({
  prompt: "Verify these bibliographic references. For each one, confirm: (1) Is this a real publication? (2) Are the authors, title, venue, and year correct? (3) Does the DOI (if present) match? Flag any that seem fabricated, have wrong metadata, or that you cannot confirm exist.\n\nReferences to verify:\n[paste 10-15 randomly selected BibTeX entries from references.bib]",
  context: "[paste the selected BibTeX entries]"
})
```

Apply the **Codex Deliberation Protocol**: if Codex flags a reference that Claude's validator marked as verified, investigate further — one of them is wrong. If Codex confirms references Claude flagged as suspicious, that's stronger evidence for removal. Write results to `reviews/codex_ref_verification.md`.

---

## Codex Risk Radar

**Run this ONCE after reference validation, before finalization.**

Use Codex's risk radar tool to get a final risk assessment of the complete manuscript:

```
mcp__codex-bridge__codex_risk_radar({
  prompt: "Final risk assessment of this research manuscript before submission. Evaluate across these dimensions: (1) SCIENTIFIC RISK — are there claims that could be proven wrong or are unfalsifiable? (2) ETHICAL RISK — any issues with data handling, consent, bias, or dual-use concerns? (3) REPUTATIONAL RISK — anything that could embarrass the authors if scrutinized? (4) REPRODUCIBILITY RISK — could an independent team reproduce these results from the description? (5) NOVELTY RISK — is the contribution incremental enough that reviewers might desk-reject? Rate each dimension: LOW / MEDIUM / HIGH with specific evidence.",
  context: "[paste the full content of main.tex]"
})
```

Write the response to `reviews/codex_risk_radar.md`.

**Action on results:**
- Any HIGH risk item → must be addressed before finalization. Edit main.tex to mitigate (add caveats, strengthen methods, etc.)
- MEDIUM risk items → flag for the user's attention in the final report but don't block finalization
- LOW risk items → note and move on

**Checkpoint**: Verify `reviews/codex_risk_radar.md` exists.

Update `.paper-state.json`: mark `codex_risk_radar` as done.

---
