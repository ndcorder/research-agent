# Stage 3: Section-by-Section Writing

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol, Tool Fallback Chain, and Codex Deliberation Protocol.

---

Each section gets its own dedicated agent. **Run sequentially** — each section builds on prior ones.

**Abstract-First Strategy (default: ON)**

The draft abstract forces alignment across all sections — every writing agent knows what the paper promises to deliver. This is now the default behavior.

Check `.paper.json` for `"abstract_strategy"`. If explicitly set to `"last"`, skip this block. **Otherwise (including when absent or set to `"first"`), run it:**

1. **Before any section writing**, spawn a **draft abstract agent** (model: claude-opus-4-6[1m]):
```
You are an expert scientific writer. Your task is to draft a preliminary abstract that will serve as an alignment tool for all subsequent writing.

Read:
- research/thesis.md (thesis and contribution statement)
- The outline in main.tex (% OUTLINE comments)
- research/claims_matrix.md (what the paper will argue and with what evidence)

Write a 200-300 word draft abstract that:
1. States the problem and motivation
2. Describes the approach/method
3. Summarizes expected contributions and key claims
4. Notes the most important evidence/results the paper will present

This is a DRAFT — it will be rewritten after all sections are complete. Its purpose is to force clarity about what the paper promises to deliver.

Write the draft abstract to research/draft_abstract.md.
```

2. **Pass the draft abstract to every writing agent** (added automatically to the MUST include list below when `abstract_strategy` is `"first"`). Include this in each agent's prompt:
```
## Alignment: Draft Abstract
The following draft abstract defines what this paper promises to deliver. Ensure your section fulfills its relevant promises.

[contents of research/draft_abstract.md]
```

3. The **final abstract** (Order 7) is still rewritten from scratch after all sections are complete — it replaces the draft with one that matches the actual content.

If `abstract_strategy` is explicitly `"last"`, skip this block. This is the ONLY way to disable abstract-first — it must be an intentional opt-out.

---

**[DEEP] Per-Section Literature Deep-Dives**

If depth is `"deep"`, BEFORE each writing agent starts, spawn a quick **section research agent** (model: claude-sonnet-4-6[1m]) to find literature specific to that section's topic:

```
You are a focused research assistant. You have 1 task: find papers relevant to the [SECTION] section of a paper about [TOPIC].
The section outline says: [paste the % OUTLINE: comments for this section from main.tex]
TOOL FALLBACK: [same chain as Stage 1]

Search for:
1. Papers directly relevant to what this section will discuss
2. Specific data points, statistics, or results this section should cite
3. Recent work (2024-2026) on this specific subtopic

Write a concise list of 5-10 relevant papers with key findings to research/section_lit_[SECTION].md.
Full citation details. Add new references to references.bib.
RESEARCH LOG: [same format]
```

The writing agent for that section should then ALSO read `research/section_lit_[SECTION].md` for fresh, section-specific references.

**Every writing agent prompt MUST include:**
- The paper topic and contribution statement (from research/thesis.md)
- Instruction to read the FULL current main.tex for context
- Instruction to read references.bib for citation keys
- Instruction to read relevant research/ files for content
- Instruction to read `research/assumptions.md` for methodological assumptions (if it exists)
- If `.venue.json` exists: instruction to read it and follow the `writing_guide` field for venue-appropriate tone, structure, and conventions
- Unless `abstract_strategy` is explicitly `"last"` in `.paper.json`: instruction to read `research/draft_abstract.md` and ensure the section delivers on the abstract's promises (see Abstract-First Strategy above)
- Instruction to invoke the `scientific-writing` skill for prose quality
- The specific word count target as a MINIMUM
- `model: "claude-opus-4-6[1m]"` for highest quality prose
- Instruction to read `research/claims_matrix.md` for the scored claims-evidence matrix. **Adjust writing confidence based on claim strength**: STRONG claims (score >= 6) use confident language ("demonstrates", "establishes"). MODERATE claims (3-5.9) use standard academic language ("shows", "indicates"). WEAK claims (1-2.9) MUST use hedged language ("suggests", "preliminary evidence indicates") and note the limitation. CRITICAL claims (< 1) should not appear in the final text without explicit qualification.
- **Argumentation** — for each major claim in your section, ensure the paragraph contains:
  1. The **CLAIM** stated clearly
  2. **EVIDENCE** supporting it (with citations)
  3. A **WARRANT** explaining why the evidence is sufficient (the logical bridge from evidence to claim, from the Warrant column in claims_matrix.md)
  4. A **QUALIFIER** if the claim has scope limitations (from the Qualifier column)
  5. Reference to where **REBUTTALS** are addressed (if not in this section, from the Rebuttal column)

  Do NOT just cite papers and state conclusions. Explain WHY the cited evidence supports YOUR specific claim. This is the difference between a literature dump and an argument.

  The claims relevant to your section are listed in `research/claims_matrix.md` with their Warrant, Qualifier, and Rebuttal columns — use these as your argumentation scaffolding.
