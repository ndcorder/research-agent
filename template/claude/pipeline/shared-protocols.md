# Shared Protocols

Reusable protocols referenced across multiple pipeline stages. The orchestrator reads this file once at pipeline start. Each protocol below is referenced by name in stage files.

---

## Bash Timeout Protocol

Some commands can run for minutes. To avoid the default 2-minute Bash timeout killing them:

- **`latexmk` / `pdflatex` / `bibtex`**: Always use `timeout: 600000` (10 minutes). Large papers with many references and figures can take 5-10 minutes to compile.
- **`python3 -m pip install`**: Use `run_in_background: true`. Package installation can be slow on first run and Claude can proceed with other work.
- **`python scripts/knowledge.py serve`**: Use `run_in_background: true`. Long-running worker that processes the ingestion queue. Started once at Stage 1d, runs throughout the pipeline.
- **`python scripts/knowledge.py enqueue`**: Instant (appends to queue file). No timeout needed.
- **`python scripts/knowledge.py drain`**: Blocks until queue is empty. Use `timeout: 600000` (10 minutes) or `run_in_background: true` if the pipeline can continue without a fully-built graph.
- **`python scripts/knowledge.py build`**: Use `run_in_background: true`. Batch fallback for standalone commands (10-30+ minutes).

All other Bash commands (curl, wc, ls, mkdir, cat, cp, rm, which, pdfinfo) complete in seconds and need no special timeout.

---

## Knowledge Graph Availability Protocol

The knowledge graph (LightRAG via `scripts/knowledge.py`) is optional but provides contradiction detection, entity coverage analysis, and evidence verification that significantly improve paper quality. When unavailable, downstream stages must compensate explicitly rather than silently degrading.

**Detection**: Stage 1d records `"knowledge_graph": { "available": true/false, ... }` in `.paper-state.json`. Any stage can also check directly: if `research/knowledge/` exists with content, the graph is available.

**When the knowledge graph is NOT available**, every stage that would have used it must:

1. **Log explicitly**: Report `"⚠ Knowledge graph not available — applying compensating checks"` (not silently skip).
2. **Compensate with source-based analysis**:
   - **Contradiction detection**: Manually compare claims across source extracts in `research/sources/`. For each major finding, check whether any other source reports a conflicting result. This is slower and less comprehensive than the graph, but catches the most obvious conflicts.
   - **Entity coverage**: Read all source extract Key Findings and compile a list of frequently-mentioned concepts, methods, and theories. Check whether the manuscript discusses each. This replaces the graph's automated entity coverage report.
   - **Evidence verification**: For each claim in the claims matrix, verify supporting sources by re-reading the relevant source extracts rather than querying the graph. Focus on WEAK and MODERATE claims.
3. **Tighten quality thresholds**:
   - In Stage 2: Apply a **-0.5 penalty** to evidence density scores for claims that rely on inference across multiple sources (the graph would have validated these cross-references). Any claim that drops from MODERATE to WEAK due to this penalty must be flagged for extra scrutiny.
   - In Stage 5 QA: The Technical Reviewer must include an explicit **"Manual Contradiction Check"** section — read the top 10 most-cited sources and flag any claims where sources disagree. This replaces the graph's `contradictions` output.
   - In Stage 5 QA: The Technical Reviewer must include an explicit **"Entity Coverage Check"** section — verify that all major concepts from the literature review appear in appropriate manuscript sections. This replaces the graph's `coverage` output.
4. **Note the gap**: Append to `reviews/technical.md` (Stage 5): `"Note: Knowledge graph was not available for this review. Contradiction detection and entity coverage checks were performed manually from source extracts. Some cross-source conflicts may have been missed."` This ensures the quality gap is visible in the review artifacts.

---

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

## Codex Telemetry Protocol

After every Codex bridge interaction (including the deliberation), append a structured JSONL entry to `research/codex_telemetry.jsonl`. This creates a machine-readable log of all Codex interactions, enabling cross-paper analysis of agreement rates, tool usage patterns, and disagreement hotspots.

**Entry format** — append one JSON object per line:

```json
{"ts":"[ISO-8601]","stage":"[stage id]","tool":"[codex_ask|codex_review|codex_plan|codex_risk_radar|codex_stats]","purpose":"[short description of what was asked]","outcome":"[AGREE|PARTIALLY_AGREE|DISAGREE|N_A]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"[file path written]","resolution_summary":"[one-line summary of what happened]"}
```

**Required fields**: `ts`, `stage`, `tool`, `purpose`, `artifact` — always present.
**Deliberation fields**: `outcome`, `points_raised`, `points_accepted`, `points_rejected` — set based on the Codex Deliberation Protocol result. Use `N_A` and `0` for informational tools where no deliberation occurs (codex_stats, codex_risk_radar).

**When to log**: After EVERY Codex tool call and its subsequent deliberation (if any). One entry per call. For loops (e.g., per-file cross-checks in Stage 1c, per-section spot-checks in Stage 3), log one entry per iteration.

