# Stage 1: Deep Literature Research

> **Prerequisites**: Read `pipeline/shared-protocols.md` first. Use its Tool Fallback Chain, Research Log format, Source Extract format, and Provenance Logging Protocol in every agent prompt below.

---

**Shared Knowledge Base Check**

Before starting research, check if a shared knowledge base exists at `~/.research-agent/shared-sources/`. If it exists:

1. Scan the shared sources for relevance to this paper's topic (from `.paper.json`)
2. Count relevant sources (read titles and key findings, assess topical overlap)
3. If relevant sources found, report to the user: "Found [N] source extracts from previous papers on related topics. Run `/import-sources` to pre-populate your bibliography."
4. Do NOT auto-import — let the user decide. The check is informational only.

If the shared directory does not exist, skip this check silently.

---

**Goal**: Comprehensive field understanding + 30-50 verified references in `references.bib`.

Spawn **4-5 research agents in parallel**. Each agent must be told to invoke the relevant skills for the detected domain. Each writes to a separate file.

**IMPORTANT — Shared Protocol Blocks**: The orchestrator reads `pipeline/shared-protocols.md` at startup. Include the following blocks from that file in EVERY research agent prompt below:
- **Tool Fallback Chain** (includes Research Log format)
- **Provenance Logging Protocol** (abbreviated form for research agents — action: "research")
- **Source Extract Format**

Do NOT paraphrase these blocks — paste the actual text from shared-protocols.md into each agent prompt so agents get complete, consistent instructions.

**Agent 1 — "Field Survey"** (model: claude-sonnet-4-6[1m])
```
You are a research scientist conducting a literature survey.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

IMPORTANT: You have access to scientific skills. Invoke these skills to guide your search:
- Use the `literature-review` skill for systematic search methodology
- Use the `research-lookup` skill for finding papers
- Search using ALL available tools: Perplexity (mcp__perplexity__search, mcp__perplexity__reason), web search, any database MCP tools
- Use domain-specific database skills: [LIST DOMAIN_SKILLS databases here]

TOOL FALLBACK: If any tool fails, try the next: domain databases → Perplexity → WebSearch → Firecrawl → research-lookup. Try at least 3 tools.

Your task:
1. Identify the 10-15 most influential papers in this field
2. Map major research threads and schools of thought
3. Note recent breakthroughs (2023-2026) and active debates
4. Identify the top researchers and groups working on this

Write a 2000+ word comprehensive survey to research/survey.md.
For EVERY paper mentioned, include: authors, title, venue, year, DOI (if findable).
Do NOT fabricate any references.
RESEARCH LOG: After every search or tool call, append an entry to research/log.md with: timestamp, tool name, query, result summary, and URLs/DOIs found. Use the format specified in the TOOL FALLBACK instructions above.
```

**Agent 2 — "Methodology Deep Dive"** (model: claude-sonnet-4-6[1m])
```
You are a research methodologist analyzing approaches for: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

Use these skills to guide your work:
- `research-lookup` for finding methodology papers
- Domain-specific skills: [LIST relevant methodology skills, e.g., scikit-learn, transformers, rdkit, scanpy]
- `statistical-analysis` for understanding evaluation methodologies
- Search all available databases and tools
TOOL FALLBACK: If any tool fails, try the next: domain databases → Perplexity → WebSearch → Firecrawl → research-lookup. Try at least 3 tools.

Your task:
1. Catalog the major methodological approaches (at least 5 distinct methods)
2. For each: describe the approach, mathematical formulation, strengths, limitations, typical use cases
3. Identify which methods are state-of-the-art and why
4. Note standard benchmarks, datasets, and evaluation protocols

Write a 1500+ word analysis to research/methods.md.
Full citation details for every paper. Do NOT fabricate references.
RESEARCH LOG: After every search or tool call, append an entry to research/log.md with: timestamp, tool name, query, result summary, and URLs/DOIs found. Use the format specified in the TOOL FALLBACK instructions above.
```

**Agent 3 — "Empirical Evidence & Benchmarks"** (model: claude-sonnet-4-6[1m])
```
You are a data scientist compiling empirical evidence for: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

Use these skills:
- `exploratory-data-analysis` for understanding data types in this field
- Domain-specific database skills: [LIST from DOMAIN_SKILLS]
- `research-lookup` and any available search tools
TOOL FALLBACK: If any tool fails, try the next: domain databases → Perplexity → WebSearch → Firecrawl → research-lookup. Try at least 3 tools.

Your task:
1. Find standard benchmarks and datasets used in this field
2. Compile state-of-the-art results (leaderboard-style where applicable)
3. Identify key experimental findings and their significance
4. Note reproducibility concerns or conflicting results

Write a 1500+ word analysis to research/empirical.md.
Include specific performance numbers where available.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: After every search or tool call, append an entry to research/log.md with: timestamp, tool name, query, result summary, and URLs/DOIs found. Use the format specified in the TOOL FALLBACK instructions above.
```

