# Knowledge — Query the Research Knowledge Graph

Interact with the per-paper knowledge graph built from source extracts using LightRAG.

## Prerequisites

- Source extracts must exist in `research/sources/` (created by the research pipeline or `/search-literature`)
- `OPENROUTER_API_KEY` must be set in the environment
- The graph must be built first (this command will build it if needed)

## Instructions

**Availability check** — before running any operation, verify prerequisites:
1. Check if `OPENROUTER_API_KEY` is set: `[ -n "$OPENROUTER_API_KEY" ] && echo "OK" || echo "MISSING"`
2. If MISSING: tell the user "Knowledge graph requires OPENROUTER_API_KEY. Set it with: export OPENROUTER_API_KEY=your-key (get a key at https://openrouter.ai/keys)" and stop. Do not attempt to run knowledge.py commands.
3. Check if lightrag is installed: `python3 -c "import lightrag" 2>/dev/null && echo "OK" || echo "MISSING"`
4. If lightrag MISSING: tell the user "lightrag not installed. Run: pip install lightrag-hku" and stop.

Parse $ARGUMENTS to determine the operation. If no arguments, show a status summary.

### Operations

**Build or rebuild the knowledge graph:**
```bash
python scripts/knowledge.py build
```
Run this after adding new source extracts or when the graph is stale.

**Start streaming ingestion worker (for long sessions):**
```bash
python scripts/knowledge.py serve
```
Run with `run_in_background: true`. Starts a long-running worker that processes queued files. Use this instead of `build` when sources will arrive incrementally.

**Enqueue files for ingestion:**
```bash
python scripts/knowledge.py enqueue research/sources/*.md
python scripts/knowledge.py enqueue attachments/parsed/*.md
python scripts/knowledge.py enqueue --reindex research/sources/*.md  # force re-ingestion
```
Instant — appends to the queue. The worker processes files in priority order (source extracts first).

**Check ingestion status:**
```bash
python scripts/knowledge.py status
```
Shows pending/done/failed counts and whether the worker is alive.

**Wait for ingestion to complete:**
```bash
python scripts/knowledge.py drain
python scripts/knowledge.py drain --timeout 300  # fail after 5 minutes
```

**Stop the worker:**
```bash
python scripts/knowledge.py stop
```

**Query the knowledge graph:**
```bash
python scripts/knowledge.py query "your question here"
```
Use for freeform semantic search across all sources. Returns synthesized answers with source citations.

**Find contradictions across sources:**
```bash
python scripts/knowledge.py contradictions
```
Identifies conflicting claims, intellectual tensions, and unresolved debates. Output saved to `research/knowledge_contradictions.md`.

**Find evidence supporting a claim:**
```bash
python scripts/knowledge.py evidence-for "the specific claim"
```
Returns sources and findings that support the claim. Useful when building the claims-evidence matrix.

**Find evidence against a claim:**
```bash
python scripts/knowledge.py evidence-against "the specific claim"
```
Returns sources and findings that challenge or contradict the claim. Useful for writing the limitations/discussion section.

**List all entities in the graph:**
```bash
python scripts/knowledge.py entities
```
Shows all extracted concepts, theories, methods, papers, authors, etc. grouped by type.

**Show relationships for an entity:**
```bash
python scripts/knowledge.py relationships "entity name"
```
Shows how a concept connects to other entities in the knowledge graph.

### If the graph doesn't exist yet

1. Check that `research/sources/` has files: `ls research/sources/`
2. If empty, run `/search-literature` or `/write-paper` first to generate source extracts
3. Build the graph: `python scripts/knowledge.py build`
4. Then run the requested operation

### Error Handling

- If `OPENROUTER_API_KEY` is not set: the availability check above catches this. The script also exits gracefully (exit 0) with a helpful message, so it will not crash.
- If `scripts/knowledge.py` is not found, the template may not have been updated — check if the file exists
- If lightrag is not installed: `pip install lightrag-hku`
- All knowledge.py commands exit 0 (not crash) when OPENROUTER_API_KEY is missing, printing a clear explanation. This prevents bash `&&` chains from breaking.

## Arguments

$ARGUMENTS

If no arguments given, show the status: whether the graph exists, how many entities/relationships, when it was last built.
