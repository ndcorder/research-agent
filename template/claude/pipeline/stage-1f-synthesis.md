# Stage 1f: Cross-Source Synthesis

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Knowledge Graph commands.

---

**Goal**: Synthesize knowledge ACROSS all source extracts to identify consensus, conflicts, methodological strengths and weaknesses, and competing frameworks. This stage transforms isolated per-source extracts into a structured understanding of the field, so that the planning stage (Stage 2) can formulate a thesis grounded in the actual state of the literature rather than individual paper summaries.

---

## Phase 1: Preparation

1. **Read all source extracts** — read every file in `research/sources/`. For each source, note:
   - BibTeX key
   - Access Level (`FULL-TEXT`, `ABSTRACT-ONLY`, `METADATA-ONLY`)
   - Source Type (journal article, book, conference paper, etc.)
   - Whether it has been deep-read (`Deep-Read: true`)
   - Key Findings (the bullet points from each extract)

2. **Run knowledge graph contradiction detection** (if `research/knowledge/` exists):
   ```bash
   python scripts/knowledge.py contradictions
   python scripts/knowledge.py entities
   ```
   Save the output — agents will use it as input alongside the source extracts.

   **If the knowledge graph is NOT available**: Log `"⚠ Knowledge graph not available — synthesis agents will perform manual contradiction detection from source extracts."` Then add the following instruction to EVERY synthesis agent prompt (in addition to "Not available" for the graph fields):
   ```
   IMPORTANT: The knowledge graph is not available for this paper. You must compensate by:
   - Explicitly comparing findings across sources to detect contradictions (do not assume absence of contradiction data means no contradictions exist)
   - Listing all major entities (methods, theories, datasets, metrics) you encounter across sources
   - Flagging any case where two sources report conflicting results, even if the conflict is subtle
   ```

3. **Build a source inventory table** — a working document (not persisted) listing all sources with their access level, source type, deep-read status, and a one-line summary of their primary finding. This gives each agent a map of the entire bibliography before they begin.

4. **Check for prior synthesis** — if `research/literature_synthesis.md` already exists with substantive content (>500 words), this stage has been completed previously. Skip to the checkpoint verification step.

Report: "Stage 1f: [N] sources to synthesize ([M] full-text, [K] abstract-only, [J] deep-read)"

---

## Phase 2: Spawn Synthesis Agents

Spawn 3 agents **in parallel**. Each agent reads all source extracts and writes to its own dedicated output file — no shared file writes, no collision risk.

**Model**: `claude-opus-4-6[1m]` — all three agents require deep reasoning across the full bibliography.

**Resume handling**: Track completed agents in `.paper-state.json` under `stages.literature_synthesis.agents_completed`. After each agent completes, update the list. If the pipeline is interrupted and resumed, only spawn agents for names NOT in `agents_completed`.

---

### Agent 1: Consensus & Conflict Mapper

**Agent prompt template** — paste the TOPIC, the source inventory, the knowledge graph contradictions output (if available), and all source extract contents:

