# Post-Ingestion Knowledge Graph Enrichment

**Date:** 2026-04-04
**Status:** Design approved
**Scope:** `template/scripts/knowledge.py` — new `enrich` subcommand + integration into `build`/`update`

## Problem

LightRAG's LLM-based entity extraction misses structured bibliographic facts that are trivially parseable from existing project files. Paper titles, author names, venues, citation cross-references, theory names, and methodology mentions are all available in `references.bib`, source extract headers, and parsed PDFs — but they don't appear as entities in the knowledge graph.

This causes query failures: asking about a specific paper by title returns "I don't have enough information" even when the paper's full text is in the corpus.

## Solution

A deterministic post-ingestion enrichment pass that mines structured data from project files, creates graph entities and relationships, merges them into LightRAG's graph, and embeds new entities for vector search. Zero LLM calls (except embeddings). Runs automatically after `build`/`update`, also available standalone via `enrich`.

## Data Sources

### 1. `references.bib`

Parse bibtex entries to create:

**Paper entities** (one per entry):
- Name: bibtex key (e.g., `gordon2002`)
- Type: `paper`
- Description: `"Author(s) (Year). Title. Journal/Publisher."`
- Fields preserved: year, DOI, journal, booktitle

**Author entities** (deduplicated by normalized name):
- Name: `"LastName, FirstInitial"` normalized form
- Type: `author`

**Venue entities** (deduplicated by normalized name):
- Name: journal name or booktitle
- Type: `venue`

**Relationships:**
- `paper AUTHORED_BY author`
- `paper PUBLISHED_IN venue`

### 2. `research/sources/*.md` headers

Each source extract has a structured header with:
```
# Title
**Citation**: ...
**DOI/URL**: ...
**BibTeX Key**: key
**Access Level**: FULL-TEXT|ABSTRACT-ONLY|METADATA-ONLY
**Source Type**: journal_article|conference_paper|book_chapter|...
**Deep-Read**: true|false
```

**Enrichment:**
- Match to existing paper entity by bibtex key
- Add access level, source type, deep-read status to entity description
- If no paper entity exists (bib entry missing), create one from the header

### 3. `research/sources/*.md` body text

**Citation cross-references:**
- Scan for `\cite{key}`, `\citet{key}`, `\citep{key}` patterns
- Scan for `(Author, Year)` and `Author (Year)` patterns matched against known bib keys
- Create `source_paper CITES cited_paper` relationships

**Theory/framework mentions:**
- Extract from markdown headings: `## Theory Name`, `### Framework Name`
- Extract from bold patterns: `**Theory Name**` in definition contexts
- Type: `theory` or `framework`
- Create `paper DISCUSSES theory` relationships

**Methodology mentions:**
- Pattern match common research methods: `regression analysis`, `case study`, `meta-analysis`, `survey`, `experiment`, `grounded theory`, `content analysis`, `systematic review`, etc.
- Type: `method`
- Create `paper USES method` relationships

### 4. `attachments/parsed/*.md`

**Table of contents:**
- Extract heading structure as topic entities
- Type: `topic`

**Abstract text:**
- First section or text before first `##` heading
- Extract key claims (sentences with "We find", "Results show", "The authors argue", "This paper", "We propose")
- Type: `claim`
- Create `paper CLAIMS claim` relationships

## Graph Integration

### Entity deduplication

Before creating any entity:
1. Normalize name: lowercase, strip whitespace, collapse multiple spaces
2. Search existing graph nodes for exact normalized match
3. If found: **merge** — append structured description, add new relationships, preserve existing data
4. If not found: create new node

### Merge rules

| Existing | New | Action |
|-|-|-|
| LightRAG entity | Enrichment entity | Append description, add relationships, mark `enriched: true` |
| Enrichment entity | Same enrichment entity (re-run) | Skip (idempotent) |
| None | Enrichment entity | Create with `enrichment_source` attribute |

### Graph modification

1. Load GraphML via `networkx.read_graphml()`
2. Add/update nodes and edges
3. Write back to GraphML
4. Embed new/modified entities only (using configured `EMBEDDING_MODEL` via OpenRouter)
5. Update `vdb_entities.json` with new embeddings

## Command Interface

### Standalone

```bash
python scripts/knowledge.py enrich
```

Output:
```
Enrichment complete:
  Papers: 79 (67 new, 12 merged with existing)
  Authors: 143 (all new)
  Venues: 31 (all new)
  Theories: 18 (5 new, 13 merged)
  Methods: 12 (all new)
  Claims: 24 (all new)
  Relationships: 487 (342 new)
  Embeddings: 267 new vectors computed
```

### Baked into build/update

```python
# At the end of cmd_build():
await _enrich(rag)

# At the end of cmd_update():
await _enrich(rag)
```

Flag: `--skip-enrich` to opt out.

### State tracking

File: `research/knowledge/.enrichment_state.json`

```json
{
  "version": 1,
  "last_run": "2026-04-04T12:00:00Z",
  "file_hashes": {
    "references.bib": "sha256:abc...",
    "research/sources/gordon2002.md": "sha256:def...",
    ...
  },
  "entities_created": 267,
  "relationships_created": 487
}
```

On re-run, only process files whose content hash changed. This makes `enrich` fast on incremental updates.

## Implementation Structure

```
async def _enrich(rag) -> dict:
    """Coordinator: run all enrichment steps, return stats."""
    ├── _parse_bib_entries(bib_path) -> list[dict]
    │   Parse bibtex → paper, author, venue dicts
    │
    ├── _parse_source_headers(sources_dir) -> list[dict]
    │   Parse source extract headers → enriched paper dicts
    │
    ├── _parse_source_bodies(sources_dir, known_keys) -> list[dict]
    │   Citation cross-refs, theory/method mentions
    │
    ├── _parse_parsed_pdfs(parsed_dir, known_keys) -> list[dict]
    │   TOC topics, abstract claims
    │
    ├── _merge_into_graph(entities, relationships, graph_path) -> stats
    │   Deduplicate, merge, write GraphML
    │
    └── _embed_new_entities(new_entities, rag) -> int
        Compute embeddings for new entities, update vdb
```

All parsing functions are pure (no side effects, no API calls). Only `_embed_new_entities` makes external calls (embedding API).

## Bibtex Parsing

Use regex-based parser (no external dependency). The bib format in this project is well-structured (generated by the pipeline's bibliographer agent). Parse:

```python
_BIB_ENTRY_RE = re.compile(
    r'@(\w+)\{(\w+),\s*\n(.*?)\n\}',
    re.DOTALL
)
_BIB_FIELD_RE = re.compile(
    r'(\w+)\s*=\s*\{(.*?)\}',
    re.DOTALL
)
```

Fields: author, title, year, journal, booktitle, doi, publisher.

Author parsing: split on ` and `, normalize each to `"Last, F."` form.

## Testing

- `tests/test_enrichment.py` with:
  - Bib parsing (sample entries → expected entity dicts)
  - Source header parsing (sample markdown → expected enrichments)
  - Citation cross-ref extraction
  - Theory/method extraction
  - Entity deduplication/merge logic
  - Idempotency (run twice, same result)
  - All pure function tests — no graph or API needed