**Abbreviated instruction for stage files** — include after each Codex call + deliberation block:

```
CODEX TELEMETRY — Append to research/codex_telemetry.jsonl:
{"ts":"[timestamp]","stage":"[N]","tool":"[tool]","purpose":"[what]","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"[file]","resolution_summary":"[one-line]"}
```

---

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

## Tool Fallback Chain

Include this instruction block in EVERY research agent prompt:

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

PROVENANCE — When your research findings directly inform a specific claim or argument direction, also append a provenance entry to research/provenance.jsonl with action "research", target "research/[your-output-file]", and reasoning explaining what this finding contributes to the paper's argument. Set stage to "1" and iteration to 0.
```

---

## Source Extract Format

Include this instruction block in EVERY research agent prompt:

```
SOURCE EXTRACTS — When you find a paper that you cite in your output:
1. Create a file: research/sources/<bibtexkey>.md (e.g., research/sources/smith2024.md)
2. Determine access level based on what you ACTUALLY accessed. Be STRICT — over-reporting FULL-TEXT causes the pipeline to skip source acquisition and degrades paper quality:
   - **FULL-TEXT**: You read substantial body content of the actual paper (multiple sections, methods, results). This means: PDF in attachments/, a full open-access HTML article body (not just the landing page), or arXiv/bioRxiv full text where you read beyond the abstract.
   - **ABSTRACT-ONLY**: You read the abstract and/or summaries but NOT the paper body. This includes: Perplexity summaries (even detailed ones), Semantic Scholar/OpenAlex metadata, database entries, web search snippets, paper landing pages, review articles summarizing this work. If you did not read the actual Methods/Results/Discussion sections written by the authors, this is ABSTRACT-ONLY.
   - **METADATA-ONLY**: You only know title/authors/year/venue (CrossRef hit, citation in another paper, reference list entry)

   ⚠ COMMON MISTAKE: Perplexity and web search results that describe a paper's findings are NOT full text — they are third-party summaries. Mark these ABSTRACT-ONLY even if the summary is detailed.
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

---

## Semantic Scholar API Rate Limiting Protocol

Stages that call the Semantic Scholar API (snowballing, co-citation analysis) must follow this protocol to avoid 429 errors and data loss.

Include this block in agent prompts that use Semantic Scholar:

```
SEMANTIC SCHOLAR RATE LIMITING:
1. Add a 3-second delay between consecutive API requests (time.sleep(3) or equivalent pacing)
2. If you receive a 429 (Too Many Requests) response:
   a. Wait 10 seconds before retrying
   b. On second 429 for the same request, wait 30 seconds
   c. On third 429, skip this paper and log the failure
3. If you receive a 5xx server error, retry once after 5 seconds, then skip
4. Track and report: total requests made, successful, rate-limited, failed
5. If more than 30% of requests are rate-limited, increase base delay to 5 seconds for remaining requests
6. Log every skipped paper to research/log.md so it can be retried manually

API base URL: https://api.semanticscholar.org/graph/v1/
Recommendations: https://api.semanticscholar.org/recommendations/v1/
No API key required, but rate limits are strict without one.
```

---

## Content Filter Fallback Protocol

Some academic papers contain passages (violence examples, demographic terminology, substance references) that trigger Anthropic's content filter when agents try to write verbatim quotes. The agent's output is blocked at the API level — the agent cannot self-correct because it is terminated before it knows it failed.

**Detection**: A content-filtered agent returns:
```
API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"Output blocked by content filtering policy"}}
```

**Fallback procedure** (for the orchestrator, not the agent):

1. The orchestrator already has the agent's prompt (it constructed it). Extract the prompt text.
2. Read the PDF content that the agent would have read (use the Read tool on the PDF).
3. Read the existing source extract to capture metadata fields.
4. Construct a self-contained prompt that embeds the PDF text directly (since the fallback model cannot use Claude Code tools). The prompt should include:
   - The full PDF text (or relevant pages)
   - The existing source extract metadata to preserve
   - The same deep-read instructions (Content Snapshot format, Key Findings format, Deep-Read flag)
5. Write the prompt to a temp file and call the fallback script:
   ```bash
   python3 scripts/openrouter-fallback.py /tmp/deep-read-KEY.txt > /tmp/deep-read-KEY-output.md
   ```
6. Review the output for quality, then write it to `research/sources/KEY.md`.
7. Append the provenance entry with `"fallback":"openrouter"` noted in the reasoning field.

**Model cascade** (defined in `scripts/openrouter-fallback.py`):
1. `google/gemini-2.5-flash` — fast, 1M context, strong at academic text extraction
2. `meta-llama/llama-4-maverick` — zero content restrictions

**Requires**: `OPENROUTER_API_KEY` environment variable (same key used by `scripts/knowledge.py`).

**Scope**: This protocol applies to any pipeline agent whose output is blocked by content filtering — not just deep-read agents. The pattern is the same: detect the 400 error, construct a self-contained prompt with embedded content, call the fallback script, write the result.