- **Voice & Rhetoric** — Write as a domain expert explaining to peers, not as a summarizer reporting findings. Follow these principles:
  1. **Vary paragraph openings.** Not every paragraph starts with a topic sentence. Sometimes lead with evidence, then interpret. Sometimes open with a question, then answer it. Sometimes start with a counterargument, then rebut. If you catch yourself writing 3+ consecutive paragraphs with the same structure (claim → evidence → interpretation), restructure at least one.
  2. **Embed evidence naturally.** Instead of always "Author (Year) showed X. This demonstrates Y." — try embedding: "The 37% improvement observed on BLEU scores (Author, Year) suggests that...". Integrate citations into the flow of argument rather than front-loading them.
  3. **Be concrete over abstract.** "37% improvement on BLEU" not "significant improvement." "Three of seven datasets" not "several datasets." "Published between 2022 and 2025" not "recent work." If you can replace a vague word with a specific number, name, or date, do it.
  4. **Vary sentence length.** Mix long analytical sentences (20-30 words, developing complex ideas) with short direct ones (5-10 words, delivering verdicts or transitions). Three consecutive sentences of similar length creates monotony.
  5. **One hedge per clause.** "May suggest" is fine. "May potentially suggest that it could be argued" is not. If a claim needs heavy hedging, the evidence is too weak — either find stronger evidence or cut the claim.
  6. **Read the literature synthesis.** If `research/literature_synthesis.md` exists (from Stage 1f), use it to understand where the field agrees and disagrees. Engage with conflicts, don't paper over them. Position your contribution relative to competing frameworks, not in a vacuum.
- **Knowledge graph queries** (run if `research/knowledge/` exists — if not, log `"⚠ Knowledge graph not available — applying compensating checks per Knowledge Graph Availability Protocol"` and follow the compensation instructions after the query blocks below). Run section-specific queries BEFORE writing and pass results as a `## Knowledge Graph Context` section in the agent prompt (capped at 500 words, summarize rather than dumping raw results):

  **For Introduction**:
  ```bash
  python scripts/knowledge.py query "What is the current state of [topic] and what problems remain?"
  python scripts/knowledge.py relationships "[main method/concept]"
  ```

  **For Related Work**:
  ```bash
  python scripts/knowledge.py entities  # identify all methods/approaches to organize thematically
  python scripts/knowledge.py relationships "[each major approach]"  # find connections between approaches
  ```

  **For Methods/Approach**:
  ```bash
  python scripts/knowledge.py evidence-for "[proposed method is valid because...]"
  python scripts/knowledge.py query "What are known limitations of [method components]?"
  ```

  **For Results/Discussion**:
  ```bash
  python scripts/knowledge.py evidence-for "[each key finding]"
  python scripts/knowledge.py evidence-against "[each key finding]"
  python scripts/knowledge.py contradictions
  ```

  **For all other sections** (Conclusion, Abstract): no additional graph queries needed — they synthesize existing content.

  **If the knowledge graph is NOT available**: Instead of graph queries, add this to each writing agent prompt:
  ```
  ## Evidence Compensation (Knowledge Graph Unavailable)
  The knowledge graph is not available for cross-source evidence queries. You must:
  1. Before writing each claim, re-read the specific source extracts cited in the claims matrix to verify the evidence actually supports the claim as stated
  2. For Results/Discussion: manually check whether any source extract contradicts your findings — read at least the 5 most relevant sources and note any tensions
  3. Use more conservative language for claims flagged as "KG-unverified" in the claims matrix
  4. If you discover a contradiction between sources while writing, flag it explicitly in the text rather than silently choosing one side
  ```