```
You are a research analyst performing a cross-source synthesis of scientific literature.

PAPER TOPIC: [TOPIC from .paper.json]
NUMBER OF SOURCES: [N]
KNOWLEDGE GRAPH CONTRADICTIONS: [paste output of `python scripts/knowledge.py contradictions`, or "Not available" if no knowledge graph]
KNOWLEDGE GRAPH ENTITIES: [paste output of `python scripts/knowledge.py entities`, or "Not available"]

SOURCE EXTRACTS:
[Paste the full content of every file in research/sources/, separated by --- markers with the filename]

Your task: Identify what the field agrees on, where it is split, and what remains genuinely contested. Produce a structured conflict map.

## Analysis Strategy

1. **Extract major claims** — from all source extracts, identify every major empirical finding, theoretical claim, or methodological assertion. Group claims by theme or research question.

2. **Map agreement and disagreement** — for each major claim or theme:
   - Which sources AGREE? (list BibTeX keys)
   - Which sources DISAGREE or present conflicting evidence? (list BibTeX keys)
   - Is the disagreement about the finding itself, its interpretation, its scope, or its methodology?
   - Is this a settled question, an active debate, or an emerging tension?

3. **Assess evidence weight** — when sources conflict, note which side has stronger evidence:
   - More sources? More recent sources? Higher-quality methodology?
   - Full-text vs. abstract-only access (we may be missing nuance from abstract-only sources)?

4. **Flag suspicious consensus** — if ALL sources agree on everything, note this explicitly. Real fields have disagreements. Either the bibliography is too narrow (only one school of thought is represented) or disagreements exist but are not captured in the current source extracts.

## Output

Write the complete analysis to `research/synthesis_conflicts.md` with this structure:

# Consensus & Conflict Map

## Settled Consensus
[Claims where the field broadly agrees, with source lists]

### [Theme/Claim 1]
- **Consensus**: [what is agreed upon]
- **Supporting sources**: [key1], [key2], [key3], ...
- **Strength of consensus**: [strong/moderate/emerging]
- **Caveats**: [any scope limitations or conditions]

## Active Debates
[Claims where sources disagree or present conflicting evidence]

### [Debate 1: descriptive title]
- **Position A**: [claim] — supported by [key1], [key2]
- **Position B**: [claim] — supported by [key3], [key4]
- **Nature of disagreement**: [empirical conflict / interpretive difference / scope disagreement / methodological dispute]
- **Evidence balance**: [which side has stronger evidence and why]
- **Implications for our paper**: [how this affects thesis formulation]

## Emerging Tensions
[Areas where disagreement is implicit or beginning to surface]

## Gaps in Coverage
[Areas where the bibliography represents only one perspective, or where key positions may be missing]

## Provenance Logging

Append one entry to research/provenance.jsonl:
{"ts":"[ISO-8601]","stage":"1f","agent":"synthesis-conflicts","action":"research","target":"synthesis_conflicts","reasoning":"Cross-source conflict analysis across [N] sources for [TOPIC]","sources":["[all bibtex keys]"],"diff_summary":"Produced consensus/conflict map identifying [X] consensus areas, [Y] active debates, [Z] emerging tensions"}
```

---

### Agent 2: Methodological Critique

**Agent prompt template** — paste the TOPIC, the source inventory, and all source extract contents:

```
You are a research methodologist evaluating the quality of evidence in a scientific bibliography.

PAPER TOPIC: [TOPIC from .paper.json]
NUMBER OF SOURCES: [N]

SOURCE EXTRACTS:
[Paste the full content of every file in research/sources/, separated by --- markers with the filename]

Your task: Evaluate the methodological quality of each major cited source and identify which evidence in the bibliography is strong and which is weak. The planning stage needs to know which sources can bear argumentative weight and which cannot.

## Analysis Strategy

1. **For each source with sufficient information** (full-text or detailed abstract), evaluate:
   - **Study design**: What type of study is this? (RCT, observational, case study, theoretical, computational, survey, meta-analysis, review, etc.)
   - **Sample/data adequacy**: Is the sample size sufficient? Is the data representative? Are there selection biases?
   - **Internal validity**: Are confounds controlled? Are the methods appropriate for the claims made?
   - **External validity**: Do findings generalize beyond the specific study context?
   - **Replication status**: Have results been independently replicated? Are they consistent with other work?
   - **Methodological transparency**: Are methods described with enough detail to reproduce?

2. **For abstract-only sources**, note that methodology cannot be fully assessed and flag any claims from these sources that depend on methodological details not available in the abstract.

3. **Identify the strongest evidence** — which 3-5 sources have the most rigorous methodology and should anchor the paper's arguments?

4. **Identify the weakest evidence** — which sources have methodological limitations that the paper should acknowledge? Flag any source the pipeline is currently treating as strong evidence but which has notable weaknesses.

5. **Cross-source methodological patterns** — are there systematic methodological issues across the bibliography? (e.g., all studies use the same dataset, no studies control for a key confound, no longitudinal evidence)

## Output

Write the complete analysis to `research/synthesis_methods.md` with this structure:

# Methodological Critique

## Source Assessment Table

| Source | Type | Design | Sample | Validity | Replication | Transparency | Overall | Notes |
|-|-|-|-|-|-|-|-|-|
| [key1] | FULL-TEXT | [design] | [adequate/limited/unclear] | [high/moderate/low] | [replicated/unreplicated/N/A] | [high/moderate/low] | [strong/moderate/weak/unassessable] | [key limitation] |

## Strongest Evidence
[Narrative assessment of the 3-5 most methodologically rigorous sources and why they should anchor the paper]

## Weakest Evidence
[Sources with notable methodological limitations, especially any currently treated as strong evidence by the pipeline]

## Systematic Methodological Gaps
[Patterns of weakness across the bibliography — missing study types, shared confounds, dataset monoculture, etc.]

## Recommendations for Planning
[How methodology assessment should inform thesis formulation and claims — which claims can be made strongly, which need hedging, which need additional evidence]

## Provenance Logging

Append one entry to research/provenance.jsonl:
{"ts":"[ISO-8601]","stage":"1f","agent":"synthesis-methods","action":"research","target":"synthesis_methods","reasoning":"Methodological critique of [N] sources for [TOPIC], assessing evidence quality and identifying strongest/weakest evidence","sources":["[all bibtex keys]"],"diff_summary":"Produced methodology assessment table for [N] sources: [X] strong, [Y] moderate, [Z] weak, [W] unassessable"}
```

