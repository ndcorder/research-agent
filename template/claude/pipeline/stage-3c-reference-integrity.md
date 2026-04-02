# Stage 3c: Reference Integrity Check

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol.

---

This stage runs after cross-section coherence (Stage 3b) and before figures (Stage 4). It verifies that every citation in the manuscript has real backing artifacts and that cited sources actually support the claims being made.

Two phases: (1) programmatic artifact integrity check, (2) agent-based misattribution detection.

## Phase 1: Artifact Integrity (automated)

Run the verification script:

```bash
python3 scripts/verify-references.py --fix --json --no-api
```

Read the JSON output from `research/reference_integrity.json`.

**Interpret results:**
- **VERIFIED**: No action needed.
- **MISSING_BIB**: A `\cite{key}` in the manuscript has no `references.bib` entry. This should not happen if the pipeline ran correctly. Log a warning.
- **MISSING_EXTRACT**: Citation exists in bib but has no source extract in `research/sources/`. The pipeline found the paper but never created an extract. Run a quick web search to confirm the paper exists. If confirmed, create a minimal source extract with `Access Level: METADATA-ONLY`. If not found, classify as FABRICATED and let `--fix` handle removal.
- **EMPTY_SNAPSHOT**: Source extract exists but has no Content Snapshot. Similar to MISSING_EXTRACT — the paper was referenced but never read. Flag for QA but do not block.
- **METADATA_OVERCLAIM**: A citation with `Access Level: METADATA-ONLY` is used in the manuscript. The writing agent cited a paper it only has title/authors for. Flag for QA — the claim may need hedging or the source needs upgrading.
- **FABRICATED**: `--fix` already removed these. Log the count and keys.

**If any FABRICATED references were removed:**
1. Log to provenance (the script does this automatically with `--fix`)
2. Re-read `main.tex` to check for orphaned sentences (sentences that lost their only citation)
3. For each orphaned sentence, insert `% [NEEDS-CITATION]` as a LaTeX comment on the line above
4. Note the removed references in `.paper-state.json` under `stages.reference_integrity.fabricated_removed`

**Gate**: Proceed to Phase 2 only if zero FABRICATED references remain. MISSING_EXTRACT and METADATA_OVERCLAIM are warnings — they inform Phase 2 priorities but do not block.

## Phase 2: Misattribution Detection (agent-based)

Spawn one **misattribution-check agent** per manuscript section (model: `claude-sonnet-4-6[1m]`), run in parallel.

**Prioritization**: Process sections in risk order based on `research/claims_matrix.md`:
- **High priority** (thorough check): Sections containing WEAK (1-2.9) or MODERATE (3-5.9) claims
- **Standard** (lighter pass): Sections with all STRONG (≥6) claims

### Agent prompt template

For each section, spawn an agent with this prompt:

```
You are a citation integrity auditor verifying that every reference in a manuscript section actually supports the claim being made. You have access to the original source extracts — the Content Snapshots showing exactly what the pipeline read from each paper.

Read ALL of the following files:
1. The section text (provided below)
2. research/claims_matrix.md — focus on claims assigned to this section
3. research/reference_integrity.json — skip keys already flagged as MISSING_EXTRACT or METADATA_OVERCLAIM
4. For EACH citation key in this section, read: research/sources/<key>.md

For every citation in the section, check:

1. **Claim-evidence alignment**: Does the Content Snapshot in the source extract actually contain evidence for the claim being made? If the claim says "Smith showed X" but Smith's snapshot discusses Y, this is a MISATTRIBUTION.

2. **Strength match**: Is the claim language appropriate for the source's access level?
   - FULL-TEXT sources: confident claims allowed if evidence is in the snapshot
   - ABSTRACT-ONLY sources: claims should be hedged ("reportedly", "according to the abstract")
   - METADATA-ONLY sources: only existence claims ("Smith et al. (2024) investigated...")

3. **Warrant presence**: Does the paragraph explain WHY the cited evidence supports the claim? A bare citation without reasoning is a CITATION_DUMP.

4. **Scope creep**: Does the claim generalize beyond what the source snapshot actually showed? (e.g., "widely adopted" when the source says "tested in lab conditions")

5. **Attribution accuracy**: Is the specific finding attributed to the correct paper? Cross-reference against other source extracts to check for mix-ups.

**Output format** — write findings to research/misattribution_check/<section_name>.md:

# Misattribution Check: <Section Name>

## Issues Found: <N>

For each issue:

### <ISSUE_TYPE> (line <N>)
- **Claim**: "<exact text from manuscript>"
- **Cited**: <bibtex_key> (<access_level>)
- **Source says**: <what the Content Snapshot actually contains>
- **Severity**: HIGH | MEDIUM | LOW
- **Fix**: <specific remediation suggestion>

Issue types: MISATTRIBUTION, OVERCLAIM, CITATION_DUMP, SCOPE_CREEP, WRONG_ATTRIBUTION

If no issues found, write: "## Issues Found: 0\n\nAll citations verified against source extracts."

PROVENANCE — After completing the audit, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"3c","agent":"misattribution-checker-<section>","action":"review","target":"<section>","reasoning":"Cross-checked N citations against source extracts","diff_summary":"Found M issues (H high, M medium, L low)","iteration":0}
```

### After all agents complete

1. Read all files in `research/misattribution_check/`
2. For each HIGH severity issue, insert `% [CITATION-CHECK: <brief issue>]` as a LaTeX comment above the flagged line in `main.tex`
3. MEDIUM and LOW issues are logged but not marked in tex — QA reviewers will read the full reports
4. Update `.paper-state.json`:
   ```json
   "reference_integrity": {
     "done": true,
     "fabricated_removed": [],
     "misattribution_issues": {"high": 0, "medium": 0, "low": 0},
     "sections_checked": []
   }
   ```
5. **Do NOT block the pipeline** on misattribution issues. They are inputs to QA (Stage 5), not hard gates.

## QA Integration

Stage 5 QA reviewers MUST read:
- `research/reference_integrity.json` — know which references are VERIFIED vs flagged
- `research/misattribution_check/*.md` — prioritize HIGH severity issues
- Any `% [CITATION-CHECK: ...]` comments in `main.tex`

QA reviewers should verify that HIGH misattribution issues have been addressed. If not addressed by QA iteration 3, escalate to the user.