- Provenance logging instructions: after writing each paragraph, append a provenance entry to `research/provenance.jsonl` recording: the paragraph target (`[section]/p[N]`), which source extracts informed it (`sources`), which claims it supports (`claims`), and a `reasoning` field explaining the writing choices (why this argument structure, why these citations, why this depth). Use action `write` and `iteration: 0`.
- **LaTeX Conventions** (see shared-protocols.md § LaTeX Conventions Protocol):
  - Float placement: `[htbp]` always. Place float environment *before* its first text reference. Caption below figures, above tables.
  - Cross-refs: Use `\cref{}` if cleveref is loaded (check `.venue.json` packages), otherwise `Figure~\ref{}`. Always `\label{}` after `\caption{}`.
  - Non-breaking spaces: `~` before `\citep`, `\citet`, `\cite`, `\ref`, `\cref`, `\eqref` and after abbreviations (e.g.,~ i.e.,~ Fig.~ Eq.~).
  - Math: `\[...\]` not `$$`, `align` not `eqnarray`, punctuate equations, use `\mathrm{}` for multi-letter names.
  - Numbers with units: use `\qty{}{}` and `\num{}` from siunitx.
  - Tables: booktabs only (`\toprule/\midrule/\bottomrule`), no vertical lines, `@{}` at edges.
  - Check `forbidden_packages` from `.venue.json` before adding any `\usepackage`.

**Section writing order and targets:**

| Order | Section | Guidance | Key instruction |
|-|-|-|-|
| 1 | Introduction | Comprehensive | Broad context → specific problem → contribution → findings preview → paper organization. Cite 8-12 works. Write until the reader fully understands the problem and why this work matters. |
| 2 | Related Work | Thorough | Organize THEMATICALLY in 3-5 subsections. Discuss 3-5 papers per theme. Position this work explicitly. Cite 15-20 works. Cover the field completely — don't leave gaps a reviewer would notice. |
| 3 | Methods/Approach | Exhaustive | Full detail for reproduction. Math in equation/align environments. Pseudocode if applicable. Design rationale. Use `sympy` skill for formulations if appropriate. Another researcher should be able to reproduce this from your description alone. **ASSUMPTIONS** — Read `research/assumptions.md`. For each assumption categorized as REASONABLE, RISKY, or CRITICAL: (1) state it explicitly at the point where it's introduced, (2) for RISKY and CRITICAL: briefly justify why it's appropriate (cite prior art if available), (3) forward-reference the Discussion/Limitations section for detailed analysis of RISKY and CRITICAL assumptions. Do NOT bury assumptions — state them near the methodological choice they relate to. A reviewer should be able to find every assumption by reading Methods. |
| 4 | Results/Experiments | Data-driven | Setup → quantitative results (tables) → ablations → qualitative analysis. At least 2 booktabs tables. Use `statistical-analysis` skill, `matplotlib` or `scientific-visualization` skill for figures. Present all results needed to support your claims. |
| 5 | Discussion | Reflective | Interpret findings → compare with prior work → limitations (be honest) → broader implications → future work. Use `scientific-critical-thinking` skill. Be thorough on limitations — reviewers respect honesty. **ASSUMPTIONS** — Read `research/assumptions.md`. The Limitations subsection MUST address: (1) every CRITICAL assumption: what happens if it doesn't hold, how bounded is the impact, (2) every RISKY assumption: evidence for and against, alternative approaches if assumption fails, (3) group assumptions by theme (data, model, evaluation) for readability. Frame limitations honestly but constructively — "We acknowledge X; however, prior work [cite] demonstrates Y, suggesting this assumption is reasonable in the context of Z." |
| 6 | Conclusion | Concise | Restate problem → summarize approach → highlight key results (with numbers) → impact statement. No new information. Brief and impactful. |
| 7 | Abstract | Self-contained | Written LAST. Specific quantitative claims. Read the ENTIRE paper first. Must stand alone — a reader should understand the full contribution from the abstract. Unless `abstract_strategy` is explicitly `"last"`, this replaces the draft abstract from `research/draft_abstract.md` — compare against it to ensure nothing promised was dropped. |

