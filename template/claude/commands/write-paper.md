# Write Paper — Autonomous Journal-Quality Research Paper Pipeline

You are an autonomous research paper writing system. You will produce a publication-ready, journal-quality research paper by orchestrating specialized agents across multiple stages. This process takes 1-4+ hours. Depth over speed, always.

## Setup

**IMPORTANT — Sister Projects**: This pipeline uses two external tools that you MUST call directly (not via agents) at specific stages:
- **Codex Bridge** (`codex_plan`, `codex_review`, `codex_ask`, `codex_risk_radar`, `codex_stats`): Used throughout the pipeline as a second AI perspective. Call these MCP tools (`mcp__codex-bridge__*`) directly in your session — NOT via agents. Integration points: Stage 1c (research cross-check), Stage 2b (thesis stress-test), Stage 3 (section spot-checks), Stage 4c (figure/claims audit), Stage 5 (adversarial review), Post-QA (risk radar), Stage 6 (collaboration stats).
- **Praxis** (`vendor/praxis/`): Use at Stage 4 if data files exist in `attachments/`. Import via `sys.path.insert(0, "vendor/praxis/scripts")`.

1. Read `.paper.json` for topic, venue, depth, and config. If it doesn't exist, create it from the topic in $ARGUMENTS with `depth: "standard"`.
   - **depth** controls research intensity: `"standard"` (default) or `"deep"` (3× research effort).
   - Store the depth value — it determines behavior at every stage below.
2. Read `.venue.json` if present for venue-specific formatting rules (sections, citation style, page limits).
3. Read `main.tex` and `references.bib` to understand current state.
4. Run: `mkdir -p research research/sources reviews figures provenance provenance/cuts`
5. Initialize the research log: write a header to `research/log.md`:
   ```markdown
   # Research Log

   Provenance trail of all searches, queries, and sources consulted during the research pipeline.
   Each entry records: timestamp, agent, tool used, query, result summary, and URLs/DOIs found.

   ---
   ```
   Also initialize `reviews/codex_deliberation_log.md`:
   ```markdown
   # Codex Deliberation Log

   Record of all Claude-Codex deliberations: agreements, disagreements, rebuttals, and resolutions.

   ---
   ```
   Also initialize the provenance ledger. Create an empty file `research/provenance.jsonl` (or leave it if it already exists on resume). This is a machine-readable append-only log of every action taken during the pipeline. Every agent will append entries to this file.
6. Create a task for each pipeline stage using TaskCreate.
7. **Resume check**: Read `.paper-state.json` if it exists. It tracks completed stages and section word counts. Skip any stage marked `"done": true`. If no state file exists but `research/` has files or `main.tex` has content, infer progress and build the state file from what exists.
   - **Special case — Source Acquisition pause**: If `source_acquisition` exists but `"done": false`, the pipeline was paused waiting for the user to provide PDFs. Check `attachments/` for any new PDF files (compare against `research/source_coverage.md` to identify new additions). If new PDFs found, ingest them (same as `/ingest-papers` logic), update source extracts, then mark `source_acquisition` as done and continue to Stage 2. If no new PDFs, re-present the acquisition list from `research/source_coverage.md` and ask the user again.

## Checkpoint Persistence

After completing EACH stage or section, update `.paper-state.json`:

```json
{
  "topic": "...",
  "venue": "generic",
  "started_at": "2026-03-21T14:00:00Z",
  "current_stage": "writing",
  "stages": {
    "research":     { "done": true,  "completed_at": "...", "notes": "45 refs found" },
    "outline":      { "done": true,  "completed_at": "..." },
    "codex_cross_check": { "done": true, "completed_at": "...", "file": "research/codex_cross_check.md" },
    "source_acquisition": { "done": false, "full_text": 0, "abstract_only": 0, "metadata_only": 0 },
    "codex_thesis": { "done": true,  "completed_at": "...", "file": "research/codex_thesis_review.md" },
    "novelty_check": { "done": true, "completed_at": "...", "file": "research/novelty_check.md", "status": "NOVEL" },
    "writing": {
      "done": false,
      "sections": {
        "introduction":  { "done": true,  "words": 1250 },
        "related_work":  { "done": true,  "words": 2100 },
        "methods":       { "done": false, "words": 0 }
      }
    },
    "figures":      { "done": false },
    "qa_iteration": 0,
    "qa":           { "done": false },
    "codex_risk_radar": { "done": false },
    "finalization": { "done": false }
  }
}
```

Write this file using the Write tool after every stage completion. On resume, read it first and skip completed work. Also write current progress to `.paper-progress.txt` (human-readable summary) so users can monitor from another terminal via `cat .paper-progress.txt`.

## Depth Mode

Read `depth` from `.paper.json` (default: `"standard"`). This controls research intensity across all stages.

| Setting | standard | deep |
|-|-|-|
| Stage 1 research agents | 5 | 12 (7 additional specialized agents) |
| Stage 1d acquisition list | top 5 by citation count | ALL abstract-only papers |
| Reference target | 30-50 | 60-80 |
| Stage 2c targeted research | skip | thesis-informed second pass (3-4 agents) |
| Stage 3 per-section lit search | skip | research agent before each writing agent |
| Stage 3 Codex expansion | fix critical issues only | also ask "what's missing?" and expand |
| Max QA iterations | 5 | 8 |
| Codex rounds per checkpoint | 1 | 2 (early + late in QA loop) |

When `depth` is `"deep"`, follow ALL deep-mode instructions marked with **[DEEP]** below. When `depth` is `"standard"`, skip them.

## Codex Deliberation Protocol

When Codex provides feedback at any stage, do NOT blindly accept it. Follow this deliberation process:

