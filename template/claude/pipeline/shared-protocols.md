# Shared Protocols

Reusable protocols referenced across multiple pipeline stages. The orchestrator reads this file once at pipeline start. Each protocol below is referenced by name in stage files.

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
