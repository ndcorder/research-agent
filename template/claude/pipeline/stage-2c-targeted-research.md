# Stage 2c: Thesis-Informed Targeted Research [DEEP]

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Tool Fallback Chain and Research Log format.

---

**Skip this stage if depth is `"standard"`.** This stage only runs in deep mode.

Now that the thesis, contribution statement, and outline are finalized, run a SECOND targeted research pass. The first pass (Stage 1) was broad. This pass is surgical — searching for literature that directly supports, challenges, or contextualizes the specific claims this paper will make.

Read `research/thesis.md` and the outline in `main.tex`. For each major claim or section, spawn a targeted research agent.

Spawn **3 agents in parallel** (model: claude-sonnet-4-6[1m]):

**Agent A — "Supporting Evidence"**
```
You are a research scientist gathering evidence to SUPPORT a specific thesis.
THESIS: [paste from research/thesis.md]
KEY CLAIMS: [list the 3-5 main claims from the thesis]
TOOL FALLBACK: [same chain as Stage 1]

Your task:
1. For EACH key claim, find 3-5 papers that provide direct supporting evidence
2. Find experimental results, datasets, or case studies that validate the approach
3. Look for meta-analyses or systematic reviews that corroborate the position
4. Ensure the evidence is strong enough to withstand peer review scrutiny

Write findings to research/targeted_support.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same format]
```

**Agent B — "Counterarguments & Rebuttals"**
```
You are a devil's advocate researcher looking for evidence AGAINST a thesis.
THESIS: [paste from research/thesis.md]
KEY CLAIMS: [list the 3-5 main claims]
TOOL FALLBACK: [same chain as Stage 1]

Your task:
1. Find papers that contradict or challenge each key claim
2. Identify the strongest counterarguments a reviewer would raise
3. Search for alternative explanations for any claimed results
4. Find evidence for competing approaches that might outperform this one

Write findings to research/targeted_counter.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same format]
```

**Agent C — "Methodological Precedents"**
```
You are a methods specialist finding precedents for the proposed approach.
PROPOSED METHOD: [paste Methods outline from main.tex]
TOOL FALLBACK: [same chain as Stage 1]

Your task:
1. Find papers that used similar methods — especially in different contexts
2. Document known limitations and failure modes of the proposed techniques
3. Find best practices, recommended parameters, and implementation guidance
4. Identify any methodological innovations that should be incorporated

Write findings to research/targeted_methods.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same format]
```

After all agents complete, run the bibliography builder again to add new references to `references.bib`.

**Update knowledge graph** — new papers from targeted research need to be incorporated. First check `.paper-state.json` `stages.knowledge_graph.available` (or check if `research/knowledge/` exists and `OPENROUTER_API_KEY` is set). If the knowledge graph is NOT available, log `"⚠ Knowledge graph not available — skipping enqueue after targeted research"` and skip this step.

If available:
```bash
python scripts/knowledge.py enqueue research/sources/*.md
python scripts/knowledge.py enqueue attachments/parsed/*.md
```
The enqueue command automatically skips files that have already been ingested and haven't changed. Only new/modified sources are queued.

**Checkpoint**: Verify targeted research files exist. Update `.paper-state.json`: mark `targeted_research` as done.
