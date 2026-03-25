# Provenance — Query the Paper's Audit Trail

Trace any word in the paper back to its origin. Query the provenance ledger to understand why something was written, what sources informed it, and how it changed over time.

## Instructions

1. **Read `research/provenance.jsonl`** — parse each line as JSON
2. **Read `main.tex`** — to cross-reference current content with provenance targets

### Query Modes

Based on $ARGUMENTS, run one of these queries:

**No arguments** — show the full provenance summary:
- Total actions, breakdown by type
- Coverage: which paragraphs have provenance entries, which don't
- Source utilization: which sources are cited most in provenance, which are unused

**Section name** (e.g., `methods`, `discussion`) — show provenance for that section:
- For each paragraph: who wrote it, what sources informed it, reasoning, revision history
- Any cuts from this section (with archived content paths)

**`trace <claim-id>`** (e.g., `trace C3`) — trace a specific claim:
- Which paragraphs support this claim
- What sources provide the evidence
- What writing reasoning connects claim to evidence
- Any revisions that affected this claim's presentation

**`history <target>`** (e.g., `history methods/p3`) — show full history of a specific paragraph:
- Original writing (agent, sources, reasoning)
- Every revision (what changed, why, what feedback triggered it)
- If cut: when, why, where archived

**`sources <bibtex-key>`** (e.g., `sources smith2024`) — show everywhere a source was used:
- Which paragraphs it informed
- What specific content from the source extract was referenced
- Whether it was used for claims, background, or methodology justification

**`gaps`** — find untraced content:
- Paragraphs in main.tex with no provenance entry
- Claims in the matrix with no linked provenance
- Sources in references.bib never referenced in any provenance entry

**`timeline [stage]`** — chronological view of all actions (optionally filtered by stage)

### Output Format

Present results as a readable markdown report. For paragraph histories, include before/after diffs where revision entries have diff_summary fields. For claims traces, show the full chain: source → provenance entry → paragraph → claim.

## Arguments

$ARGUMENTS