**Agent 4 — "Theoretical Foundations"** (model: claude-sonnet-4-6[1m])
```
You are a theoretical researcher analyzing foundations of: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

Use these skills where relevant:
- `sympy` for mathematical formulations
- Domain theory skills from: [LIST from DOMAIN_SKILLS]
- `scientific-critical-thinking` for evaluating theoretical claims
TOOL FALLBACK: If any tool fails, try the next: domain databases → Perplexity → WebSearch → Firecrawl. Try at least 3 tools.

Your task:
1. Identify foundational theories and frameworks underlying this field
2. Document formal definitions, key theorems, and important proofs
3. Map connections to broader theoretical frameworks
4. Note open theoretical questions

Write a 1200+ word analysis to research/theory.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: After every search or tool call, append an entry to research/log.md with: timestamp, tool name, query, result summary, and URLs/DOIs found. Use the format specified in the TOOL FALLBACK instructions above.
```

**Agent 5 — "Gap Analysis & Positioning"** (model: claude-opus-4-6[1m])
```
You are a senior researcher identifying research gaps for: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

Use these skills:
- `scientific-brainstorming` for identifying novel angles
- `hypothesis-generation` for formulating testable propositions
- `scientific-critical-thinking` for evaluating gaps

Read ALL existing files in research/ directory first (survey.md, methods.md, empirical.md, theory.md).
Then analyze:
1. What specific problems remain unsolved?
2. What limitations of current approaches are most impactful?
3. What novel combinations or approaches haven't been tried?
4. What is the most promising direction for a new contribution?
5. Propose a clear thesis and contribution statement for this paper

Write a 1000+ word gap analysis to research/gaps.md.
This will directly inform the paper's contribution statement.
RESEARCH LOG: After every search or tool call, append an entry to research/log.md with: timestamp, tool name, query, result summary, and URLs/DOIs found. Use the format specified in the TOOL FALLBACK instructions above.
```

**[DEEP] Agents 6-12 — Additional Specialized Research** (model: claude-sonnet-4-6[1m])

If `depth` is `"deep"`, spawn 7 additional research agents IN PARALLEL alongside agents 1-4. Each gets the same TOOL FALLBACK, RESEARCH LOG, and SOURCE EXTRACTS instructions as agents 1-5.

**Agent 6 — "Recent Frontiers (2024-2026)"** (model: claude-sonnet-4-6[1m])
```
You are a research scientist focused exclusively on the MOST RECENT work.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Search ONLY for papers published 2024-2026
2. Identify emerging trends, new methods, and paradigm shifts in the last 2 years
3. Note any papers that challenge established findings from earlier work
4. Identify preprints and work-in-progress that hasn't been peer-reviewed yet

Write to research/recent_frontiers.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 7 — "Negative Results & Failed Approaches"** (model: claude-sonnet-4-6[1m])
```
You are a research scientist studying what DIDN'T work.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Find papers reporting negative results, null findings, or failed approaches
2. Document approaches that were tried and abandoned — and WHY
3. Identify common pitfalls and known failure modes
4. Note any replication failures or controversial findings

Write to research/negative_results.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 8 — "Cross-Disciplinary Insights"** (model: claude-sonnet-4-6[1m])
```
You are a cross-disciplinary researcher looking for insights from ADJACENT fields.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Identify related techniques or approaches from other fields that could apply
2. Find analogous problems solved in different domains
3. Note any interdisciplinary collaborations or hybrid methods
4. Look for theoretical frameworks from other fields that might provide insight

Write to research/cross_disciplinary.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 9 — "Datasets, Benchmarks & Reproducibility"** (model: claude-sonnet-4-6[1m])
```
You are a research engineer focused on data and reproducibility.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Catalog ALL standard datasets and benchmarks used in this field
2. Document data availability, licensing, and access methods
3. Find open-source implementations and code repositories
4. Note reproducibility studies — which results have been independently verified?
5. Identify gaps in available data or benchmarks

