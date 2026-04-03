# Knowledge Graph Reference

The knowledge graph system (`template/scripts/knowledge.py`) uses [LightRAG](https://github.com/HKUDS/LightRAG) to build a queryable entity-relationship graph from research source material. It powers the `/knowledge` slash command and is used by several pipeline stages for semantic search, contradiction detection, and evidence retrieval.

All LLM and embedding calls route through OpenRouter (`OPENROUTER_API_KEY`).

## How it works

### Ingestion pipeline (build / update / serve)

```
Documents (source extracts, prepared docs, parsed PDFs, raw PDFs)
  |
  |  ainsert() accepts a batch of documents
  |
  v
[1] CHUNKING (CPU-only, fast)
    Split each document into chunks of CHUNK_TOKEN_SIZE tokens
    with CHUNK_OVERLAP_TOKEN_SIZE token overlap.
    Small source extracts (~1-2k tokens) become 1 chunk.
    Full PDFs (50k+ tokens) become many chunks.
  |
  v
[2] STAGE 1 — parallel per document (capped by MAX_PARALLEL_INSERT)
    |-- Embed each chunk via embedding model  -->  chunks_vdb (vector store)
    |-- Store chunk text                      -->  text_chunks (KV store)
    |-- Update doc processing status          -->  doc_status (KV store)
  |
  v
[3] STAGE 2 — entity extraction (THE BOTTLENECK)
    For each chunk (up to LLM_MAX_ASYNC concurrent):
      |-- LLM extracts (entity, type, description) tuples
      |-- LLM extracts (source, target, relationship) tuples
      |-- If MAX_GLEANING > 0: LLM re-reads chunk for missed entities
  |
  v
[4] MERGE — per entity/relation
    |-- If < FORCE_LLM_SUMMARY_ON_MERGE descriptions: concatenate (no LLM)
    |-- If >= threshold: LLM summarizes via map-reduce (recursive)
    |-- Upsert entity/relation to graph + embed into vector DB
  |
  v
[5] FLUSH — persist all storage to disk
```

### Where time goes

| Phase | % of wall time | Bottleneck |
|-|-|-|
| Chunking | ~0% | CPU only |
| Chunk embedding (Stage 1) | ~10-15% | `EMBEDDING_BATCH_NUM`, `EMBEDDING_FUNC_MAX_ASYNC` |
| Entity extraction LLM calls | ~60-70% | `LLM_MAX_ASYNC` (concurrent calls per document) |
| Merge summarization | ~10-20% | Only triggers when entity has many descriptions |
| Entity/relation embedding | ~5-10% | Same embedding pool as chunk embedding |

### Effective concurrency

Total concurrent LLM calls during ingestion:

```
min(batch_size, MAX_PARALLEL_INSERT) x min(chunks_per_doc, LLM_MAX_ASYNC)
```

The `serve` worker batches up to `WORKER_BATCH_SIZE` pending files into a single `ainsert()` call so that `MAX_PARALLEL_INSERT` is actually utilized. Without batching (batch size = 1), only one document is processed at a time and `MAX_PARALLEL_INSERT` is wasted.

### Query pipeline

```
User query
  |
  v
[1] KEYWORD EXTRACTION (1 LLM call)
    Extract high-level and low-level keywords to guide graph traversal.
  |
  v
[2] RETRIEVAL (no LLM, uses vector DB + graph)
    |-- Find matching entities/relations via embedding similarity
    |-- Traverse graph neighborhood
    |-- Retrieve related text chunks
    |-- Mode determines strategy: local, global, hybrid, naive, mix
  |
  v
[3] RESPONSE GENERATION (1 LLM call)
    Synthesize final answer from retrieved context.
    Uses QUERY_LLM_MODEL if set, otherwise falls back to LLM_MODEL.
```

## Model selection guide

Different pipeline stages have different model requirements. You can (and should) use different models for ingestion vs. queries.

### Ingestion models

| Stage | What it does | Model need | Recommendation |
|-|-|-|-|
| Chunk embedding | Turns text into dense vectors | High-recall semantic similarity, not generative | `qwen/qwen3-embedding-8b` (current default). Alternatives: `nomic-embed-text-v1.5`, `voyage-3-large` |
| Entity extraction | Structured `(entity, type, description)` and `(src, tgt, relation)` output | Fast, cheap, good instruction-following. Does NOT need creativity or deep reasoning | Flash-tier: `google/gemini-3-flash-preview` (default), `gpt-4o-mini`, `deepseek-v3-0324`. Key metric is tokens/sec |
| Gleaning | Re-reads chunk + prior extraction, finds missed entities | Same as extraction, slightly harder | Same model. Consider `MAX_GLEANING=0` for well-structured source extracts, `1` for raw PDFs |
| Merge summarization | Condenses 20+ descriptions of the same entity into one | Coherent summarization, moderate intelligence | Flash-tier is fine. Rarely fires for small corpora |

### Query models

| Stage | What it does | Model need | Recommendation |
|-|-|-|-|
| Keyword extraction | Extracts search terms from user query | Short structured output | Flash-tier (same as ingestion model) |
| Response generation | Synthesizes answer from retrieved context | **Reasoning, synthesis, nuance, citation accuracy** | **This is where a smarter model pays off.** One call, so cost is low. Use `anthropic/claude-sonnet-4`, `google/gemini-2.5-pro`, or `openai/gpt-4o` |

### Configuring separate models

```bash
# Fast model for bulk extraction during ingestion
export LIGHTRAG_LLM_MODEL="google/gemini-3-flash-preview"

# Smart model for answering questions
export LIGHTRAG_QUERY_LLM_MODEL="anthropic/claude-sonnet-4"
```

If `LIGHTRAG_QUERY_LLM_MODEL` is unset or empty, all operations use `LIGHTRAG_LLM_MODEL`.

## Ingestion modes

### Batch (build / update)

```bash
python scripts/knowledge.py build    # Full rebuild from all sources
python scripts/knowledge.py update   # Incremental (new/changed files only)
```

`build` reads all documents at once and submits them as a single `ainsert()` call. `update` checks file modification times against the last build timestamp.

### Queue-based streaming (serve / enqueue)

```bash
python scripts/knowledge.py serve                  # Start background worker
python scripts/knowledge.py enqueue file [file...]  # Queue files (instant)
python scripts/knowledge.py enqueue --reindex file  # Force re-ingestion
python scripts/knowledge.py status                  # Show queue state
python scripts/knowledge.py drain [--timeout N]     # Block until queue empty
python scripts/knowledge.py stop                    # Graceful shutdown
```

The worker collects up to `WORKER_BATCH_SIZE` pending files per cycle and ingests them as a single batch. Files are prioritized: source extracts > prepared docs > parsed markdown > raw PDFs.

### Document priority (ingestion order)

| Priority | Source | Path |
|-|-|-|
| 1 (highest) | Curated source extracts | `research/sources/*.md` |
| 2 | Structured claims/methodology | `research/prepared/**/*.md` |
| 3 | Docling-parsed full-text | `attachments/parsed/*.md` |
| 4 (lowest) | Raw PDF fallback | `attachments/*.pdf` |

When both a parsed markdown and raw PDF exist for the same stem, the parsed version is used and the PDF is skipped.

## Query modes

Pass `--mode` to the `query` subcommand, or set `LIGHTRAG_DEFAULT_QUERY_MODE`.

| Mode | Strategy | Best for |
|-|-|-|
| `local` | Entity-centric: finds entities matching the query, returns their descriptions and neighborhood | Specific factual questions ("What method did X use?") |
| `global` | Relationship-centric: traverses the full graph for broad patterns | Big-picture questions ("What contradictions exist?") |
| `hybrid` | Combines local + global | General-purpose (default) |
| `naive` | Vector search only, no graph traversal | Quick similarity search, baseline comparison |
| `mix` | Knowledge graph + vector retrieval integrated | LightRAG's recommended mode for best quality |

## Environment variables reference

All tunables are set via environment variables with `LIGHTRAG_` prefix. The defaults shown are the current values in `knowledge.py`.

### Models

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_LLM_MODEL` | `google/gemini-3-flash-preview` | LLM for ingestion (extraction, merge, summarization) |
| `LIGHTRAG_QUERY_LLM_MODEL` | *(empty = use LLM_MODEL)* | LLM for query response generation |
| `LIGHTRAG_EMBEDDING_MODEL` | `qwen/qwen3-embedding-8b` | Embedding model for chunks, entities, relations |
| `LIGHTRAG_EMBEDDING_DIM` | `4096` | Embedding vector dimensions (must match model) |
| `LIGHTRAG_EMBEDDING_LENGTH` | `32000` | Max input tokens for embedding model |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API base URL |

### Concurrency

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_MAX_PARALLEL_INSERT` | `20` | Max documents processed concurrently in a single `ainsert()` |
| `LIGHTRAG_MAX_ASYNC` | `32` | Max concurrent LLM calls per document (entity extraction) |
| `LIGHTRAG_EMBEDDING_BATCH_NUM` | `16` | Texts per embedding API call |
| `LIGHTRAG_EMBEDDING_FUNC_MAX_ASYNC` | `16` | Max concurrent embedding API calls |

### Chunking

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_CHUNK_TOKEN_SIZE` | `8000` | Max tokens per chunk. Larger = fewer LLM calls, but extraction quality may degrade past ~12k |
| `LIGHTRAG_CHUNK_OVERLAP_TOKEN_SIZE` | `100` | Overlap between consecutive chunks. Higher preserves more cross-boundary context |
| `LIGHTRAG_TIKTOKEN_MODEL` | `gpt-4o-mini` | Tokenizer model for chunk splitting |

### Entity extraction

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_MAX_GLEANING` | `1` | Extra extraction passes per chunk. `0` = one pass (2x faster), `1` = two passes (better recall) |
| `LIGHTRAG_MAX_EXTRACT_INPUT_TOKENS` | `20480` | Max tokens fed into a single extraction call |
| `LIGHTRAG_FORCE_SUMMARY_ON_MERGE` | `20` | Descriptions threshold before LLM re-summarizes. Higher = fewer LLM calls during merge |
| `LIGHTRAG_ENTITY_TYPES` | *(default list)* | Comma-separated entity types to extract. Default: Person, Creature, Organization, Location, Event, Concept, Method, Content, Data, Artifact, NaturalObject |

### Summary generation

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_SUMMARY_MAX_TOKENS` | `1200` | Max tokens for entity/relation descriptions |
| `LIGHTRAG_SUMMARY_CONTEXT_SIZE` | `12000` | Max context tokens for summary LLM calls |
| `LIGHTRAG_SUMMARY_LENGTH_RECOMMENDED` | `600` | Target summary length in tokens |
| `LIGHTRAG_SUMMARY_LANGUAGE` | `English` | Language for generated summaries |

### Query and retrieval

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_TOP_K` | `40` | Entities/relations retrieved per query |
| `LIGHTRAG_CHUNK_TOP_K` | `20` | Text chunks retrieved per query |
| `LIGHTRAG_MAX_ENTITY_TOKENS` | `6000` | Token budget for entity context in query |
| `LIGHTRAG_MAX_RELATION_TOKENS` | `8000` | Token budget for relation context in query |
| `LIGHTRAG_MAX_TOTAL_TOKENS` | `30000` | Total token budget for query context |
| `LIGHTRAG_COSINE_THRESHOLD` | `0.2` | Min cosine similarity for retrieval. Raise to filter noise, lower for wider net |
| `LIGHTRAG_RELATED_CHUNK_NUMBER` | `5` | Chunks grabbed per entity/relation match |
| `LIGHTRAG_KG_CHUNK_PICK_METHOD` | `VECTOR` | `VECTOR` (embedding similarity) or `WEIGHT` (graph-edge weight) |
| `LIGHTRAG_DEFAULT_QUERY_MODE` | `hybrid` | Default mode for `query` subcommand |

### Graph size limits

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_MAX_GRAPH_NODES` | `10000` | Max nodes returned in knowledge graph queries |
| `LIGHTRAG_MAX_SOURCE_IDS_PER_ENTITY` | `300` | Source chunk IDs stored per entity |
| `LIGHTRAG_MAX_SOURCE_IDS_PER_RELATION` | `300` | Source chunk IDs stored per relation |
| `LIGHTRAG_SOURCE_IDS_LIMIT_METHOD` | `FIFO` | `FIFO` (drop oldest) or `IGNORE_NEW` when limit hit |
| `LIGHTRAG_MAX_FILE_PATHS` | `10000` | Max file paths stored per entity/relation |

### Caching

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_ENABLE_LLM_CACHE` | `true` | Cache LLM responses to avoid redundant calls |
| `LIGHTRAG_ENABLE_LLM_CACHE_FOR_EXTRACT` | `true` | Cache entity extraction specifically. Disable for non-deterministic experiments |
| `LIGHTRAG_EMBEDDING_CACHE_ENABLED` | `true` | Cache embeddings by similarity. Saves API calls for near-duplicate text |
| `LIGHTRAG_EMBEDDING_CACHE_SIMILARITY` | `0.95` | Similarity threshold for embedding cache hits |

### Timeouts

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_LLM_TIMEOUT` | `600` | Seconds before LLM call times out |
| `LIGHTRAG_EMBEDDING_TIMEOUT` | `600` | Seconds before embedding call times out |

### Worker

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_WORKER_POLL_INTERVAL` | `2.0` | Seconds between queue polls when idle |
| `LIGHTRAG_WORKER_STOP_TIMEOUT` | `30` | Seconds to wait for graceful shutdown |
| `LIGHTRAG_DRAIN_POLL_INTERVAL` | `5.0` | Seconds between drain status checks |
| `LIGHTRAG_WORKER_BATCH_SIZE` | `10` | Files batched per `ainsert()` call. Higher = better parallelism. `1` = legacy one-at-a-time |

### Storage

| Variable | Default | Description |
|-|-|-|
| `LIGHTRAG_STORAGE` | `file` | `file` (JSON + GraphML on disk) or `opensearch` (OpenSearch cluster) |

For OpenSearch, also set: `OPENSEARCH_HOSTS`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD`, `OPENSEARCH_USE_SSL`.

## Performance tuning

### Speed up ingestion

**Highest impact:**
1. **Batch ingestion** (`WORKER_BATCH_SIZE`): Set to 10+ so multiple documents are processed concurrently via `MAX_PARALLEL_INSERT`. A batch of 10 single-chunk source extracts runs 10 extraction calls in parallel instead of 1.
2. **Raise `LLM_MAX_ASYNC`**: If your OpenRouter plan allows, go to 32-64. This is the number of concurrent LLM calls per document's chunks. Matters most for PDFs with many chunks.
3. **Set `MAX_GLEANING=0`**: Cuts entity extraction LLM calls in half. Safe for well-structured source extracts. Keep at `1` for raw PDFs.

**Moderate impact:**
4. **Increase `CHUNK_TOKEN_SIZE`**: Fewer chunks = fewer LLM calls. Diminishing returns past ~8000. Watch extraction quality.
5. **Raise `FORCE_SUMMARY_ON_MERGE`**: Reduces hidden LLM summarization calls during graph construction. Set higher (e.g., 30-50) if you prefer fast ingestion over polished entity descriptions.
6. **Use a faster LLM**: Entity extraction is structured output, not creative writing. Optimize for tokens/second.

### Improve query quality

1. **Use a smarter `QUERY_LLM_MODEL`**: The retrieval is already done. You're paying for one LLM call. Use the best model you can afford.
2. **Raise `TOP_K` / `CHUNK_TOP_K`**: Retrieve more context at the cost of longer prompts. Try 60/30.
3. **Lower `COSINE_THRESHOLD`**: Cast a wider retrieval net (more results, some noise). Try 0.1.
4. **Try `mix` mode**: LightRAG's recommended mode combines KG traversal + vector retrieval.
5. **Customize `ENTITY_TYPES`**: Replace the generic defaults with domain-specific types (e.g., `Protein,Gene,Pathway,Drug,ClinicalTrial,Biomarker` for biomedical papers).

### Reduce costs

1. **Enable all caches**: `ENABLE_LLM_CACHE=true`, `ENABLE_LLM_CACHE_FOR_EXTRACT=true`, `EMBEDDING_CACHE_ENABLED=true`. Avoids redundant API calls on re-builds and near-duplicate text.
2. **Use `update` instead of `build`**: Only processes new/changed files.
3. **Use the queue (`serve`/`enqueue`)**: Processes files as they arrive instead of re-scanning everything.
4. **Set `MAX_GLEANING=0`** for source extracts (halves extraction API calls).

## File layout

All knowledge graph state lives under `research/knowledge/` in paper projects (gitignored):

```
research/knowledge/
  graph_chunk_entity_relation.graphml   # NetworkX graph (file backend)
  vdb_chunks.json                       # Chunk vector DB
  vdb_entities.json                     # Entity vector DB
  vdb_relationships.json                # Relationship vector DB
  kv_store_full_docs.json               # Full document content
  kv_store_text_chunks.json             # Chunk text content
  kv_store_llm_response_cache.json      # LLM response cache
  .last_build                           # Timestamp of last build
  .cache/                               # Query result cache
  .queue.jsonl                          # Ingestion queue (serve mode)
  .queue_progress.json                  # Queue processing state
  .worker.pid                           # Worker process ID
  worker.log                            # Worker log
```