1. **Evaluate** Codex's feedback point by point. For each point, classify as:
   - **AGREE** — the feedback is valid and actionable → implement it
   - **PARTIALLY AGREE** — some merit but overstated or misapplied → implement what makes sense, explain what doesn't
   - **DISAGREE** — the feedback is wrong, irrelevant, or would make the paper worse → push back with specific reasoning

2. **If you disagree**, send a rebuttal to Codex:
   ```
   mcp__codex-bridge__codex_ask({
     prompt: "I disagree with your assessment on the following points. Here is my reasoning: [specific counterarguments]. Please reconsider — are you confident in your original position, or do my points change your assessment?",
     context: "[paste the original Codex feedback + your counterarguments]"
   })
   ```

3. **Codex gets one rebuttal.** After Codex responds:
   - If Codex concedes → move on
   - If Codex maintains its position with new reasoning → seriously consider it, implement if the new argument is compelling
   - If still unresolved → log BOTH perspectives in the relevant review file and let the user decide

4. **Log all deliberations** to `reviews/codex_deliberation_log.md`:
   ```markdown
   ### [Stage] — [Topic]
   **Codex said**: [summary]
   **Claude's assessment**: AGREE / PARTIALLY AGREE / DISAGREE
   **Reasoning**: [why]
   **Resolution**: [what was done]
   **Rebuttal needed**: yes/no
   ```

This protocol applies to EVERY Codex interaction below — not just reviews, but research cross-checks, figure audits, risk radar, etc. The goal is genuine collaboration, not rubber-stamping.

## Provenance Logging Protocol

Every agent that writes, revises, or modifies manuscript content MUST append provenance entries to `research/provenance.jsonl`. This creates a traceable chain from every word in the final paper back to its origin.

**When to log:**
- After writing each paragraph or subsection (action: `write`)
- After revising text based on review feedback (action: `revise`)
- After cutting/removing content (action: `cut`)
- After adding new content during expansion (action: `add` or `expand`)
- After reordering sections or paragraphs (action: `reorder`)
- After a research query that directly informs writing (action: `research`)
- After a planning decision that shapes the paper (action: `plan`)

**Entry format** — append one JSON object per line to `research/provenance.jsonl`:

```json
{"ts":"[ISO-8601]","stage":"[stage number]","agent":"[your agent name]","action":"[write|revise|cut|add|expand|reorder|research|plan]","target":"[section/paragraph, e.g. methods/p3]","reasoning":"[WHY you made this choice — what sources, logic, or feedback drove it]","sources":["bibtex_keys"],"claims":["C1"],"feedback_ref":"reviews/file.md#issue","diff_summary":"one-line change summary","iteration":0}
```

**Required fields**: `ts`, `stage`, `agent`, `action`, `target`, `reasoning` — always present.
**Conditional fields**:
- `sources` — BibTeX keys of source extracts that informed this action (required for `write`, `add`, `expand`)
- `claims` — claim IDs from `research/claims_matrix.md` that this action supports (when applicable)
- `feedback_ref` — pointer to the review feedback that triggered this action (required for `revise`, `cut` during QA)
- `diff_summary` — one-line description of the change (required for `revise`, `cut`, `expand`)
- `archived_to` — file path where cut content was saved (required for `cut`)
- `iteration` — 0 for the initial pipeline, 1+ for `/auto` iterations

**For cuts**: Save the removed text to `provenance/cuts/[section]-[paragraph]-[context].tex` and record the path in `archived_to`. Never delete content without archiving.

**Paragraph targeting**: Use `[section]/p[N]` format where N is the paragraph number within that section (1-indexed). E.g., `introduction/p1`, `methods/p5`, `discussion/p3`. For subsections, use `methods/training-procedure/p2`. When revising, if a paragraph is rewritten entirely, keep the same target ID. If a paragraph is split, use `methods/p3a` and `methods/p3b`.

**Abbreviated instruction for agent prompts** — include this in every writing, revision, expansion, and QA agent prompt:

```
PROVENANCE — After EACH writing or editing action, append a JSON entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"[N]","agent":"[your-name]","action":"[write|revise|cut|add|expand]","target":"[section/pN]","reasoning":"[why]","sources":["keys"],"claims":["CN"],"diff_summary":"[what changed]","iteration":0}
For cuts, save removed text to provenance/cuts/[section]-[pN]-[context].tex and record in archived_to field.
```

---

## Domain Detection & Skill Routing

Before starting research, analyze the topic to determine the paper's domain. This determines which skills and databases agents should prioritize.

**Detect the domain from the topic, then set DOMAIN_SKILLS accordingly:**

| Domain | Indicator keywords | Priority skills to invoke |
|-|-|-|
| Biomedical / Life Sciences | gene, protein, cell, disease, clinical, drug, genomic, molecular, pathology, cancer, mutation | `literature-review`, `pubmed-database`, `biorxiv-database`, `gene-database`, `uniprot-database`, `ensembl-database`, `clinvar-database`, `gwas-database`, `kegg-database`, `reactome-database`, `opentargets-database`, `string-database`, `pdb-database`, `biopython`, `scanpy` |
| Chemistry / Drug Discovery | molecule, compound, synthesis, binding, docking, SMILES, drug, pharmacology, ADMET | `pubchem-database`, `chembl-database`, `drugbank-database`, `zinc-database`, `bindingdb-database`, `rdkit`, `datamol`, `medchem`, `molfeat`, `diffdock`, `rowan` |
| Computer Science / AI/ML | neural, network, model, training, algorithm, deep learning, transformer, LLM, NLP, vision | `arxiv-database`, `transformers`, `pytorch-lightning`, `scikit-learn`, `torch-geometric`, `shap`, `umap-learn` |
| Physics / Quantum | quantum, physics, particle, field, relativity, simulation, optics | `arxiv-database`, `astropy`, `qiskit`, `cirq`, `pennylane`, `qutip`, `sympy` |
| Materials Science | crystal, material, alloy, polymer, semiconductor, lattice | `arxiv-database`, `pymatgen` |
| Ecology / Geospatial | ecology, climate, satellite, geographic, species, biodiversity | `geomaster`, `geopandas`, `scikit-bio` |
| Economics / Finance | market, economic, fiscal, stock, hedge fund, GDP | `fred-economic-data`, `alpha-vantage`, `edgartools`, `hedgefundmonitor`, `usfiscaldata` |
| Clinical / Medical | patient, treatment, trial, diagnosis, clinical, hospital | `clinicaltrials-database`, `fda-database`, `clinical-reports`, `clinical-decision-support`, `pyhealth`, `clinpgx-database` |
| General / Cross-domain | (default) | `literature-review`, `arxiv-database`, `openalex-database` |