**Provenance for each section**: After completing each section, the writing agent must have appended at least one provenance entry per paragraph. If a paragraph draws from multiple sources, list all of them. The `reasoning` field should explain the paragraph's role in the argument (e.g., "Sets up the gap in prior work by contrasting smith2024's approach with jones2023's limitations, motivating our contribution").

**Codex-Authored Limitations Draft**

After the Discussion section is written (Order 5), have Codex draft the Limitations subsection. Codex brings a genuinely different perspective on weaknesses — this is where adversarial thinking is most valuable.

```
mcp__codex-bridge__codex_review({
  prompt: "Read this research paper's Methods and Results sections. Write a thorough Limitations subsection (as LaTeX) covering: (1) Methodological limitations — what assumptions might not hold? (2) Data/evaluation limitations — are the benchmarks sufficient? Could results look different on other data? (3) Scope limitations — what does this NOT address? (4) Threats to validity — what could invalidate the conclusions? Be honest but fair — the goal is to preempt reviewer criticism, not sabotage the paper. Write in academic prose, not bullet points.",
  context: "[paste Methods and Results sections from main.tex]",
  evidence_mode: true
})
```

Apply the **Codex Deliberation Protocol**: evaluate Codex's limitations. You may push back if Codex overstates weaknesses or misunderstands the method. Then have the Discussion writing agent (model: claude-opus-4-6[1m]) integrate the agreed-upon limitations into the Discussion section's limitations subsection, blending them with Claude's own identified limitations.

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"3","tool":"codex_review","purpose":"limitations draft","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"reviews/codex_deliberation_log.md","resolution_summary":"[one-line]"}
```

**After each writing agent completes**, assess whether the section is substantively complete. If the section feels thin — missing depth, lacking citations, skipping over important points, or leaving obvious gaps — spawn an expansion agent:
```
The [SECTION] section in main.tex needs more depth.
Read main.tex. Invoke the `scientific-writing` skill.
EXPAND the section by adding depth, subsections, citations, analysis, and formal detail.
Do NOT delete existing content. Only ADD substantive content — not filler.
Write until the section is comprehensive. A domain expert should not feel anything important was left unsaid.
Edit main.tex directly.
PROVENANCE — For each paragraph you add, append a provenance entry to research/provenance.jsonl with action "expand", the paragraph target, reasoning for why this content was needed, and sources used. Set iteration to 0.
```

**After each section completes**, call Codex for a spot-check. This applies to ALL sections: Introduction, Related Work, Methods, Results, Discussion, Conclusion, and Abstract.

```
mcp__codex-bridge__codex_review({
  prompt: "Quick review of the [SECTION] section of a research paper. Check: (1) Are the claims proportionate to the evidence presented? (2) Is the logic sound — does each paragraph follow from the previous? (3) Are there any obvious gaps a reviewer would flag? (4) Is the technical depth appropriate? Keep your review focused and concise — this is a section check, not a full paper review.",
  context: "[paste the section content from main.tex]",
  evidence_mode: true
})
```

Write each spot-check to `reviews/codex_section_[SECTION].md` (e.g., `reviews/codex_section_introduction.md`). If Codex finds CRITICAL issues, fix them in main.tex before moving to the next section. MAJOR issues can wait for Stage 5.

**Codex Telemetry** — After each per-section spot-check, append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"3","tool":"codex_review","purpose":"spot-check [SECTION]","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"reviews/codex_section_[SECTION].md","resolution_summary":"[one-line]"}
```

