# Check Ref Integrity — Artifact Integrity + Misattribution Check

Run the full Stage 3c reference integrity check outside the pipeline. Useful for spot-checking during `/auto` iterations or standalone quality assurance.

## Instructions

This command runs two phases:

### Phase 1: Artifact Integrity

Run the verification script:

```bash
python3 scripts/verify-references.py --fix --json
```

Read `research/reference_integrity.json` and report results to the user.

- If any FABRICATED references were removed, summarize what was removed
- If MISSING_EXTRACT or METADATA_OVERCLAIM issues exist, list them with recommendations
- If all VERIFIED, confirm clean status

### Phase 2: Misattribution Detection

Read the instructions in `pipeline/stage-3c-reference-integrity.md`, Phase 2 section. Execute the misattribution detection agents for all manuscript sections.

Report a summary of all issues found, grouped by severity (HIGH, MEDIUM, LOW).

### When to use this command

- After adding new citations with `/add-citation`
- During `/auto` iterations when references changed
- Before `/prepare-submission` as a final check
- Any time you suspect citation quality issues
