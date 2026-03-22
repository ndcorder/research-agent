# Write Paper — Autonomous Journal-Quality Research Paper Pipeline

You are an autonomous research paper writing system. You will produce a publication-ready, journal-quality research paper by orchestrating specialized agents across multiple stages. This process takes 1-4+ hours. Depth over speed, always.

## Setup

1. Read `.paper.json` for topic, venue, model, and config. If it doesn't exist, create it from the topic in $ARGUMENTS.
2. Read `.venue.json` if present for venue-specific formatting rules (sections, citation style, page limits).
3. Read `main.tex` and `references.bib` to understand current state.
4. Run: `mkdir -p research reviews figures`
5. Create a task for each pipeline stage using TaskCreate.
6. **Resume check**: Read `.paper-state.json` if it exists. It tracks completed stages and section word counts. Skip any stage marked `"done": true`. If no state file exists but `research/` has files or `main.tex` has content, infer progress and build the state file from what exists.

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
    "finalization": { "done": false }
  }
}
```

Write this file using the Write tool after every stage completion. On resume, read it first and skip completed work. Also write current progress to `.paper-progress.txt` (human-readable summary) so users can monitor from another terminal via `cat .paper-progress.txt`.

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
```

**Agent 1 — "Field Survey"** (model: sonnet)
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
```

**Agent 2 — "Methodology Deep Dive"** (model: sonnet)
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
```

**Agent 3 — "Empirical Evidence & Benchmarks"** (model: sonnet)
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
```

**Agent 4 — "Theoretical Foundations"** (model: sonnet)
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
```

**Agent 5 — "Gap Analysis & Positioning"** (model: sonnet)
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
```

**Note:** Run agents 1-4 in parallel (they're independent). Run agent 5 AFTER 1-4 complete (it reads their outputs).

**After all research agents complete, spawn a Bibliography Builder agent** (model: sonnet)**:**
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
```

**Checkpoint**: Count entries in `references.bib`. If fewer than 25, report which research areas are underrepresented and spawn additional targeted research agents for those areas.

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

4. Use the `scientific-writing` skill for IMRAD structure guidance.
5. Use the `venue-templates` skill if targeting a specific venue.

**Checkpoint**: Verify outline has 5+ major sections, subsections under each, and planning notes.

**Codex stress-test (if available)**: If `mcp__codex-bridge__codex_plan` is available, call it now:
```
Call mcp__codex-bridge__codex_plan with:
- prompt: "Stress-test this research paper plan. The thesis is: [thesis from research/thesis.md]. The sections are: [list sections from outline]. Challenge: (1) Is the contribution genuinely novel given the related work? (2) Is the argument structure sound — does evidence flow logically? (3) What will reviewers attack? (4) Are there missing sections or weak links?"
- context: [paste research/thesis.md + outline from main.tex]
```
If Codex identifies structural problems, address them in the outline before proceeding to writing. If codex-bridge is not available, skip this step.

---

### Stage 3: Section-by-Section Writing

Each section gets its own dedicated agent. **Run sequentially** — each section builds on prior ones.

**Every writing agent prompt MUST include:**
- The paper topic and contribution statement (from research/thesis.md)
- Instruction to read the FULL current main.tex for context
- Instruction to read references.bib for citation keys
- Instruction to read relevant research/ files for content
- Instruction to invoke the `scientific-writing` skill for prose quality
- The specific word count target as a MINIMUM
- `model: "opus"` for highest quality prose

**Section writing order and targets:**

| Order | Section | Target Words | Key instruction |
|-|-|-|-|
| 1 | Introduction | 1200+ | Broad context → specific problem → contribution → findings preview → paper organization. Cite 8-12 works. |
| 2 | Related Work | 2000+ | Organize THEMATICALLY in 3-5 subsections. Discuss 3-5 papers per theme. Position this work explicitly. Cite 15-20 works. |
| 3 | Methods/Approach | 2500+ | Full detail for reproduction. Math in equation/align environments. Pseudocode if applicable. Design rationale. Use `sympy` skill for formulations if appropriate. |
| 4 | Results/Experiments | 2000+ | Setup → quantitative results (tables) → ablations → qualitative analysis. At least 2 booktabs tables. Use `statistical-analysis` skill, `matplotlib` or `scientific-visualization` skill for figures. |
| 5 | Discussion | 1500+ | Interpret findings → compare with prior work → limitations (be honest) → broader implications → future work. Use `scientific-critical-thinking` skill. |
| 6 | Conclusion | 600+ | Restate problem → summarize approach → highlight key results (with numbers) → impact statement. No new information. |
| 7 | Abstract | 250+ | Written LAST. Self-contained. Specific quantitative claims. Read the ENTIRE paper first. |

