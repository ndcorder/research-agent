# Stage 3: Section-by-Section Writing

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol, Tool Fallback Chain, and Codex Deliberation Protocol.

---

Each section gets its own dedicated agent. **Run sequentially** — each section builds on prior ones.

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
- Instruction to invoke the `scientific-writing` skill for prose quality
- The specific word count target as a MINIMUM
- `model: "claude-opus-4-6[1m]"` for highest quality prose
- Instruction to read `research/claims_matrix.md` for the scored claims-evidence matrix. **Adjust writing confidence based on claim strength**: STRONG claims (score >= 6) use confident language ("demonstrates", "establishes"). MODERATE claims (3-5.9) use standard academic language ("shows", "indicates"). WEAK claims (1-2.9) MUST use hedged language ("suggests", "preliminary evidence indicates") and note the limitation. CRITICAL claims (< 1) should not appear in the final text without explicit qualification.
- If `research/knowledge/` exists, instruction to query the knowledge graph for section-specific evidence:
  `python scripts/knowledge.py query "question relevant to this section"` — use this to find specific evidence, check for contradictions, and ensure comprehensive coverage.
- Provenance logging instructions: after writing each paragraph, append a provenance entry to `research/provenance.jsonl` recording: the paragraph target (`[section]/p[N]`), which source extracts informed it (`sources`), which claims it supports (`claims`), and a `reasoning` field explaining the writing choices (why this argument structure, why these citations, why this depth). Use action `write` and `iteration: 0`.

**Section writing order and targets:**

| Order | Section | Guidance | Key instruction |
|-|-|-|-|
| 1 | Introduction | Comprehensive | Broad context → specific problem → contribution → findings preview → paper organization. Cite 8-12 works. Write until the reader fully understands the problem and why this work matters. |
| 2 | Related Work | Thorough | Organize THEMATICALLY in 3-5 subsections. Discuss 3-5 papers per theme. Position this work explicitly. Cite 15-20 works. Cover the field completely — don't leave gaps a reviewer would notice. |
| 3 | Methods/Approach | Exhaustive | Full detail for reproduction. Math in equation/align environments. Pseudocode if applicable. Design rationale. Use `sympy` skill for formulations if appropriate. Another researcher should be able to reproduce this from your description alone. |
| 4 | Results/Experiments | Data-driven | Setup → quantitative results (tables) → ablations → qualitative analysis. At least 2 booktabs tables. Use `statistical-analysis` skill, `matplotlib` or `scientific-visualization` skill for figures. Present all results needed to support your claims. |
| 5 | Discussion | Reflective | Interpret findings → compare with prior work → limitations (be honest) → broader implications → future work. Use `scientific-critical-thinking` skill. Be thorough on limitations — reviewers respect honesty. |
| 6 | Conclusion | Concise | Restate problem → summarize approach → highlight key results (with numbers) → impact statement. No new information. Brief and impactful. |
| 7 | Abstract | Self-contained | Written LAST. Specific quantitative claims. Read the ENTIRE paper first. Must stand alone — a reader should understand the full contribution from the abstract. |

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

**[DEEP] Codex-Assisted Expansion**

If depth is `"deep"`, after the spot-check, also call Codex to identify content gaps:

```
mcp__codex-bridge__codex_ask({
  prompt: "You are a domain expert reviewing the [SECTION] section. What substantive content is MISSING that a knowledgeable reviewer would expect to see? Don't focus on writing quality — focus on intellectual completeness. What arguments, evidence, comparisons, or nuances are absent? Be specific.",
  context: "[paste the section content from main.tex]"
})
```

If Codex identifies substantive gaps, spawn an **expansion agent** (model: claude-opus-4-6[1m]) to address them:
```
Read main.tex. The [SECTION] section has been reviewed and these content gaps were identified:
[paste Codex response]

Address each gap by adding substantive content — new paragraphs, additional citations from references.bib, deeper analysis. Do NOT pad with filler. Only add content that addresses the identified gaps.
Invoke the `scientific-writing` skill.
Edit main.tex directly.
```

---