**[DEEP] Codex-Assisted Expansion**

If depth is `"deep"`, after the spot-check, also call Codex to identify content gaps:

```
mcp__codex-bridge__codex_ask({
  prompt: "You are a domain expert reviewing the [SECTION] section. What substantive content is MISSING that a knowledgeable reviewer would expect to see? Don't focus on writing quality — focus on intellectual completeness. What arguments, evidence, comparisons, or nuances are absent? Be specific.",
  context: "[paste the section content from main.tex]"
})
```

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"3","tool":"codex_ask","purpose":"content gap identification [SECTION]","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"reviews/codex_deliberation_log.md","resolution_summary":"[one-line]"}
```

If Codex identifies substantive gaps, spawn an **expansion agent** (model: claude-opus-4-6[1m]) to address them:
```
Read main.tex. The [SECTION] section has been reviewed and these content gaps were identified:
[paste Codex response]

Address each gap by adding substantive content — new paragraphs, additional citations from references.bib, deeper analysis. Do NOT pad with filler. Only add content that addresses the identified gaps.
Invoke the `scientific-writing` skill.
Edit main.tex directly.
```

**Evidence Check Loop**

After ALL post-section steps above (expansion, spot-check, [DEEP] Codex expansion), run an evidence check before moving to the next section. This catches under-supported claims while the section is fresh.

**Step 1: Evidence Check** — Spawn a fast agent (model: `claude-sonnet-4-6[1m]`) to cross-reference the just-written section against the evidence base:

```
You are an evidence gap detector. Read the [SECTION] section that was just written in main.tex.
Also read research/claims_matrix.md and the source extracts in research/sources/.

For each claim or factual statement in this section:
1. Is it supported by a citation? If not, flag it.
2. If cited, does the source extract for that citation actually contain content supporting this specific claim? (Check research/sources/<key>.md)
3. Are there claims that go BEYOND what the source extract says? (e.g., claiming "X shows that..." when the source extract only contains an abstract)
4. **WARRANT CHECK**: For each major claim (those in research/claims_matrix.md), does the paragraph contain an explicit WARRANT — a sentence explaining WHY the cited evidence supports this specific claim? A paragraph that cites three papers but never explains the logical connection between those citations and the claim is a "citation dump." Flag missing warrants.