**All domains also get these universal skills:**
`scientific-writing`, `citation-management`, `peer-review`, `statistical-analysis`, `scientific-visualization`, `venue-templates`, `scientific-critical-thinking`, `research-lookup`, `exploratory-data-analysis`, `matplotlib`, `seaborn`, `plotly`

Store the detected domain and skill list in your context — pass relevant skills to each agent.

---

## Pipeline

### Stage 1: Deep Literature Research

**Goal**: Comprehensive field understanding + 30-50 verified references in `references.bib`.

Spawn **4-5 research agents in parallel**. Each agent must be told to invoke the relevant skills for the detected domain. Each writes to a separate file.

**IMPORTANT — Tool Fallback Chains**: Research agents must try multiple tools. If one fails, try the next. Include this fallback instruction in EVERY research agent prompt:

```
TOOL FALLBACK CHAIN — try in this order, skip failures:
1. Domain-specific database skills (e.g., pubmed-database, arxiv-database)
2. Perplexity search (mcp__perplexity__search or mcp__perplexity__reason)
3. Web search (WebSearch tool)
4. Firecrawl search (mcp__firecrawl__firecrawl_search)
5. Web fetch of known database URLs (WebFetch tool)
6. research-lookup skill as a general fallback

If a tool returns an error or is unavailable, log it and move to the next.
You MUST try at least 3 different tools. Do not stop at the first failure.
If ALL tools fail for a query, note the gap and move on — other agents may cover it.

RESEARCH LOG — After EACH tool call (success or failure), append an entry to research/log.md:
```markdown
### [TIMESTAMP] — [YOUR AGENT NAME]
- **Tool**: [tool name, e.g., mcp__perplexity__search]
- **Query**: [exact query string]
- **Result**: [SUCCESS: N papers found / FAILURE: error message / EMPTY: no results]
- **Key finds**: [1-2 sentence summary of what was found, or "N/A"]
- **URLs/DOIs**: [list any URLs or DOIs discovered]
```
This log is critical for research provenance. Do not skip it.

SOURCE EXTRACTS — When you find a paper that you cite in your output:
1. Create a file: research/sources/<bibtexkey>.md (e.g., research/sources/smith2024.md)
2. Determine access level based on what you ACTUALLY accessed:
   - **FULL-TEXT**: You read the complete paper (PDF in attachments/, open-access HTML, arXiv/bioRxiv full text)
   - **ABSTRACT-ONLY**: You read the abstract but not the full paper (API metadata, database entry, Perplexity summary)
   - **METADATA-ONLY**: You only know title/authors/year/venue (CrossRef hit, citation in another paper)
3. Format:
```markdown
# <Paper Title>

**Citation**: <authors>, <title>, <venue>, <year>
**DOI/URL**: <doi or url>
**BibTeX Key**: <key>
**Access Level**: FULL-TEXT | ABSTRACT-ONLY | METADATA-ONLY
**Accessed Via**: <tool name and method — e.g., "arXiv API full text", "Perplexity summary", "PDF in attachments/davis1997.pdf">

## Content Snapshot

