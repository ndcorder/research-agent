# Auto Phase 3: Execution

> **Prerequisites**: Read `pipeline/shared-protocols.md` first. Use its Provenance Logging Protocol, Tool Fallback Chain, and Research Log format throughout this phase.

---

## Phase 3: Execute

### Research phase (if needed, max 3 queries)

If any selected action requires new evidence, spawn a targeted research agent (model: claude-sonnet-4-6[1m]):
```
You are a targeted research agent for iteration [N] of paper improvement.
TOPIC: [TOPIC]
DOMAIN: [DOMAIN]
TOOL FALLBACK: domain databases → Perplexity → WebSearch → Firecrawl → research-lookup. Try at least 3 tools.

Search for SPECIFIC evidence to support these improvements:
[paste only the actions that need research]

You have a budget of 3 searches maximum. Be precise — we know exactly what we need.
Write findings to research/auto_iter[N]_research.md.
Add any new references to references.bib.
RESEARCH LOG: Append entries to research/log.md.
Create source extracts in research/sources/ for any new papers.
```

**After the research agent completes** (if it ran and added new source extracts or references), rebuild the knowledge graph incrementally:
```bash
python scripts/knowledge.py update
```
**Run with `run_in_background: true`** — incremental updates can take several minutes. You will be notified when it completes. If `research/knowledge/` does not exist, log `"⚠ Knowledge graph not available — skipping update"` and continue.

### Revision phase

Spawn a revision agent (model: claude-opus-4-6[1m]):
```
You are improving a research paper in iteration [N] of autonomous improvement.
Invoke the `scientific-writing` skill.
Read main.tex, references.bib, and the action plan at reviews/auto_iter[N]_plan.md.
[If research was done: Also read research/auto_iter[N]_research.md]

Execute EVERY action in the plan. For each action:
1. Make the change in main.tex (and references.bib if needed)
2. For CUTS: save removed text to provenance/cuts/[section]-[pN]-auto[N].tex BEFORE deleting
3. Maintain consistency with surrounding text — update transitions, cross-references

Writing rules:
- No em dashes (—) or en dashes (–) as punctuation. Use commas, parentheses, colons, or separate sentences.
- No AI writing patterns (delve, tapestry, realm, multifaceted, furthermore/moreover at sentence starts)
- Full paragraphs only, flowing academic prose
- Do NOT add filler to compensate for cuts — if you remove a paragraph, the surrounding text should still flow

After all changes, compile: latexmk -pdf -interaction=nonstopmode main.tex
Fix any LaTeX errors.

PROVENANCE — After EACH change, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"auto","agent":"auto-revision","action":"[revise|cut|add|expand|reorder]","target":"[section/pN]","reasoning":"[why — reference the action plan item]","feedback_ref":"reviews/auto_iter[N]_plan.md#action-[M]","diff_summary":"[what changed]","sources":["keys"],"iteration":[N]}
For cuts: set archived_to to the path where you saved the removed text.
```