Output a list of evidence gaps:
- GAP: [section/paragraph] — [claim text] — [what's missing: citation needed / source is abstract-only / claim exceeds source content / missing_warrant]
- OK: [section/paragraph] — [claim text] — [supported by: key (access level), warrant: present/absent]

**Missing warrants count as evidence gaps** for the micro-research trigger threshold. Unlike citation gaps (which need new sources), warrant gaps need the writing agent to articulate WHY the evidence matters — this is a revision task, not a research task. When the patch step (Step 4) runs, warrant gaps trigger a quick edit agent to add the logical bridge, not a research agent.

Write to reviews/evidence_gaps_[SECTION].md
```

If the knowledge graph is available (`research/knowledge/` exists), the evidence check agent also queries it before flagging gaps:

```bash
python scripts/knowledge.py evidence-for "[claim from gap]"
```

Sometimes the evidence exists in the graph (from a source the writing agent didn't think to cite) and no new research is needed — just add the citation.

**Step 2: Decision Gate** — Based on gaps found:

| Gaps found | Action |
|-|-|
| 0 gaps | Proceed to next section immediately |
| 1-2 gaps, minor (missing citation for well-known fact) | Note for QA. Proceed. |
| 3+ gaps OR any gap where claim exceeds source content | Trigger micro-research before next section |

**Depth mode override**: In `"deep"` mode, the threshold drops to 1+ gap triggering micro-research.

**Step 3: Micro-Research** (when triggered) — Spawn a targeted agent (model: `claude-sonnet-4-6[1m]`) to fill exactly the identified gaps:

```
You are a targeted research agent filling evidence gaps found during writing.
TOPIC: [TOPIC]
TOOL FALLBACK: [standard chain from shared-protocols.md]

Fill these specific gaps:
[paste gap list from reviews/evidence_gaps_[SECTION].md]

For each gap:
1. Search for a paper that directly supports the claim
2. If found: add to references.bib, create source extract in research/sources/, note the BibTeX key
3. If NOT found: report that the claim may need to be hedged or removed

Budget: maximum 2 search queries per gap (4 in deep mode). Be precise.
Write findings to research/section_gaps_[SECTION].md.
Add new references to references.bib.
RESEARCH LOG: Append entries to research/log.md.
```

Micro-research runs **at most once per section**. If gaps remain after research, they're deferred to Stage 5 QA.

**[DEEP] Post-Micro-Research Verification**: In `"deep"` mode, after micro-research completes, re-run the evidence check (Step 1) to verify gaps were filled. Do NOT trigger a second round of micro-research — this is verification only.

**Step 4: Patch** — After micro-research:
1. If new citations were found for the just-written section, spawn a quick edit agent (model: `claude-sonnet-4-6[1m]`) to add the citations to main.tex in the appropriate locations.
2. The NEXT section's writing agent prompt must include: `Also read research/section_gaps_[PREVIOUS_SECTION].md for references discovered during evidence checking of the previous section.`

**Sections that skip micro-research**: Conclusion and Abstract do not trigger micro-research (they summarize existing content, not introduce new claims). The evidence check still runs on Conclusion to catch any unsupported summary claims, but gaps are deferred to QA.

**Depth mode summary:**

| Setting | Standard | Deep |
|-|-|-|
| Evidence check | After every section | After every section |
| Gap threshold for micro-research | 3+ gaps | 1+ gap |
| Max search queries per gap | 2 | 4 |
| Re-check after micro-research | No | Yes (verify only) |

**Pipeline flow with evidence check:**

```
Write Intro → [Expansion/Spot-check] → Evidence Check → [Micro-Research if needed] →
Write Related Work → [Expansion/Spot-check] → Evidence Check → [Micro-Research if needed] →
Write Methods → [Expansion/Spot-check] → Evidence Check → [Micro-Research if needed] →
Write Results → [Expansion/Spot-check] → Evidence Check → [Micro-Research if needed] →
Write Discussion → [Expansion/Spot-check] → Evidence Check → [Micro-Research if needed] →
Write Conclusion → [Expansion/Spot-check] → Evidence Check (no micro-research) →
Write Abstract
```

**State tracking** — After each section's evidence check, update `.paper-state.json` under the writing stage:

```json
"writing": {
  "sections": {
    "introduction": { "done": true, "words": 1250, "evidence_gaps": 1, "micro_research": false },
    "related_work": { "done": true, "words": 2100, "evidence_gaps": 4, "micro_research": true, "new_refs": 3 },
    "methods": { "done": true, "words": 1800, "evidence_gaps": 0, "micro_research": false }
  }
}
```

Record `evidence_gaps` (count from evidence check), `micro_research` (whether it triggered), and `new_refs` (count of references added by micro-research, if any).

**Partial resume**: Update `.paper-state.json` after each section completes AND after each sub-step (expansion, spot_check, evidence_check, micro_research, patch). Set the section's `current_substep` field to track progress within a section. The sub-step order is: `"write"` → `"expansion"` → `"spot_check"` → `"evidence_check"` → `"micro_research"` → `"patch"`. On resume, if a section's `done` is false but `current_substep` is set, skip completed sub-steps and resume from the recorded sub-step. When a section fully completes, set `done: true` and `current_substep: null`. Also set `writing.current_substep` at the stage level to the currently active sub-step for quick status visibility.

---