---

### Agent 3: Framework Synthesizer

**Agent prompt template** — paste the TOPIC, the source inventory, the knowledge graph entities output (if available), and all source extract contents:

```
You are a research analyst mapping the theoretical and conceptual landscape of a scientific field.

PAPER TOPIC: [TOPIC from .paper.json]
NUMBER OF SOURCES: [N]
KNOWLEDGE GRAPH ENTITIES: [paste output of `python scripts/knowledge.py entities`, or "Not available"]

SOURCE EXTRACTS:
[Paste the full content of every file in research/sources/, separated by --- markers with the filename]

Your task: Identify the competing theoretical frameworks, paradigms, methodological approaches, or schools of thought represented in the bibliography. Produce a taxonomy that maps every source to a framework and identifies where frameworks fail, overlap, or could be synthesized.

## Analysis Strategy

1. **Identify frameworks** — read across all sources and identify distinct:
   - Theoretical frameworks (conceptual models, theories, paradigms)
   - Methodological approaches (families of methods, analytical traditions)
   - Research programs (groups of researchers pursuing the same questions with the same assumptions)
   - Taxonomies or categorization schemes used in the field

2. **Map sources to frameworks** — for each identified framework:
   - Which sources explicitly adopt it?
   - Which sources implicitly work within it (use its assumptions without naming it)?
   - Which sources critique it or propose alternatives?

3. **Compare frameworks** — for each pair of competing frameworks:
   - What are the key differences in assumptions, methods, or conclusions?
   - Are they complementary (address different aspects), competing (make incompatible predictions), or nested (one is a special case of the other)?
   - Where does the taxonomy break down? (sources that don't fit neatly, hybrid approaches)

4. **Identify gaps and opportunities** — based on the framework analysis:
   - Are there frameworks that haven't been applied to this specific topic but could be?
   - Are there synthesis opportunities where combining frameworks could produce novel insight?
   - Are there framework limitations that the paper could address?
   - If the knowledge graph entities include concepts not covered by any framework, note these as potential blind spots.

## Output

Write the complete analysis to `research/synthesis_frameworks.md` with this structure:

# Framework & Paradigm Synthesis

## Identified Frameworks

### [Framework 1: descriptive name]
- **Core assumptions**: [key assumptions]
- **Key methods**: [characteristic methods]
- **Sources**: [key1], [key2], [key3]
- **Strengths**: [what this framework explains well]
- **Limitations**: [what it misses or gets wrong]

### [Framework 2: descriptive name]
...

## Framework Taxonomy

[A structured comparison — table or narrative — showing how frameworks relate to each other: competing, complementary, nested, or orthogonal]

## Source-Framework Map

| Source | Primary Framework | Secondary | Notes |
|-|-|-|-|
| [key1] | [framework] | [if any] | [hybrid, bridges two frameworks, etc.] |

## Gaps and Opportunities

### Unapplied Frameworks
[Frameworks from adjacent fields that could illuminate this topic]

### Synthesis Opportunities
[Where combining frameworks could produce novel contributions — this feeds directly into Stage 2 thesis formulation]

### Framework Failures
[Where existing frameworks fail to explain observed phenomena, producing openings for new theory]

## Provenance Logging

Append one entry to research/provenance.jsonl:
{"ts":"[ISO-8601]","stage":"1f","agent":"synthesis-frameworks","action":"research","target":"synthesis_frameworks","reasoning":"Framework and paradigm synthesis across [N] sources for [TOPIC], identifying [X] frameworks and mapping source affiliations","sources":["[all bibtex keys]"],"diff_summary":"Produced framework taxonomy with [X] frameworks, source-framework map, and [Y] gaps/opportunities identified"}
```