> Paste here the ACTUAL content you accessed, verbatim or near-verbatim.
> This section records what you really read — not what you think the paper says.
>
> - If FULL-TEXT: key sections (abstract + most relevant passages to this paper's topic, 500-1500 words)
> - If ABSTRACT-ONLY: the abstract as retrieved, plus any excerpts from Perplexity/web summaries
> - If METADATA-ONLY: "No content accessed. Title, authors, and venue only."

## Key Findings Used

<bullet points of specific findings, data, or claims you referenced from this paper>
<For each finding, note whether it came from the snapshot above or was inferred>

## Provenance

- **Found via**: <tool name, e.g., mcp__perplexity__search>
- **Query**: <exact query string>
- **Date**: <timestamp>
- **URL**: <where the content was accessed>
```
This ensures every cited claim is traceable to a specific source document with a verifiable content snapshot.
```

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

**Agent 6 — "Recent Frontiers (2024-2026)"**
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

**Agent 7 — "Negative Results & Failed Approaches"**
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

**Agent 8 — "Cross-Disciplinary Insights"**
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

**Agent 9 — "Datasets, Benchmarks & Reproducibility"**
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

**Agent 10 — "Industry & Applied Work"**
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

**Agent 11 — "Competing Hypotheses & Debates"**
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

**Agent 12 — "Intellectual Lineage"**
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

**After all research agents complete, spawn a Bibliography Builder agent** (model: haiku)**:**
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

**Checkpoint**: Count entries in `references.bib`. In standard mode, if fewer than 25 — or in deep mode, if fewer than 50 — report which research areas are underrepresented and spawn additional targeted research agents for those areas.

---

### Stage 1c: Codex Research Cross-Check

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

After all research agents and bibliography building are complete, use Codex to cross-check the key findings.

1. Read ALL research files: `research/survey.md`, `research/methods.md`, `research/empirical.md`, `research/theory.md`, `research/gaps.md` (and in deep mode, also the 7 additional files).
2. For EACH research file, call Codex to cross-check its claims:

```
mcp__codex-bridge__codex_ask({
  prompt: "Cross-check these research findings from [FILENAME]. For each major claim: (1) Is it accurately represented? (2) Are there contradicting studies or nuances missing? (3) Are key papers overlooked? (4) Are any claims exaggerated or out of context? Be specific — cite papers by name if you know of contradictions.",
  context: "[paste content of the research file being checked]"
})
```

3. Write all Codex responses to `research/codex_cross_check.md` (append each file's review as a section)
4. Apply the **Codex Deliberation Protocol**: evaluate each point, push back where you disagree, log the deliberation
5. If Codex identifies missing perspectives or inaccurate claims, spawn a **targeted follow-up research agent** (model: claude-sonnet-4-6[1m]) to investigate those specific gaps. The agent should update the relevant research files and add any new references to `references.bib`.

**Checkpoint**: Verify `research/codex_cross_check.md` exists. If it does not exist, you skipped this stage — go back and do it.

Update `.paper-state.json`: mark `codex_cross_check` as done.

---

### Stage 1d: Source Coverage Audit & Acquisition

**Goal**: Ensure every cited source has a verifiable content snapshot, and obtain full text for critical papers.

This stage audits what the research agents actually accessed vs. what they cited. Papers where the pipeline only saw an abstract are flagged — the user can provide full-text PDFs before the writing stages begin.

**This stage has three phases: audit, resolve, acquire.**

#### Phase 1: Audit

1. **Read `references.bib`** — extract every BibTeX key
2. **Scan `research/sources/`** — check which keys have source extract files
3. **For each reference, classify access level**:
   - If `research/sources/<key>.md` exists AND has `Access Level: FULL-TEXT` → **FULL-TEXT**
   - If a PDF matching this paper exists in `attachments/` → **FULL-TEXT** (but may need ingesting — see Phase 3)
   - If `research/sources/<key>.md` exists with `Access Level: ABSTRACT-ONLY` → **ABSTRACT-ONLY**
   - If no source file exists → **METADATA-ONLY**
4. **Write audit summary** to `research/source_coverage.md`:
   ```markdown
   # Source Coverage Audit
   Generated: [timestamp]

   ## Summary
   - Total references: N
   - Full-text accessed: N (X%)
   - Abstract-only: N (Y%)
   - Metadata-only: N (Z%)

   ## Full-Text Sources
   | Key | Title | Access Method |
   |-|-|-|
   | smith2024 | "Title..." | arXiv full text |

   ## Abstract-Only Sources (need upgrade)
   | Key | Title | DOI | Why It Matters |
   |-|-|-|-|
   | davis1997 | "Toward a Stewardship..." | 10.5465/... | Foundational theory — cited 5 times in paper |

   ## Metadata-Only Sources (need investigation)
   | Key | Title | Notes |
   |-|-|-|
   | jones2023 | "Title..." | Only found as citation in another paper |
   ```

#### Phase 2: Automated OA Resolution

For each ABSTRACT-ONLY and METADATA-ONLY source, attempt to find a legal open-access copy. Try in order:

1. **Semantic Scholar** — check `openAccessPdf` field:
   ```
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=openAccessPdf,title
   ```
   If `openAccessPdf.url` is present, fetch it and update the source extract to FULL-TEXT.

2. **Web search for PDF** — the "Bing filetype:pdf trick", automated:
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<exact paper title>\" <first author last name> filetype:pdf",
     limit: 5
   })
   ```
   If results include a direct PDF URL (ending in `.pdf` or from known preprint servers like arxiv.org, biorxiv.org, ssrn.com, repec.org), attempt to fetch and snapshot the content.

3. **Academic repository search**:
   ```
   mcp__firecrawl__firecrawl_search({
     query: "\"<exact paper title>\" site:researchgate.net OR site:academia.edu OR site:ssrn.com",
     limit: 3
   })
   ```
   If found on these sites, note the URL — it may require a free account to download, which goes on the user's acquisition list.

4. **For each successfully resolved paper**:
   - Fetch the content (WebFetch on the PDF/HTML URL)
   - Update or create `research/sources/<key>.md` with Access Level: FULL-TEXT and the content snapshot
   - Log the resolution in `research/log.md`

5. **For each paper where a URL was found but content couldn't be fetched** (login wall, expired link, CAPTCHA):
   - Note the URL in the acquisition list with a hint: "Found on Academia.edu — free account required"

#### Phase 3: Human Acquisition (pause if needed)

After automated resolution, re-count access levels. If there are still ABSTRACT-ONLY or METADATA-ONLY papers:

1. **Prioritize the acquisition list** — sort by how many times each paper is cited in the research files (more citations = more important to have full text for). In standard mode, present only the **top 5** papers. In deep mode, present ALL abstract-only and metadata-only papers.
2. **Use AskUserQuestion** to present the list and pause:

```
I've completed the literature research and found [N] references. Here's the source coverage:

✓ [X] papers with full text accessed
⚠ [Y] papers where I only read the abstract
✗ [Z] papers where I only have metadata

The following papers would strengthen the manuscript if I had full text.
They're sorted by importance (citation frequency in the paper):

1. **[key]** — "[Title]" ([Year])
   DOI: [doi] | Cited [N] times in draft
   💡 Suggested: Search "[title]" filetype:pdf on Bing
   🔗 Found on Academia.edu: [url] (free account needed)

2. **[key]** — "[Title]" ([Year])
   DOI: [doi] | Cited [N] times in draft
   💡 Suggested: Check your university library access

[... more papers ...]

