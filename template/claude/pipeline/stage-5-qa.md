# Stage 5: Quality Assurance Loop

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Codex Deliberation Protocol.

---

**This stage LOOPS until all quality criteria pass.** Maximum 5 iterations (or 8 if depth is `"deep"`).

#### Step 5a: Parallel Review

**Before spawning review agents**, run contradiction detection if the knowledge graph exists:
```bash
python scripts/knowledge.py contradictions
```
Read `research/knowledge_contradictions.md` and pass its content to the review agents as additional context. Contradictions should be addressed in the Discussion section or flagged for the author.

Spawn **3 review agents in parallel** (model: claude-sonnet-4-6[1m]):

**Technical Reviewer:**
```
You are a rigorous peer reviewer. Invoke the `peer-review` skill for structured evaluation.
Also invoke `scientific-critical-thinking` for evidence assessment.
Read main.tex, references.bib, and research/claims_matrix.md completely.

Evaluate:
- Claims supported by evidence or citations?
- Methodology sound and reproducible?
- Results properly analyzed with appropriate statistics?
- Limitations honestly discussed?
- Argument logically coherent Introduction → Conclusion?
- Mathematical notation defined and consistent?
- Appropriate use of domain-specific terminology?
- **Evidence density**: Check the scored claims-evidence matrix. Any WEAK (score 1-2.9) or CRITICAL (score < 1) claims that appear in the manuscript MUST use appropriately hedged language. Flag any WEAK/CRITICAL claims written with unjustified confidence as CRITICAL issues. Flag any CRITICAL claims that survived to Stage 5 without being addressed as mandatory fix items.

Write a detailed review to reviews/technical.md:
- CRITICAL issues (list with line references and specific fixes)
- MAJOR issues (list with line references and specific fixes)
- MINOR issues (list)
- Evidence density heatmap: list all claims by strength (STRONG/MODERATE/WEAK/CRITICAL) with their scores
```

**Writing Quality Reviewer:**
```
You are a scientific writing editor. Invoke the `scientific-writing` skill.
Read main.tex completely.

Check:
- Any bullet points in body text? (MUST be full paragraphs)
- Every paragraph has topic sentence, development, conclusion?
- Transitions between sections smooth and logical?
- Terminology consistent throughout (same term for same concept)?
- Tense correct (past for methods/results, present for established facts)?
- Vague words ("various", "some", "interesting", "several")?
- Passive voice overused?
- Each section meets its minimum word count?

Compute word counts per section and report them.
Write review to reviews/writing.md with specific issues and suggested rewrites.
```

**Citation & Completeness Reviewer:**
```
You are a publication readiness auditor. Invoke the `citation-management` skill.
Read main.tex and references.bib.

Verify:
- All \citep{} and \citet{} keys exist in references.bib
- Claims that need citations but lack them (flag with suggested refs)
- All references.bib entries actually cited in text (flag uncited)
- No duplicate BibTeX entries
- No TODO, TBD, FIXME, \lipsum, placeholder text
- All \ref{} cross-references resolve
- Compile: latexmk -pdf -interaction=nonstopmode main.tex — report errors/warnings

Write review to reviews/completeness.md with every issue found.
```

#### Step 5a-ii: Codex Adversarial Review

**This is a separate step. Do NOT skip it. Do NOT merge it with the agent reviews above.**

After spawning the 3 review agents, IMMEDIATELY call Codex directly in your main session (this runs in parallel while agents work):

1. Read `main.tex` completely
2. Call the Codex MCP tool:

```
mcp__codex-bridge__codex_review({
  prompt: "You are an adversarial peer reviewer. Find the weakest points in this manuscript: (1) Claims that exceed the evidence (2) Logical gaps in the argument chain (3) Methodological shortcuts (4) Missing baselines or unfair comparisons (5) Conclusions that don't follow from results. Be specific — cite sections and sentences.",
  context: "[paste the full content of main.tex]",
  evidence_mode: true
})
```

3. Write the Codex response to `reviews/codex_adversarial.md`

**Checkpoint**: Before proceeding to Step 5b, verify ALL 4 review files exist:
- `reviews/technical.md` (from agent)
- `reviews/writing.md` (from agent)
- `reviews/completeness.md` (from agent)
- `reviews/codex_adversarial.md` (from Codex call above)

If `reviews/codex_adversarial.md` is missing, you skipped the Codex review — go back and do it.

#### Step 5b: Synthesize Reviews

Read ALL files in `reviews/` including `codex_adversarial.md`. Also read `research/claims_matrix.md` for the evidence density heatmap. Build a prioritized fix list:
1. All CRITICAL issues (must fix) — including any CRITICAL-strength claims that must be removed, supported, or heavily hedged
2. All MAJOR issues (should fix) — including WEAK claims written with unjustified confidence
3. Word count shortfalls
4. Missing citations
5. Evidence density upgrades — actions that would move WEAK claims toward MODERATE (e.g., finding additional sources, strengthening evidence descriptions)

#### Step 5c: Revision Agent

Spawn a revision agent (model: claude-opus-4-6[1m]):
```
You are revising a research paper based on peer review feedback.
Invoke the `scientific-writing` skill.

Read the following review feedback and fix EVERY critical and major issue in main.tex:
[PASTE CONSOLIDATED REVIEW FINDINGS]

For each issue:
1. Locate the problem in main.tex
2. Fix it with careful edits that maintain consistency with the rest of the paper
3. If a section needs more words, add substantive content (not filler)
4. If citations are needed, find appropriate ones from references.bib
5. If new citations are needed, add verified entries to references.bib
6. If content should be REMOVED (redundant, weak, or diluting stronger arguments), cut it

After all fixes, compile: latexmk -pdf -interaction=nonstopmode main.tex
Fix any LaTeX errors.
Edit main.tex and references.bib directly.

PROVENANCE — After EACH revision, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"5","agent":"qa-revision","action":"revise|cut|add","target":"[section/pN]","reasoning":"[why — reference the specific review issue]","feedback_ref":"[reviews/file.md#issue-number]","diff_summary":"[what changed]","sources":["keys"],"iteration":0}
For cuts: save removed text to provenance/cuts/[section]-[pN]-qa[iteration].tex and set archived_to.
```

#### Step 5d: Quality Gate Check

After revision, check ALL criteria from the table below. If any fail, loop back to Step 5a with fresh reviewers. If all pass, proceed to Stage 6.

**[DEEP]** If depth is `"deep"` and this is the FINAL QA iteration (all criteria pass), run one additional Codex review before exiting:

```
mcp__codex-bridge__codex_review({
  prompt: "Final deep review of this manuscript. This paper has already passed multiple rounds of QA. Look for subtle issues that earlier reviews missed: (1) Implicit assumptions never made explicit (2) Logical leaps that seem fine on first read but don't hold up (3) Claims that are technically true but misleading (4) Missing qualifications or edge cases (5) Opportunities to strengthen the argument that were overlooked.",
  context: "[paste the full content of main.tex]",
  evidence_mode: true
})
```

Write to `reviews/codex_final_deep.md`. If this surfaces CRITICAL issues, do one more fix-and-review cycle. Otherwise, proceed.

---