Write to research/datasets_reproducibility.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 10 — "Industry & Applied Work"** (model: claude-sonnet-4-6[1m])
```
You are a research analyst tracking industry and applied implementations.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Find industry applications, deployed systems, and commercial use of these methods
2. Identify patents, technical reports, and white papers from companies
3. Note the gap between academic benchmarks and real-world performance
4. Document any industry-specific constraints or requirements

Write to research/industry_applied.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 11 — "Competing Hypotheses & Debates"** (model: claude-sonnet-4-6[1m])
```
You are a research scientist mapping the intellectual landscape of active debates.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Identify active scientific debates and competing hypotheses
2. Map the different "camps" or schools of thought and their key proponents
3. Document the strongest arguments on each side
4. Note any emerging consensus or unresolved tensions

Write to research/competing_hypotheses.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 12 — "Intellectual Lineage"** (model: claude-sonnet-4-6[1m])
```
You are a research historian tracing the intellectual roots of this field.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]
TOOL FALLBACK: [same chain as above]

Your task:
1. Identify the 5-10 most foundational papers that shaped this field
2. Trace how ideas evolved from those seminal works to current approaches
3. Map the citation lineage — which breakthroughs enabled which subsequent work?
4. Identify any paradigm shifts and what caused them

Write to research/intellectual_lineage.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**In standard mode**, run agents 1-4 in parallel. Run agent 5 AFTER 1-4 complete.
**In deep mode**, run agents 1-4 AND 6-12 in parallel. Run agent 5 AFTER ALL complete (it reads all research files, including the 7 deep-mode files).

**Codex Independent Literature Contribution**

After all Claude research agents complete but BEFORE the bibliography builder, call Codex to contribute its own research findings. Different models have different training data — Codex may know papers Claude doesn't.

```
mcp__codex-bridge__codex_ask({
  prompt: "You are an independent research contributor. The topic is: [TOPIC]. I have already gathered research on this topic. Now I need YOU to independently suggest papers and findings that I might have missed. Focus on: (1) Papers from the last 2 years that are highly relevant (2) Seminal older papers that are commonly cited but might be overlooked (3) Papers from adjacent fields that offer useful insights (4) Any well-known datasets or benchmarks I should reference. For each paper, provide: authors, title, venue, year, and a 1-2 sentence summary of relevance. Do NOT just confirm what I already found — add NEW information.",
  context: "[paste a brief summary of what the research agents found — topic areas covered, key papers already identified]"
})
```

Write Codex's contributions to `research/codex_independent_research.md`. Apply the **Codex Deliberation Protocol**: verify Codex's paper suggestions are real (search to confirm), push back on any that seem fabricated, and add verified ones to the research notes. Pass all verified new papers to the bibliography builder.

**After all research agents complete, spawn a Bibliography Builder agent** (model: claude-sonnet-4-6[1m])**:**
```
You are a meticulous bibliographer.
Read ALL files in research/ directory. Extract every paper cited.

Use the `citation-management` skill for proper BibTeX formatting.

For each paper:
1. Search to VERIFY it is a real publication (use Perplexity, web search, or domain databases)
2. Find complete metadata: all authors, full title, journal/conference, volume, number, pages, year, DOI
3. Generate BibTeX entry with key format: firstauthorlastnameYear
4. Use correct entry type (@article, @inproceedings, @book, @misc, @phdthesis)

Write all verified entries to references.bib organized by theme (add % comment headers).
Remove duplicates. Target: 30-50 references minimum.

CRITICAL: Do NOT fabricate or guess references. If you cannot verify a paper, omit it.
After writing references.bib, count the entries and report the total.
RESEARCH LOG: For every verification search, append an entry to research/log.md recording: the paper being verified, tool used, query, and result (VERIFIED/SUSPICIOUS/FABRICATED). Include the verification URL or DOI.
```

**Partial resume**: After EACH research agent completes, update `.paper-state.json` to add the agent name to `stages.research.agents_completed` and remove it from `stages.research.agents_pending`. This enables resume if the session is interrupted mid-stage. Use the agent's short name: `"survey"`, `"methods"`, `"empirical"`, `"theory"`, `"gaps"`, and for deep mode: `"recent_frontiers"`, `"negative_results"`, `"cross_disciplinary"`, `"datasets_reproducibility"`, `"industry_applied"`, `"competing_hypotheses"`, `"intellectual_lineage"`. Also update `stages.research.notes` with a running count (e.g., `"3/5 agents done"`). On resume, the orchestrator will only spawn agents not in `agents_completed` (after verifying their output files exist and have content).

**Checkpoint**: Count entries in `references.bib`. In standard mode, if fewer than 25 — or in deep mode, if fewer than 50 — report which research areas are underrepresented and spawn additional targeted research agents for those areas.
