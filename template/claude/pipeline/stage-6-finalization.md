# Stage 6: Finalization

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol.

---

Spawn a **final polish agent** (model: claude-opus-4-6[1m]):
```
You are a senior editor doing the final pass before journal submission.
Invoke the `scientific-writing` skill.
Read main.tex completely.

Final improvements:
1. Abstract accurately summarizes the final content (specific results/numbers)
2. Title is specific, compelling, and accurately reflects the contribution
3. Introduction's "paper organization" paragraph matches actual sections
4. Conclusion references actual results with specific numbers
5. Remove redundancies, tighten prose, fix any remaining rough edges
6. Verify consistent formatting: heading caps, citation style, notation, abbreviation definitions
7. Ensure first use of abbreviations includes full form
8. Final compile: latexmk -pdf -interaction=nonstopmode main.tex

Report: word count per section, total words, citation count, page count.
Edit main.tex directly.

PROVENANCE — After completing all edits, append a summary provenance entry to research/provenance.jsonl with action "revise", stage "6", agent "final-polish", target "all", and reasoning listing the categories of changes made. Set iteration to 0.
```

After polish, generate a **lay summary** (model: claude-sonnet-4-6[1m]):
```
Read main.tex completely. Generate:
1. A 200+ word plain-language summary (no jargon, high school reading level)
2. A 2-3 sentence elevator pitch
Write both to research/summaries.md.
If .venue.json indicates the venue requires a lay summary (Nature, medical journals), add it to main.tex after the abstract.
```

**De-AI Polish** — remove AI writing patterns (model: claude-opus-4-6[1m]):
```
You are an expert editor removing AI-generated writing patterns.
Read main.tex completely.

Search for and replace these common AI writing tells:
1. **Hedging overuse**: "it is worth noting that", "it should be noted", "it is important to mention" → remove or rephrase directly
2. **AI vocabulary**: "delve", "realm", "landscape", "tapestry", "multifaceted", "furthermore", "moreover" at sentence starts → use simpler transitions or remove
3. **Formulaic structures**: "In this section, we..." openers on every section → vary openings
4. **Repetitive connectors**: "Additionally", "Furthermore", "Moreover" used repeatedly → diversify or remove
5. **Passive hedging**: "it can be observed that", "it is evident that" → state the observation directly
6. **Empty emphasis**: "significantly", "notably", "remarkably" without quantification → remove or add numbers
7. **Redundant phrasing**: "in order to" → "to", "a total of" → remove, "the fact that" → remove
8. **Flowery conclusions**: "In conclusion, this groundbreaking work..." → tone down to academic neutral
9. **List-to-prose artifacts**: Sentences that read like expanded bullet points → rewrite as flowing prose
10. **Uniform paragraph length**: If all paragraphs are ~same length, vary them for natural rhythm
11. **Em dashes and en dashes**: Replace ALL em dashes (—) and en dashes used as punctuation (–) with commas, parentheses, colons, or separate sentences. Number ranges may keep en dashes. Em dashes are the single most recognizable AI writing tell.

Do NOT change technical content, citations, or mathematical notation.
Do NOT remove necessary hedging (e.g., "may" when results are genuinely uncertain).
Focus on making the paper read like a human domain expert wrote it.
Edit main.tex directly.

PROVENANCE — After completing all edits, append a summary provenance entry to research/provenance.jsonl with action "revise", stage "6", agent "de-ai-polish", target "all", and reasoning listing the categories of changes made and counts per category. Set iteration to 0.
```

Then do one final compile and report results.

**Provenance Report** — Generate a human-readable provenance report from the ledger. Spawn an agent (model: claude-sonnet-4-6[1m]):
```
You are a provenance report generator.
Read research/provenance.jsonl completely. Parse each JSON line.

Generate research/provenance_report.md with this structure:

# Provenance Report
Generated: [timestamp]

## Summary
- Total actions logged: N
- Writing actions: N (paragraphs originally written)
- Revisions: N (changes from QA feedback)
- Expansions: N (content added for depth)
- Cuts: N (content removed)
- Planning decisions: N
- Research actions informing writing: N
- Unique sources referenced: N (list of BibTeX keys)
- Claims covered: N / total claims in matrix

## Timeline
[Chronological list of all actions, grouped by stage]

## Section Provenance
### Introduction
[For each paragraph in this section, show:]
#### Paragraph 1 (introduction/p1)
- **Written by**: [agent], Stage [N]
- **Sources**: [list of BibTeX keys with paper titles]
- **Claims supported**: [C1, C3]
- **Writing reasoning**: [from the reasoning field]
- **Revision history**: [list of subsequent revisions, if any, with reasoning and feedback refs]

### Methods
[same structure]
...

## Cuts Archive
[List all cuts with: what was removed, from where, why, and where the original text is archived]

## Untraced Content
[Flag any paragraphs in main.tex that have NO provenance entry — these are gaps in the trace]
```

Write the report to research/provenance_report.md.

Finally, **archive all research artifacts** by running the `/archive` command. This creates a self-contained `archive/` directory with all research notes, reviews, figures, data, and metadata organized for easy browsing, with a README index. This allows the user to browse through all research findings, downloaded materials, and intermediate outputs after the pipeline completes.

**Report Codex collaboration metrics:**

```
mcp__codex-bridge__codex_stats({})
```

Include the Codex stats in the final completion report to show how the two AI systems collaborated throughout the pipeline.

---
