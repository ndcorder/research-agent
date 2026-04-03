# Stage 6: Finalization

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol.

---

**Pre-Finalization Scooping Check**

Before any polish or finalization, check whether recent preprints overlap with this paper's contribution. Spawn a **scooping check agent** (model: claude-sonnet-4-6[1m]):
```
You are a preprint scooping detector. Your task is to determine whether any very recent preprints significantly overlap with this paper's contribution.

Read:
- .paper.json for the topic and keywords
- research/thesis.md for the contribution statement
- .paper-state.json for the pipeline start date (if available — fall back to "last 14 days" if not)

TOOL FALLBACK CHAIN — try in this order:
1. Perplexity search (mcp__perplexity__search or mcp__perplexity__reason)
2. Web search (WebSearch tool)
3. Firecrawl search (mcp__firecrawl__firecrawl_search)

Search for recent preprints:
1. Search arXiv for: [paper topic keywords] published in the last 14 days (or since pipeline start date)
2. If the paper is biomedical/clinical (detect from topic keywords: medical, clinical, health, disease, drug, gene, protein, biomarker, patient, therapy, diagnosis), also search bioRxiv and medRxiv
3. Search Semantic Scholar for very recent papers matching the topic

For each potentially conflicting preprint found:
1. Read the title and abstract
2. Assess overlap with our contribution statement:
   - HIGH: The preprint makes the same core contribution (same method applied to same problem, or same finding). This would significantly diminish our novelty.
   - MEDIUM: The preprint addresses the same problem but with a different approach, or makes a related but distinct contribution. Should be cited and differentiated.
   - LOW: The preprint is in the same field but does not overlap with our specific contribution.

Write findings to reviews/scooping_check.md with this format:

# Pre-Finalization Scooping Check
Date: [timestamp]
Search window: [start date] to [today]

## Summary
- Searched: arXiv [and bioRxiv/medRxiv if applicable]
- Potentially relevant preprints found: N
- HIGH overlap: N
- MEDIUM overlap: N
- LOW overlap: N

## Findings

### [If HIGH overlap found]
⚠️ HIGH OVERLAP DETECTED — Review before proceeding

**Title**: [preprint title]
**Authors**: [authors]
**Posted**: [date]
**URL/DOI**: [link]
**Overlap assessment**: [detailed explanation of how this overlaps with our contribution]
**Recommendation**: STOP — the user should review this preprint and decide whether to proceed, pivot the contribution, or cite and differentiate.

### [For MEDIUM overlap]
**Title**: [preprint title]
**Authors**: [authors]
**Posted**: [date]
**URL/DOI**: [link]
**Overlap assessment**: [explanation]
**Recommendation**: Cite this preprint and explicitly differentiate our contribution in the Introduction or Related Work.

### [For LOW overlap]
**Title**: [preprint title] — LOW overlap, noted for awareness.
```

If the scooping check finds **HIGH overlap**:
- **STOP the pipeline** and alert the user immediately
- Print the scooping report summary
- Ask the user to decide: proceed (with differentiation), pivot the contribution, or abandon
- Do NOT continue to the polish step until the user responds

If only **MEDIUM** or **LOW** overlap (or no overlapping preprints found):
- Print a brief summary: "Scooping check: [N] preprints reviewed, no high overlap found."
- If MEDIUM overlaps exist, note: "Consider citing [N] recent related preprints — see reviews/scooping_check.md"
- Proceed to the polish step

---

**Preamble Audit** — Before polish, verify the LaTeX preamble is correct. Check main.tex:

1. `\pdfoutput=1` present within first 5 lines
2. `\label{}` always comes after `\caption{}` in every float (search for the pattern)
3. No packages from `.venue.json` `forbidden_packages` are loaded
4. hyperref is loaded after most other packages (before cleveref if present)
5. No `$$...$$`, no `eqnarray`, no bare `[h]` or `[H]` float specifiers
6. All `\begin{figure}` and `\begin{table}` environments use `[htbp]` or `[!htbp]`
7. Compile with `latexmk -pdf -interaction=nonstopmode main.tex` and check for:
   - Zero `Overfull \hbox` warnings > 1pt (fix with rewording, not `\sloppy`)
   - Zero undefined reference warnings
   - Zero multiply-defined label warnings
8. If issues found, fix them before proceeding to polish

This is a mechanical check, not a creative task. Do it yourself (no agent needed).

---

**Quality Scorecard** — Run the quality scoring engine to produce the final paper scorecard:

```bash
python scripts/quality.py score --format json --project . > .paper-quality.json
python scripts/quality.py save --project . --checkpoint final
python scripts/quality.py score --format text --project .
```

Read the text output and include it in the final completion report. Store the JSON scorecard in `.paper-state.json` under `stages.quality_scores.final`.

If any dimension scores below 40, flag it as a known weakness in the completion report with the dimension-specific recommendation from `/score`.

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

Include the scooping check results in the final report. If `reviews/scooping_check.md` exists, append a summary:
```
## Scooping Check
- Searched arXiv [and domain preprint servers] for work posted since [pipeline start date]
- Found [N] potentially relevant preprints
- [NONE with significant overlap / Details of MEDIUM/LOW overlaps noted]
```

Finally, **archive all research artifacts** by running the `/archive` command. This creates a self-contained `archive/` directory with all research notes, reviews, figures, data, and metadata organized for easy browsing, with a README index. This allows the user to browse through all research findings, downloaded materials, and intermediate outputs after the pipeline completes.

**Report Codex collaboration metrics:**

```
mcp__codex-bridge__codex_stats({})
```

Include the Codex stats in the final completion report to show how the two AI systems collaborated throughout the pipeline.

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"6","tool":"codex_stats","purpose":"collaboration metrics","outcome":"N_A","points_raised":0,"points_accepted":0,"points_rejected":0,"artifact":"N/A","resolution_summary":"[total interactions reported by codex_stats]"}
```

---