Drop any PDFs you find into the `attachments/` folder and say "continue" when ready.
Or say "skip" to proceed with abstract-level sources (I'll flag thin evidence in the paper).
```

3. **When the user responds**:
   - If "continue" or similar: scan `attachments/` for new PDFs, run the ingestion logic (same as `/ingest-papers`), update source extracts to FULL-TEXT with content snapshots
   - If "skip" or similar: proceed, but mark all abstract-only sources with a warning flag in the claims-evidence matrix

4. **If ALL sources already have full text** after Phase 2, skip the pause entirely — no need to bother the user.

#### Phase 4: Update Coverage Report

After acquisition is complete (or skipped), update `research/source_coverage.md` with final counts. This file persists as a permanent record of what the pipeline had access to.

**Checkpoint**: Verify `research/source_coverage.md` exists. Update `.paper-state.json`:
```json
"source_acquisition": {
  "done": true,
  "completed_at": "...",
  "full_text": N,
  "abstract_only": N,
  "metadata_only": N,
  "user_provided": N,
  "auto_resolved": N
}
```

Update `.paper-progress.txt`: "Stage 1d complete: [N] full-text, [M] abstract-only sources"

#### Knowledge Graph Build

After source acquisition is complete, build the knowledge graph from all source extracts:

```bash
python scripts/knowledge.py build
```

This creates a queryable knowledge graph in `research/knowledge/` from all files in `research/sources/`. The graph extracts entities (papers, theories, methods, findings, authors) and relationships (cites, contradicts, supports, extends) that agents can query during writing.

**If `scripts/knowledge.py` does not exist or `OPENROUTER_API_KEY` is not set**, skip this step silently — the knowledge graph is optional. The pipeline works without it; agents fall back to reading research/ files directly.

Update `.paper-state.json`: add `"knowledge_graph": { "done": true, "entities": N, "relationships": N }` to the stages object.

---

### Stage 2: Thesis, Contribution & Outline

Read ALL files in `research/`, especially `research/gaps.md`. Then:

1. **Define the paper's thesis and contribution** based on the gap analysis:
   - What specific problem does this paper address?
   - What is the novel contribution?
   - What are the key claims this paper will make?
   - Write these to `research/thesis.md`

2. **Determine paper structure** based on topic type AND venue:
   - Read `.venue.json` for venue-specific section order (e.g., Nature puts Results before Methods)
   - Read `.venue.json` for citation style (natbib vs numeric vs APA), page limits, abstract limits
   - Survey → taxonomy-based Related Work, no Methods/Results; instead use thematic analysis sections
   - Empirical → standard IMRAD with heavy Methods and Results
   - Theoretical → formal framework section, proofs, theoretical analysis
   - Methods → proposed approach, evaluation against baselines
   - **Adapt section word targets** if venue has page limits (e.g., 8-page IEEE = shorter sections)

3. **Create detailed outline** in `main.tex`:
   - Replace all placeholder content
   - Add `\maketitle`, abstract placeholder, all sections/subsections
   - Under each subsection, add `% OUTLINE:` comments with key arguments, citation keys, figure/table plans, word targets
   - Add `\bibliographystyle{plainnat}` and `\bibliography{references}`
   - Update title and authors — derive an appropriate academic title from the topic

4. **Build a Claims-Evidence Matrix** — create `research/claims_matrix.md`:
   - List every major claim the paper will make (from thesis.md)
   - For each claim, identify: what evidence supports it (experiment, citation, formal proof, data)
   - For each claim, note: which section will present this evidence
   - Flag any claims that lack evidence — these must be either supported or removed before writing begins
   - Format as a markdown table:
     ```
     | # | Claim | Evidence Type | Evidence Source | Source Access | Section | Status |
     |-|-|-|-|-|-|-|
     | 1 | Our method improves X by Y% | Experiment | Table 2, benchmark Z | N/A (own data) | Results | Planned |
     | 2 | Prior approaches fail because... | Citation | smith2024, jones2025 | smith2024: FULL-TEXT, jones2025: ABSTRACT-ONLY ⚠ | Related Work | Supported |
     ```
   - This matrix becomes a quality gate in Stage 5 — every claim must have status "Supported" before the paper passes QA
   - **Source access warning**: Any claim supported ONLY by ABSTRACT-ONLY sources should be flagged with ⚠ — the pipeline may be inferring beyond what was actually read. In Stage 5 QA, reviewers must verify these claims are conservative and well-hedged.
   - **If the knowledge graph is available** (`research/knowledge/` exists), use it to verify evidence:
     ```bash
     python scripts/knowledge.py evidence-for "claim text here"
     python scripts/knowledge.py evidence-against "claim text here"
     ```
     Update the matrix with any additional evidence or contradictions the graph surfaces.

5. **Codex reviews the Claims-Evidence Matrix**:
   ```
   mcp__codex-bridge__codex_ask({
     prompt: "Review this claims-evidence matrix for a research paper. For each claim, assess: (1) Is the proposed evidence actually sufficient to support this claim? (2) Are there claims that are too strong for the evidence type? (e.g., claiming 'proves' based on empirical results) (3) Are there obvious missing claims that the paper should make but doesn't? (4) Are any claims redundant or overlapping?",
     context: "[paste content of research/claims_matrix.md]"
   })
   ```
   Apply the **Codex Deliberation Protocol**. Update the matrix based on agreed feedback. Log deliberation.

6. Use the `scientific-writing` skill for IMRAD structure guidance.
7. Use the `venue-templates` skill if targeting a specific venue.

**Checkpoint**: Verify outline has 5+ major sections, subsections under each, and planning notes.

Update `.paper-state.json`: mark `outline` as done.

---

### Stage 2b: Codex Thesis Stress-Test

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

1. Read `research/thesis.md` for the thesis/contribution statement
2. Read `main.tex` for the outline structure
3. Call the Codex MCP tool directly:

```
mcp__codex-bridge__codex_plan({
  prompt: "Stress-test this research paper plan. The thesis is: [paste thesis]. The sections are: [list sections]. Challenge: (1) Is the contribution genuinely novel given the related work? (2) Is the argument structure sound — does evidence flow logically? (3) What will reviewers attack? (4) Are there missing sections or weak links?",
  context: "[paste content of research/thesis.md and the outline sections from main.tex]"
})
```

4. Write the Codex response to `research/codex_thesis_review.md`
5. If Codex identifies structural problems, fix them in the outline in `main.tex` before proceeding
6. Surface any disagreements between your assessment and Codex's to the user

**Checkpoint**: Verify `research/codex_thesis_review.md` exists. If it does not exist, you skipped this stage — go back and do it.

Update `.paper-state.json`: mark `codex_thesis` as done.

---

### Stage 2c: Thesis-Informed Targeted Research [DEEP]

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

**Checkpoint**: Verify targeted research files exist. Update `.paper-state.json`: mark `targeted_research` as done.

---

### Stage 2d: Novelty Verification

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

Before investing hours in writing, verify the contribution hasn't already been published. This catches the worst-case scenario: writing a complete paper about something that already exists.

1. Read `research/thesis.md` for the contribution statement and key claims
2. Search for existing work that makes the SAME contribution:

**Search strategy** — use ALL available tools in parallel:
- Search arXiv for papers with similar titles and abstracts (use `mcp__perplexity__search` or domain database skills)
- Search Semantic Scholar / Google Scholar for the specific method or approach name
- Search DBLP for the exact technique combination
- If Codex is available, also ask:
  ```
  mcp__codex-bridge__codex_ask({
    prompt: "Has this specific contribution already been published? The claimed contribution is: [paste thesis]. Search your knowledge for any existing work that makes the same or very similar claims. Be thorough — check not just the exact method name but also equivalent approaches under different names.",
    context: "[paste content of research/thesis.md]"
  })
  ```

3. Write the results to `research/novelty_check.md`:
   - **NOVEL**: No existing work makes the same contribution → proceed
   - **PARTIALLY NOVEL**: Similar work exists but our angle/approach differs → document how we differentiate, update thesis.md to clarify the distinction
   - **NOT NOVEL**: Existing work already covers this → STOP. Report to user with the conflicting papers. Do NOT proceed to writing.

4. If partially novel, update `research/thesis.md` and the outline in `main.tex` to explicitly differentiate from the similar work. Add the similar papers to `references.bib` and plan to discuss them in Related Work.

**Checkpoint**: Verify `research/novelty_check.md` exists and status is NOVEL or PARTIALLY NOVEL. If NOT NOVEL, halt the pipeline and report to the user.

Update `.paper-state.json`: mark `novelty_check` as done.

---

### Stage 3: Section-by-Section Writing

Each section gets its own dedicated agent. **Run sequentially** — each section builds on prior ones.

**[DEEP] Per-Section Literature Deep-Dives**

If depth is `"deep"`, BEFORE each writing agent starts, spawn a quick **section research agent** (model: haiku) to find literature specific to that section's topic:

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

### Stage 4: Figures, Tables & Visual Elements

**Step 4a: Data-driven figures with Praxis (if available)**

If `vendor/praxis/scripts/` exists AND `attachments/` contains data files, spawn a **data analysis agent** (model: claude-sonnet-4-6[1m]):
```
You are a scientific data analyst. Read .claude/skills/praxis/SKILL.md for the Praxis toolkit API.
Read vendor/praxis/references/cookbook.md for worked examples.
Read .venue.json for the target venue — map to Praxis journal style (nature, ieee, acs, science, elsevier, springer, rsc, wiley, mdpi).

Scan attachments/ for data files. For each file:
1. Auto-detect the characterisation technique from the data structure
2. Write a Python analysis script using Praxis (sys.path.insert(0, "vendor/praxis/scripts"))
3. Apply the venue-matched journal style: apply_style("<style>")
4. Use colourblind-safe palette: set_palette("okabe_ito")
5. Run technique-specific analysis (XRD → crystallite size, DSC → Tg/Tm, mechanical → modulus, etc.)
6. Export figures as PDF to figures/
7. Save scripts to figures/scripts/ for reproducibility

After generating figures:
- Add \includegraphics{} to Results section of main.tex with descriptive captions
- Add quantitative results to the Results text
- Add methodology to the Methods section
- Write analysis summary to research/praxis_analysis.md

If no data files exist in attachments/, skip this step.
```

If Praxis is not available but data files exist, fall back to generic matplotlib (use the `matplotlib` skill from `.claude/skills/matplotlib/SKILL.md`).

**Step 4b: Structural figures and tables**

Spawn an agent (model: claude-sonnet-4-6[1m]):
```
You are a scientific visualization specialist.
Read main.tex completely.

Invoke the `scientific-visualization` skill (read .claude/skills/scientific-visualization/SKILL.md).

Ensure the paper has:
1. At least 1 overview/architecture/framework figure (use TikZ or describe in a figure environment)
2. At least 2 data/results tables with booktabs formatting
3. All figures/tables referenced in text with \ref{} BEFORE they appear
4. All captions are descriptive (2-3 sentences explaining what the figure shows and why it matters)
5. Consistent figure/table numbering and labeling
6. Float placement uses [htbp]

If Praxis already generated data figures (check figures/ directory), don't duplicate them — focus on structural/conceptual figures.
Add any new figures to main.tex with proper \includegraphics{} and \caption{}.
Edit main.tex directly.
```

**Step 4c: Codex Figure & Claims Audit**

After figures and tables are in place, call Codex to sanity-check the visual claims:

```
mcp__codex-bridge__codex_ask({
  prompt: "Audit the figures, tables, and their associated claims in this manuscript. For each figure/table: (1) Does the caption accurately describe what is shown? (2) Do the claims in the surrounding text match what the data actually shows? (3) Are there misleading axis scales, cherry-picked comparisons, or missing error bars/confidence intervals? (4) Are any figures redundant or better presented as tables (or vice versa)?",
  context: "[paste the Results and Discussion sections from main.tex, including all figure/table environments]"
})
```

Write the response to `reviews/codex_figures_audit.md`. Fix any critical mismatches between figures and claims in main.tex immediately.

---

### Stage 5: Quality Assurance Loop

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
Read main.tex and references.bib completely.

Evaluate:
- Claims supported by evidence or citations?
- Methodology sound and reproducible?
- Results properly analyzed with appropriate statistics?
- Limitations honestly discussed?
- Argument logically coherent Introduction → Conclusion?
- Mathematical notation defined and consistent?
- Appropriate use of domain-specific terminology?

Write a detailed review to reviews/technical.md:
- CRITICAL issues (list with line references and specific fixes)
- MAJOR issues (list with line references and specific fixes)
- MINOR issues (list)
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

Read ALL files in `reviews/` including `codex_adversarial.md`. Build a prioritized fix list:
1. All CRITICAL issues (must fix)
2. All MAJOR issues (should fix)
3. Word count shortfalls
4. Missing citations

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

After all fixes, compile: latexmk -pdf -interaction=nonstopmode main.tex
Fix any LaTeX errors.
Edit main.tex and references.bib directly.
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

### Post-QA: Consistency & Claims Audit

**These steps run ONCE after the QA loop exits (all quality criteria met).** They are NOT inside the loop.

Run two final audits **in parallel** (model: claude-sonnet-4-6[1m]):

**Consistency Checker:**
```
Read main.tex completely. Check for:
- Notation inconsistencies (same concept, different symbols)
- Terminology drift (same thing called different names)
- Abbreviations used before definition or defined twice
- Tense inconsistencies within sections
- Reference format inconsistencies (Figure vs Fig., Section vs Sec.)
Fix all issues directly in main.tex.
Write report to reviews/consistency.md.
```

**Claims Auditor:**
```
Read main.tex completely. For every claim, check:
- "novel"/"first" — is it actually, given the Related Work?
- "significantly" — is there a statistical test?
- "prove"/"demonstrate" — is there formal proof or only experiments?
- Unsupported factual claims missing citations
- Overclaims from limited experiments ("generalizes" from 2 datasets)
Fix Critical and Major overclaims in main.tex (soften language, add hedging, note missing tests).
Write report to reviews/claims_audit.md.
```

After both complete, also spawn a **reproducibility checker** (model: haiku):
```
Read main.tex. Check if Methods section includes: all hyperparameters, training details, compute resources, dataset descriptions, evaluation metric definitions, random seed/variance info.
For each missing item, add it to the appropriate section in main.tex.
Write checklist to research/reproducibility_checklist.md.
```

---

### Post-QA: Reference Validation (mandatory before finalization)

Spawn a **reference validation agent** (model: haiku):
```
You are a reference verification specialist. Your job is to ensure every citation is real.
Read references.bib. For EACH entry:
1. If DOI present: verify via CrossRef API (curl -s "https://api.crossref.org/works/DOI")
2. If no DOI: search for exact title using Perplexity or web search
3. Classify: VERIFIED, METADATA MISMATCH, SUSPICIOUS, or FABRICATED
4. Fix metadata mismatches directly in references.bib
5. REMOVE fabricated entries from references.bib AND their citations from main.tex

Write validation report to research/reference_validation.md.
After fixes, compile: latexmk -pdf -interaction=nonstopmode main.tex
```

**This is non-negotiable.** Fabricated references are the #1 risk in AI-assisted writing. Every reference must be verified before the paper is finalized. Update `.paper-state.json` with validation results.

**Codex Independent Reference Verification**

In parallel with Claude's reference validation, have Codex independently verify a random sample of 10-15 references:

```
mcp__codex-bridge__codex_ask({
  prompt: "Verify these bibliographic references. For each one, confirm: (1) Is this a real publication? (2) Are the authors, title, venue, and year correct? (3) Does the DOI (if present) match? Flag any that seem fabricated, have wrong metadata, or that you cannot confirm exist.\n\nReferences to verify:\n[paste 10-15 randomly selected BibTeX entries from references.bib]",
  context: "[paste the selected BibTeX entries]"
})
```

Apply the **Codex Deliberation Protocol**: if Codex flags a reference that Claude's validator marked as verified, investigate further — one of them is wrong. If Codex confirms references Claude flagged as suspicious, that's stronger evidence for removal. Write results to `reviews/codex_ref_verification.md`.

---

### Post-QA: Codex Risk Radar

**Run this ONCE after reference validation, before finalization.**

Use Codex's risk radar tool to get a final risk assessment of the complete manuscript:

```
mcp__codex-bridge__codex_risk_radar({
  prompt: "Final risk assessment of this research manuscript before submission. Evaluate across these dimensions: (1) SCIENTIFIC RISK — are there claims that could be proven wrong or are unfalsifiable? (2) ETHICAL RISK — any issues with data handling, consent, bias, or dual-use concerns? (3) REPUTATIONAL RISK — anything that could embarrass the authors if scrutinized? (4) REPRODUCIBILITY RISK — could an independent team reproduce these results from the description? (5) NOVELTY RISK — is the contribution incremental enough that reviewers might desk-reject? Rate each dimension: LOW / MEDIUM / HIGH with specific evidence.",
  context: "[paste the full content of main.tex]"
})
```

Write the response to `reviews/codex_risk_radar.md`.

**Action on results:**
- Any HIGH risk item → must be addressed before finalization. Edit main.tex to mitigate (add caveats, strengthen methods, etc.)
- MEDIUM risk items → flag for the user's attention in the final report but don't block finalization
- LOW risk items → note and move on

**Checkpoint**: Verify `reviews/codex_risk_radar.md` exists.

Update `.paper-state.json`: mark `codex_risk_radar` as done.

---

### Stage 6: Finalization

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
```

After polish, generate a **lay summary** (model: haiku):
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

Do NOT change technical content, citations, or mathematical notation.
Do NOT remove necessary hedging (e.g., "may" when results are genuinely uncertain).
Focus on making the paper read like a human domain expert wrote it.
Edit main.tex directly.
```

Then do one final compile and report results.

Finally, **archive all research artifacts** by running the `/archive` command. This creates a self-contained `archive/` directory with all research notes, reviews, figures, data, and metadata organized for easy browsing, with a README index. This allows the user to browse through all research findings, downloaded materials, and intermediate outputs after the pipeline completes.

**Report Codex collaboration metrics:**

```
mcp__codex-bridge__codex_stats({})
```

Include the Codex stats in the final completion report to show how the two AI systems collaborated throughout the pipeline.

---

## Quality Criteria

ALL must pass to exit Stage 5. Note: writing targets in Stage 3 are intentionally higher than these minimums — aim high, gate at the floor. Scale all targets proportionally if venue has page limits (Rule 12).

| Criterion | Requirement |
|-|-|
| Sections substantively complete | No obvious gaps, thin arguments, or missing depth |
| Introduction | Sets up the problem, contribution, and paper structure clearly |
| Related Work / Background | Covers the field thoroughly — no major omissions a reviewer would flag |
| Methods / Approach | Detailed enough for reproduction by an independent researcher |
| Results / Experiments | All claims supported by presented evidence |
| Discussion | Honest limitations, meaningful comparisons with prior work |
| Conclusion | Concise summary with specific results |
| Abstract | Self-contained, specific, quantitative where possible |
| Claims-Evidence Matrix | Every claim in research/claims_matrix.md has status "Supported" |
| References in .bib | 25+ verified entries |
| Placeholder text | 0 (no TODO/TBD/FIXME/lipsum/mbox{}) |
| LaTeX compilation | No errors |
| Tables | 2+ with booktabs |
| \ref{} cross-references | All resolve |
| \citep{}/\citet{} keys | All exist in references.bib |
| Body text format | Full paragraphs only (no bullet points) |

---

## Error Handling & Robustness

- **Agent failure**: If an agent fails or produces no output, log the error and retry ONCE with a simplified prompt. If it fails again, skip and note in the task list what was missed.
- **Empty research results**: If a research agent returns no papers, try alternative search tools (different MCP servers, web search, etc.). If still empty, note the gap and continue — other agents may cover it.
- **Compilation errors**: After any edit to main.tex, compile. If errors appear, fix them immediately before proceeding.
- **Word count under target after expansion**: If a section remains under target after 2 expansion attempts, accept it and flag for manual review.
- **Session interruption**: All progress is written to files (research/, reviews/, main.tex). On resume, check existing files and skip completed stages. Use TaskList to see prior progress.
- **Reference verification failures**: If a reference cannot be verified as real, REMOVE it rather than keeping a potentially fabricated citation.

## Rules

1. **Never fabricate references.** Every BibTeX entry must be a real, verifiable publication.
2. **Never leave bullet points in manuscript body.** All content must be flowing paragraphs.
3. **Write exhaustively.** More depth is always better. 2000 thorough words beats 500 concise ones.
4. **How to use skills.** When an agent prompt says "use the `scientific-writing` skill", the agent should read the file `.claude/skills/scientific-writing/SKILL.md` and follow its guidance. Skills are markdown files at `.claude/skills/<skill-name>/SKILL.md`. The `scientific-writing` skill is mandatory for all writing agents.
5. **Sequential writing, parallel research/review.** Writing agents one at a time. Research and review agents in parallel.
6. **Assess completeness after every writing agent.** If the section lacks depth, is missing citations, or leaves obvious gaps, expand immediately. The expansion agent should use `model: "claude-opus-4-6[1m]"`.
7. **Model selection.** Three tiers — use 1M context variants (`[1m]` suffix) for opus and sonnet so agents can read entire manuscripts + all research files + full bibliographies without hitting context limits:
   - **Opus 1M** (`model: "claude-opus-4-6[1m]"`): Writing, revision, expansion, final polish, gap analysis, de-AI polish — anything requiring deep reasoning, synthesis, or prose quality.
   - **Sonnet 1M** (`model: "claude-sonnet-4-6[1m]"`): Research agents, review agents, data analysis, figures — tasks requiring tool use, search, and structured evaluation.
   - **Haiku** (`model: "haiku"`): Bibliography building, reference validation, lay summary, reproducibility checklist, section lit searches — mechanical tasks requiring lookup, pattern matching, or summarization.

   **IMPORTANT**: The shorthand `"opus"` and `"sonnet"` resolve to the standard context models, NOT the 1M variants. You MUST use the full model IDs above for opus and sonnet agents.
8. **Track progress.** Use TaskCreate/TaskUpdate for every stage. Naming: `"Stage 1: Research"`, `"Stage 3: Write Introduction"`, etc. Set status to `in_progress` when starting, `completed` when done.
9. **Be patient.** This pipeline runs 1-4+ hours. Every stage matters. Do not rush or skip.
10. **Domain awareness.** Use the detected domain to choose appropriate skills and databases for each agent.
11. **Clear stale reviews.** Before each QA loop iteration (Stage 5a), delete old review files: `rm -f reviews/technical.md reviews/writing.md reviews/completeness.md` so reviewers evaluate the latest version.
12. **Venue-aware length.** If `.venue.json` has a `page_limit`, respect it. An 8-page IEEE paper must be concise — prioritize depth over breadth and cut less critical content. Read the venue config and adjust scope accordingly.

## Topic

$ARGUMENTS
