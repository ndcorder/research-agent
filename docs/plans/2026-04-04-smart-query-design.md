# Smart Knowledge Graph Query

**Date:** 2026-04-04
**Status:** Design approved
**Scope:** `template/scripts/knowledge.py` — replace the current `query` subcommand

## Problem

The current `query` subcommand is a dumb pipe: question in, LLM synthesis out. This causes two failures in practice:

1. **Missed entities.** LightRAG's hybrid mode extracts keywords from the query and searches for matching entities. A query like `"Tell me about 'Toward a Stewardship Theory of Management'"` gets decomposed into generic keywords (`Paper`, `Management model`) that miss the actual entity. The paper exists in the graph but the answer says "I don't have enough information."

2. **No multi-step reasoning.** Pipeline stages need to find a paper, trace its connections, check for contradictions, and verify against source extracts — but each of those is a separate `knowledge.py` call with separate LLM synthesis, producing redundant or contradictory answers.

## Solution

Replace the `query` subcommand with a 3-phase smart query pipeline that separates retrieval from synthesis using LightRAG's `aquery_data()` API.

### Phase 1: Entity pre-flight

Before any retrieval, inspect the graph directly:

1. **Extract candidate names** from the query:
   - Quoted strings get highest priority (`'Toward a Stewardship Theory'`)
   - Remaining noun-phrase heuristics (capitalized sequences, known patterns like `Author2024`)
   - No NLP dependency — regex/heuristics cover 90% of pipeline queries

2. **Search the entity index** for matches:
   - Exact substring match against entity names (fast, from loaded graphml)
   - Cosine similarity against entity embeddings via `vdb_entities.json` (already loaded)
   - Return top-K matches with scores

3. **Pull relationships** for matched entities directly from the graph — these are structured facts that bypass LightRAG's retrieval entirely.

### Phase 2: Pattern-aware multi-strategy retrieval

Classify the query into a research pattern and pick retrieval strategies:

| Pattern | Detection | Strategies |
|-|-|-|
| Specific paper/author | Quoted title, "paper by X", bibtex key pattern | Entity lookup + naive |
| Theory/concept exploration | "What is X", "approaches to" | Entity lookup + hybrid + naive |
| Evidence query | "evidence for/against", "supports" | Entity pre-flight on claim concepts + hybrid |
| Broad survey | "What do sources say", "state of" | Hybrid + naive |
| Contradiction/tension | "contradictions", "disagree" | Global + entity relationships |
| Default | Unrecognized | Hybrid + naive |

For each strategy, call `aquery_data(query, QueryParam(mode=...))` which returns raw `{entities, relationships, chunks, references}` **without** an LLM call.

Run strategies concurrently with `asyncio.gather()`.

### Phase 3: Merge, synthesize, output

1. **Merge** all raw results: union entities, relationships, and chunks across modes. Deduplicate by entity/chunk ID.

2. **Inject pre-flight context**: prepend matched entities and their direct relationships as structured facts at the top of the context, so the synthesis LLM cannot miss them.

3. **Single LLM synthesis call**: assemble the merged context and call the query model (Gemini Flash via OpenRouter, 1M context) with a research-aware system prompt. One call regardless of how many strategies ran — same cost as today.

4. **Structured output**:

```
## Query Results

**Confidence:** HIGH | 3 entities matched, 2 modes contributed
**Matched entities:** Stewardship Theory, Davis1997, Donaldson1991
**Sources:** davis1997.md, donaldson1991.md, jensen1976.md

### Answer

[LLM synthesis]

### Entity Context

- Stewardship Theory → CONTRASTS_WITH → Agency Theory
- Davis1997 → PROPOSES → Stewardship Theory
- Davis1997 → CHALLENGES → Jensen1976
```

**Confidence levels:**
- `HIGH`: 2+ entity matches AND 2+ modes contributed chunks
- `MEDIUM`: 1 entity match OR only 1 mode contributed
- `LOW`: No entity matches, sparse chunks

## API: `aquery_data()`

LightRAG v1.4.13 provides clean retrieval/synthesis separation:

```python
from lightrag import LightRAG, QueryParam

# Retrieval only — no LLM call
data = await rag.aquery_data(query, QueryParam(mode="hybrid"))
# Returns: {"status": "success", "data": {"entities": [...], "relationships": [...], "chunks": [...], "references": [...]}}

# Full pipeline (retrieval + LLM)
result = await rag.aquery(query, QueryParam(mode="hybrid"))
```

Internally, `aquery_data()` sets `only_need_context=True` on QueryParam, which short-circuits the LLM call in `kg_query`/`naive_query`.

For synthesis after merging, we call the query LLM directly (same `openai_complete` function already used elsewhere in knowledge.py) with the assembled context.

## What changes

### `knowledge.py` modifications

- `cmd_query()`: replace current implementation with the 3-phase pipeline
- New helper: `_entity_preflight(rag, query) -> list[EntityMatch]`
- New helper: `_classify_query(query) -> QueryPattern`
- New helper: `_multi_retrieve(rag, query, pattern) -> MergedContext`
- New helper: `_synthesize(merged_context, query) -> str`
- `_cached_query()`: still used for caching, but now caches the final structured output

### `evidence-for`, `evidence-against`, `contradictions`

These commands also benefit from entity pre-flight. Add pre-flight to extract claim concepts and verify they exist as entities before querying. The rest of their logic (specialized prompts) stays the same.

### No changes needed

- Pipeline stage files — they already call `knowledge.py query "..."`, same interface
- Build/update/serve/enqueue — ingestion is unaffected
- entities/relationships subcommands — already direct graph access

## RAG-Anything

Evaluated and rejected. RAG-Anything is a multimodal *ingestion* wrapper (images, tables, equations). Its query layer is a passthrough to LightRAG's `aquery()`. Adds no retrieval flexibility, just extra dependencies (MinerU, VLM). Not useful for this work.

## Future: Agent-orchestrated queries (Phase 2)

For complex multi-step reasoning ("find paper X, trace connections to Y, check contradictions, verify against source extracts"), a Claude agent (Sonnet 1M) can orchestrate `knowledge.py` primitives as tools. This is a separate effort — the smart query pipeline handles the common case; the agent handles the long-tail.

## Logging

LightRAG's verbose logging (INFO from lightrag, nano-vectordb, httpx, openai) is redirected to `research/knowledge/lightrag.log`. Console only shows ERROR+ by default. Override with `LIGHTRAG_LOG_LEVEL=DEBUG`.