---

## Phase 3: Integration

After all three agents complete:

1. **Read all synthesis files** — read `research/synthesis_conflicts.md`, `research/synthesis_methods.md`, and `research/synthesis_frameworks.md` in full.

2. **Build the unified literature synthesis** — create `research/literature_synthesis.md` that integrates all three analyses into a single reference document for Stage 2. Structure:

   ```markdown
   # Literature Synthesis

   **Paper topic**: [TOPIC]
   **Sources analyzed**: [N] ([M] full-text, [K] abstract-only)
   **Date**: [ISO-8601]

   ## 1. Field Consensus
   [What the field agrees on — major claims with consensus, drawn from synthesis_conflicts.md.
   For each consensus item, note the evidence strength from synthesis_methods.md.]

   ## 2. Active Debates and Conflicts
   [Where the field is split — drawn from synthesis_conflicts.md.
   For each debate, note which side has stronger methodology from synthesis_methods.md.
   Note which frameworks from synthesis_frameworks.md are driving each side.]

   ## 3. Evidence Quality Landscape
   [Summary of methodological assessment — which sources are strongest, which are weakest.
   Systematic gaps. How this should constrain the paper's claims.]

   ## 4. Competing Frameworks
   [Summary of framework taxonomy and how it maps onto the debates.
   Which framework does this paper's likely contribution fit within?]

   ## 5. Gaps and Opportunities
   [Unified list from all three analyses — what the field is missing, where existing
   frameworks fail, what methodology would strengthen the area, where synthesis
   could create new insight. These feed directly into thesis formulation in Stage 2.]

   ## 6. Recommendations for Planning
   [Concrete guidance for Stage 2:
   - Which thesis directions are well-supported by the evidence?
   - Which directions lack sufficient evidence and would require hedging?
   - Which sources should anchor the argument? Which should be cited with caveats?
   - What framework positioning would maximize the contribution?
   - What reviewer objections are predictable from the conflict map?]
   ```

3. **Knowledge graph update** (if `research/knowledge/` exists, skip silently if not):
   ```bash
   python scripts/knowledge.py update
   ```
   Run with `run_in_background: true` — the synthesis files add new relationships and entities to the graph.

4. **Update source manifest**:
   ```bash
   python3 scripts/update-manifest.py
   ```

5. **Log integration provenance** — append to `research/provenance.jsonl`:
   ```json
   {"ts":"[ISO-8601]","stage":"1f","agent":"synthesis-integrator","action":"research","target":"literature_synthesis","reasoning":"Integrated conflict map, methodological critique, and framework synthesis into unified literature synthesis for [TOPIC]","sources":["[all bibtex keys]"],"diff_summary":"Produced literature_synthesis.md: [X] consensus items, [Y] debates, [Z] frameworks, [W] gaps/opportunities"}
   ```

---

## Checkpoint

Update `.paper-state.json`:
```json
"literature_synthesis": {
  "done": true,
  "completed_at": "...",
  "sources_analyzed": N,
  "agents_completed": ["synthesis-conflicts", "synthesis-methods", "synthesis-frameworks"],
  "agents_pending": [],
  "outputs": [
    "research/synthesis_conflicts.md",
    "research/synthesis_methods.md",
    "research/synthesis_frameworks.md",
    "research/literature_synthesis.md"
  ]
}
```

Update `.paper-progress.txt`: "Stage 1f complete: literature synthesis across [N] sources — [X] consensus items, [Y] active debates, [Z] frameworks identified"

> **Next**: Proceed to **Stage 2: Thesis, Contribution & Outline** (`pipeline/stage-2-planning.md`), which reads `research/literature_synthesis.md` as primary input for thesis formulation and claims-evidence matrix construction.
