# Targeted Research — Resolve Specific Claims

Investigate one or more claim ids and update the paper's evidence base.

## Instructions

1. Read `.paper.json`, `main.tex`, `references.bib`, and `research/claims_matrix.md`.
2. Read `.codex/pipeline/shared-protocols.md` for tool fallback and provenance rules.
3. Parse claim ids from `$ARGUMENTS`:
   - `--claims C1,C2,...`
   - optional `--context "..."`
   - optional `--batch`
4. For each requested claim:
   - identify what evidence is missing
   - gather supporting and contradictory sources
   - update or create targeted notes in `research/`
   - add only verified references to `references.bib`
   - update claim evidence, score, and status in `research/claims_matrix.md` when warranted
5. Use `.codex/skills/` for domain-specific research skills when relevant.
6. Append provenance entries for all substantive changes.

$ARGUMENTS