**After each writing agent completes**, check the word count of that section inline. If under 70% of target, immediately spawn an expansion agent:
```
The [SECTION] section in main.tex is currently [N] words. Target: [TARGET]+.
Read main.tex. Invoke the `scientific-writing` skill.
EXPAND the section by adding depth, subsections, citations, analysis, and formal detail.
Do NOT delete existing content. Only ADD.
Target: [TARGET]+ words total for this section.
Edit main.tex directly.
```

---

### Stage 4: Figures, Tables & Visual Elements

**Step 4a: Data-driven figures with Praxis (if available)**

If `vendor/praxis/scripts/` exists AND `attachments/` contains data files, spawn a **data analysis agent** (model: sonnet):
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

Spawn an agent (model: sonnet):
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

---

### Stage 5: Quality Assurance Loop

**This stage LOOPS until all quality criteria pass.** Maximum 5 iterations.

#### Step 5a: Parallel Review

Spawn **3 review agents in parallel** (model: sonnet):

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

**Codex Adversarial Reviewer (if available):** In parallel with the 3 agents above, if `mcp__codex-bridge__codex_review` is available:
```
Call mcp__codex-bridge__codex_review with:
- prompt: "You are an adversarial peer reviewer. Find the weakest points in this manuscript: (1) Claims that exceed the evidence (2) Logical gaps in the argument chain (3) Methodological shortcuts (4) Missing baselines or unfair comparisons (5) Conclusions that don't follow from results. Be specific — cite sections and sentences."
- context: [read main.tex and pass its content]
- evidence_mode: true
```
Write Codex findings to `reviews/codex_adversarial.md`. If codex-bridge is not available, skip — the 3 agent reviewers are sufficient.

#### Step 5b: Synthesize Reviews

Read all files in `reviews/` (including `codex_adversarial.md` if it exists). Build a prioritized fix list:
1. All CRITICAL issues (must fix)
2. All MAJOR issues (should fix)
3. Word count shortfalls
4. Missing citations

#### Step 5c: Revision Agent

Spawn a revision agent (model: opus):
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

---

### Post-QA: Consistency & Claims Audit

**These steps run ONCE after the QA loop exits (all quality criteria met).** They are NOT inside the loop.

Run two final audits **in parallel** (model: sonnet):

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

After both complete, also spawn a **reproducibility checker** (model: sonnet):
```
Read main.tex. Check if Methods section includes: all hyperparameters, training details, compute resources, dataset descriptions, evaluation metric definitions, random seed/variance info.
For each missing item, add it to the appropriate section in main.tex.
Write checklist to research/reproducibility_checklist.md.
```

---

### Post-QA: Reference Validation (mandatory before finalization)

Spawn a **reference validation agent** (model: sonnet):
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

---

### Stage 6: Finalization

Spawn a **final polish agent** (model: opus):
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

After polish, generate a **lay summary** (model: sonnet):
```
Read main.tex completely. Generate:
1. A 200+ word plain-language summary (no jargon, high school reading level)
2. A 2-3 sentence elevator pitch
Write both to research/summaries.md.
If .venue.json indicates the venue requires a lay summary (Nature, medical journals), add it to main.tex after the abstract.
```

Then do one final compile and report results.

---

## Quality Criteria

ALL must pass to exit Stage 5. Note: writing targets in Stage 3 are intentionally higher than these minimums — aim high, gate at the floor. Scale all targets proportionally if venue has page limits (Rule 12).

| Criterion | Requirement |
|-|-|
| Total word count | 8000+ (or .paper.json target_words) |
| Introduction | 1000+ words |
| Related Work / Background | 1500+ words |
| Methods / Approach | 2000+ words |
| Results / Experiments | 1500+ words |
| Discussion | 1200+ words |
| Conclusion | 500+ words |
| Abstract | 200+ words |
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
6. **Check word counts after every writing agent.** Expand immediately if under 70% of target. The expansion agent should use `model: "opus"`.
7. **Model selection.** Writing and revision agents: `model: "opus"`. Research, review, and utility agents: `model: "sonnet"`.
8. **Track progress.** Use TaskCreate/TaskUpdate for every stage. Naming: `"Stage 1: Research"`, `"Stage 3: Write Introduction"`, etc. Set status to `in_progress` when starting, `completed` when done.
9. **Be patient.** This pipeline runs 1-4+ hours. Every stage matters. Do not rush or skip.
10. **Domain awareness.** Use the detected domain to choose appropriate skills and databases for each agent.
11. **Clear stale reviews.** Before each QA loop iteration (Stage 5a), delete old review files: `rm -f reviews/technical.md reviews/writing.md reviews/completeness.md` so reviewers evaluate the latest version.
12. **Venue-aware word targets.** If `.venue.json` has a `page_limit`, scale section word targets proportionally. An 8-page IEEE paper needs ~6000 words total, not 8000+. Read the venue config and adjust.

## Topic

$ARGUMENTS
