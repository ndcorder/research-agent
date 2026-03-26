# Plan 04: Knowledge Graph Deep Integration

## Problem

The LightRAG knowledge graph is built after source acquisition but only queried at a few discrete points: claims matrix verification, contradiction detection before QA, and optionally during writing. It's treated as a nice-to-have rather than a core reasoning tool. The graph contains rich entity-relationship data that could systematically improve every downstream stage.

## Goal

Make the knowledge graph a first-class participant in planning, writing, and review, with structured queries at every stage where evidence matters.

## Design

### Current Query Points (keep these)

- Stage 2: `evidence-for` and `evidence-against` for claims matrix
- Stage 5a: `contradictions` before QA review
- Stage 3: Optional `query` during section writing

### New Query Points

#### Stage 2 — Thesis Development

After the gap analysis agent produces `research/gaps.md`, query the knowledge graph to validate the proposed contribution:

```bash
python scripts/knowledge.py query "What approaches have been proposed for [thesis topic]?"
python scripts/knowledge.py evidence-against "[proposed contribution statement]"
python scripts/knowledge.py contradictions
```

Feed results into the thesis development. If the graph reveals existing work that closely matches the proposed contribution, this is a novelty red flag that should be surfaced before Stage 2d (novelty check).

Also run:
```bash
python scripts/knowledge.py entities
```
Use the entity list to identify key concepts the paper MUST discuss. If an entity with many relationships isn't mentioned in the outline, it's likely a gap.

#### Stage 3 — Section Writing (make mandatory, not optional)

Before each writing agent starts, run structured queries and pass the results as context:

**For Introduction**:
```bash
python scripts/knowledge.py query "What is the current state of [topic] and what problems remain?"
python scripts/knowledge.py relationships "[main method/concept]"
```

**For Related Work**:
```bash
python scripts/knowledge.py entities  # identify all methods/approaches to organize thematically
python scripts/knowledge.py relationships "[each major approach]"  # find connections between approaches
```

**For Methods**:
```bash
python scripts/knowledge.py evidence-for "[proposed method is valid because...]"
python scripts/knowledge.py query "What are known limitations of [method components]?"
```

**For Results/Discussion**:
```bash
python scripts/knowledge.py evidence-for "[each key finding]"
python scripts/knowledge.py evidence-against "[each key finding]"
python scripts/knowledge.py contradictions  # scoped to section's sources
```

The query results are passed to the writing agent as a `## Knowledge Graph Context` section in its prompt, formatted as bullet points with source attribution.

#### Stage 5 — QA Review

Each review agent gets contradiction report + entity coverage analysis:

```bash
python scripts/knowledge.py contradictions
python scripts/knowledge.py entities
```

Add to the Technical Reviewer prompt:
```
The knowledge graph identified these contradictions across sources:
[paste contradictions]

Check whether the paper addresses these contradictions in the Discussion.
Also verify that these key entities from the graph are discussed where appropriate:
[paste entity list]
```

#### `/auto` Iterations

Before each iteration's assessment phase:
```bash
python scripts/knowledge.py contradictions  # may have new sources from previous iterations
```

Pass to the Depth & Evidence Reviewer.

### Knowledge Graph Rebuild Triggers

Currently rebuilt once after Stage 1d. Add rebuilds after:
1. Stage 2c (deep targeted research) — new papers from thesis-informed search
2. Any `/auto` iteration that adds new references
3. Manual `/ingest-papers` runs

Add to `knowledge.py`: an `update` command that only ingests new/changed source files (currently `build` reprocesses everything):

```bash
python scripts/knowledge.py update  # only ingest files newer than last build
```

Implementation: store a `.last_build` timestamp file in `research/knowledge/`. On `update`, only process source files and PDFs with mtime > last build.

### Query Result Caching

Multiple stages query the same graph within minutes. Add a simple file-based cache:
- Cache key: query string + graph modification time
- Cache location: `research/knowledge/.cache/`
- TTL: until next graph rebuild (invalidate on build/update)

This avoids redundant LLM calls for repeated queries like `contradictions`.

### Graceful Degradation

All new query points must check if `research/knowledge/` exists before querying. If the graph isn't built (no OPENROUTER_API_KEY, build failed, etc.), skip all graph queries silently. The pipeline must still work without it — but log a note: "Knowledge graph not available. Evidence quality may be reduced."

## Changes to knowledge.py

1. **New `update` command**: incremental ingestion of new/changed files
2. **Cache layer**: file-based caching of query results
3. **Entity coverage command**: `python scripts/knowledge.py coverage research/thesis.md` — cross-reference entities in the graph against a text file, report entities NOT mentioned

```python
async def cmd_coverage(args):
    """Check which graph entities appear in a document."""
    # Read the target document
    # Get all entities from graph
    # Check which entities appear in the document text
    # Report missing entities sorted by relationship count (more connected = more important)
```

## Files to Modify

1. Pipeline stage files:
   - `template/claude/pipeline/stage-2-planning.md` — Add graph queries for thesis validation and entity coverage
   - `template/claude/pipeline/stage-3-writing.md` — Make graph queries mandatory (not optional) for each section, with specific queries per section
   - `template/claude/pipeline/stage-5-qa.md` — Add entity coverage and contradictions to reviewer context
   - `template/claude/pipeline/stage-2c-targeted-research.md` — Add graph rebuild after deep targeted research
2. `template/claude/commands/auto.md`:
   - Add contradiction query before assessment phase
   - Add graph rebuild trigger after iterations that add references
3. `template/scripts/knowledge.py`:
   - Add `update` command (incremental ingestion)
   - Add `coverage` command (entity coverage check)
   - Add query caching

## Files to Create

None.

## Risks

- Graph queries add latency to every stage. Mitigation: caching + the `update` command keeps rebuilds fast.
- LightRAG query quality depends on the underlying LLM. Mitigation: use hybrid mode (combining local + global search) for all queries.
- Too much graph context could overwhelm writing agents. Mitigation: cap graph context at 500 words per section, summarize rather than dump raw results.

## Acceptance Criteria

- [ ] Graph queries are mandatory (not optional) at Stages 2, 3, and 5
- [ ] Each section type has tailored queries (not one-size-fits-all)
- [ ] `knowledge.py update` does incremental ingestion
- [ ] `knowledge.py coverage` checks entity presence in documents
- [ ] Query results are cached until next rebuild
- [ ] Graph rebuilds after Stage 2c and after `/auto` iterations that add references
- [ ] All graph queries degrade gracefully if graph is unavailable
- [ ] Writing agents receive graph context capped at 500 words
