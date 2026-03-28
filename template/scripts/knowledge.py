#!/usr/bin/env python3
"""
Knowledge graph for research paper source extracts.

Uses LightRAG to build a queryable knowledge graph from research/sources/*.md files.
All LLM and embedding calls go through OpenRouter (OPENROUTER_API_KEY env var).

Usage:
    python scripts/knowledge.py build                        # Build/update graph from sources
    python scripts/knowledge.py update                       # Incremental update (new/changed files only)
    python scripts/knowledge.py query "question"             # Freeform semantic search
    python scripts/knowledge.py contradictions               # Find conflicting claims
    python scripts/knowledge.py evidence-for "claim"         # Sources supporting a claim
    python scripts/knowledge.py evidence-against "claim"     # Sources challenging a claim
    python scripts/knowledge.py entities                     # List extracted entities
    python scripts/knowledge.py relationships "entity"       # Show entity connections
    python scripts/knowledge.py coverage "document.md"       # Check entity coverage in a document
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WORKING_DIR = "research/knowledge"
SOURCES_DIR = "research/sources"
ATTACHMENTS_DIR = "attachments"
PARSED_DIR = "attachments/parsed"
LOG_FILE = "research/log.md"
CONTRADICTIONS_FILE = "research/knowledge_contradictions.md"
LAST_BUILD_FILE = os.path.join(WORKING_DIR, ".last_build")
CACHE_DIR = os.path.join(WORKING_DIR, ".cache")

LLM_MODEL = os.environ.get("LIGHTRAG_LLM_MODEL", "google/gemini-3-flash-preview")
EMBEDDING_MODEL = os.environ.get("LIGHTRAG_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
EMBEDDING_DIM = int(os.environ.get("LIGHTRAG_EMBEDDING_DIM", "4096"))
EMBEDDING_LENGTH = int(os.environ.get("LIGHTRAG_EMBEDDING_LENGTH", "32768"))
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Concurrency settings — conservative defaults to avoid OpenRouter rate limits.
# Total concurrent LLM calls ≈ MAX_PARALLEL_INSERT × LLM_MAX_ASYNC
# Override via env vars if your API plan supports higher throughput.
MAX_PARALLEL_INSERT = int(os.environ.get("LIGHTRAG_MAX_PARALLEL_INSERT", "8"))
LLM_MAX_ASYNC = int(os.environ.get("LIGHTRAG_MAX_ASYNC", "8"))
EMBEDDING_BATCH_NUM = int(os.environ.get("LIGHTRAG_EMBEDDING_BATCH_NUM", "16"))

# Timeout settings (seconds) — full PDFs need more time than short extracts.
LLM_TIMEOUT = int(os.environ.get("LIGHTRAG_LLM_TIMEOUT", "300"))
EMBEDDING_TIMEOUT = int(os.environ.get("LIGHTRAG_EMBEDDING_TIMEOUT", "300"))


def get_api_key():
    """Get OpenRouter API key from environment."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Error: OPENROUTER_API_KEY environment variable not set.", file=sys.stderr)
        print("Get a key at https://openrouter.ai/keys", file=sys.stderr)
        sys.exit(1)
    return key


def log_operation(operation: str, details: dict):
    """Append an entry to research/log.md."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"\n### {timestamp} — Knowledge Graph {operation}\n"
    for key, value in details.items():
        entry += f"- **{key}**: {value}\n"
    log_path = Path(LOG_FILE)
    if log_path.exists():
        with open(log_path, "a") as f:
            f.write(entry)


def _save_build_timestamp():
    """Save current timestamp as last build time."""
    Path(LAST_BUILD_FILE).write_text(
        datetime.now(timezone.utc).isoformat(), encoding="utf-8"
    )


def _invalidate_cache():
    """Delete query cache (called after build/update)."""
    import shutil

    cache_path = Path(CACHE_DIR)
    if cache_path.exists():
        shutil.rmtree(cache_path)


def _get_cache_path(query: str, mode: str) -> Path:
    """Get cache file path for a query."""
    import hashlib

    key = hashlib.sha256(f"{query}|{mode}".encode()).hexdigest()[:32]
    return Path(CACHE_DIR) / f"{key}.txt"


async def _cached_query(rag, query: str, mode: str) -> str:
    """Query with file-based caching. Returns cached result if available."""
    from lightrag import QueryParam

    cache_path = _get_cache_path(query, mode)
    if cache_path.exists():
        print("(using cached result)", file=sys.stderr)
        return cache_path.read_text(encoding="utf-8")

    result = await rag.aquery(query, param=QueryParam(mode=mode))
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path.write_text(str(result), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# LightRAG initialization
# ---------------------------------------------------------------------------

def create_rag():
    """Create and return a LightRAG instance configured for OpenRouter."""
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete, openai_embed

    api_key = get_api_key()

    try:
        from lightrag.utils import EmbeddingFunc
    except ImportError:
        from lightrag.base import EmbeddingFunc

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=openai_complete,
        llm_model_name=LLM_MODEL,
        llm_model_kwargs={
            "base_url": OPENROUTER_BASE_URL,
            "api_key": api_key,
        },
        llm_model_max_async=LLM_MAX_ASYNC,
        max_parallel_insert=MAX_PARALLEL_INSERT,
        default_llm_timeout=LLM_TIMEOUT,
        default_embedding_timeout=EMBEDDING_TIMEOUT,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM,
            max_token_size=EMBEDDING_LENGTH,
            func=partial(
                openai_embed,
                model=EMBEDDING_MODEL,
                base_url=OPENROUTER_BASE_URL,
                api_key=api_key,
            ),
        ),
        embedding_batch_num=EMBEDDING_BATCH_NUM,
    )
    return rag


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract full text from a PDF using pymupdf."""
    try:
        import fitz  # pymupdf
    except ImportError:
        print(
            f"Warning: pymupdf not installed, skipping PDF {pdf_path.name}. "
            "Install with: pip install pymupdf",
            file=sys.stderr,
        )
        return ""

    try:
        doc = fitz.open(str(pdf_path))
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        full_text = "\n\n".join(pages)
        if not full_text.strip():
            return ""
        # Prepend a header so the graph can attribute entities back to this PDF
        return f"# PDF: {pdf_path.stem}\n\nSource file: {pdf_path.name}\n\n{full_text}"
    except Exception as e:
        print(f"Warning: Failed to extract text from {pdf_path.name}: {e}", file=sys.stderr)
        return ""


async def cmd_build(_args):
    """Build or update the knowledge graph from source extracts and PDFs."""
    sources_path = Path(SOURCES_DIR)
    attachments_path = Path(ATTACHMENTS_DIR)

    documents = []
    ids = []

    # --- Source extract markdown files ---
    if sources_path.exists():
        source_files = sorted(sources_path.glob("*.md"))
        for f in source_files:
            content = f.read_text(encoding="utf-8")
            documents.append(content)
            ids.append(f.stem)
        print(f"Found {len(source_files)} source extracts in {SOURCES_DIR}/")
    else:
        source_files = []
        print(f"Warning: {SOURCES_DIR}/ not found, skipping source extracts.", file=sys.stderr)

    # --- Parsed markdown or PDF files in attachments ---
    # Prefer Docling-parsed markdown (attachments/parsed/<key>.md) over raw PDF
    # extraction. This avoids duplicate ingestion and gives higher quality text.
    parsed_path = Path(PARSED_DIR)
    pdf_count = 0
    parsed_count = 0
    parsed_stems = set()

    if parsed_path.exists():
        parsed_files = sorted(parsed_path.glob("*.md"))
        for f in parsed_files:
            content = f.read_text(encoding="utf-8")
            if content.strip():
                doc_id = f"parsed_{f.stem}"
                documents.append(content)
                ids.append(doc_id)
                parsed_count += 1
                parsed_stems.add(f.stem)
        if parsed_files:
            print(f"Found {parsed_count} Docling-parsed files in {PARSED_DIR}/")

    if attachments_path.exists():
        pdf_files = sorted(attachments_path.glob("*.pdf"))
        for pdf in pdf_files:
            if pdf.stem in parsed_stems:
                continue  # Already ingested via parsed markdown
            text = extract_pdf_text(pdf)
            if text:
                doc_id = f"pdf_{pdf.stem}"
                documents.append(text)
                ids.append(doc_id)
                pdf_count += 1
        if pdf_files:
            skipped = len([p for p in pdf_files if p.stem in parsed_stems])
            print(f"Extracted text from {pdf_count}/{len(pdf_files)} PDFs in {ATTACHMENTS_DIR}/ ({skipped} skipped — parsed markdown exists)")
    else:
        print(f"No {ATTACHMENTS_DIR}/ directory found, skipping PDFs.")

    if not documents:
        print("Error: No documents to ingest (no source extracts and no readable PDFs).", file=sys.stderr)
        sys.exit(1)

    print(f"Building knowledge graph from {len(documents)} total documents...")

    os.makedirs(WORKING_DIR, exist_ok=True)
    rag = create_rag()
    await rag.initialize_storages()
    from lightrag.kg.shared_storage import initialize_pipeline_status
    await initialize_pipeline_status()
    await rag.ainsert(documents, ids=ids)

    entity_count = 0
    relation_count = 0
    try:
        import networkx as nx
        graph_path = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
        if graph_path.exists():
            G = nx.read_graphml(str(graph_path))
            entity_count = G.number_of_nodes()
            relation_count = G.number_of_edges()
    except Exception:
        pass

    summary = (
        f"Built knowledge graph: {entity_count} entities, "
        f"{relation_count} relationships from {len(documents)} documents "
        f"({len(source_files)} source extracts + {parsed_count} parsed + {pdf_count} PDFs)"
    )
    print(summary)

    log_operation("Build", {
        "Tool": "scripts/knowledge.py build",
        "Source extracts": f"{len(source_files)} from {SOURCES_DIR}",
        "Parsed markdown": f"{parsed_count} from {PARSED_DIR}",
        "PDFs ingested": f"{pdf_count} from {ATTACHMENTS_DIR} (skipped {len(parsed_stems)} with parsed markdown)",
        "Total documents": str(len(documents)),
        "Entities extracted": str(entity_count),
        "Relationships extracted": str(relation_count),
        "Storage": WORKING_DIR,
    })

    _save_build_timestamp()
    _invalidate_cache()


async def cmd_update(_args):
    """Incremental update: only ingest files newer than last build."""
    last_build_path = Path(LAST_BUILD_FILE)
    if not last_build_path.exists():
        print("No previous build found. Running full build instead.")
        await cmd_build(_args)
        return

    last_build_time = datetime.fromisoformat(
        last_build_path.read_text(encoding="utf-8").strip()
    ).timestamp()

    sources_path = Path(SOURCES_DIR)
    attachments_path = Path(ATTACHMENTS_DIR)

    documents = []
    ids = []

    # --- New/changed source extracts ---
    new_sources = 0
    if sources_path.exists():
        for f in sorted(sources_path.glob("*.md")):
            if f.stat().st_mtime > last_build_time:
                documents.append(f.read_text(encoding="utf-8"))
                ids.append(f.stem)
                new_sources += 1

    # --- New/changed parsed markdown or PDFs ---
    parsed_path = Path(PARSED_DIR)
    new_parsed = 0
    new_pdfs = 0
    parsed_stems = set()

    if parsed_path.exists():
        for f in sorted(parsed_path.glob("*.md")):
            parsed_stems.add(f.stem)
            if f.stat().st_mtime > last_build_time:
                content = f.read_text(encoding="utf-8")
                if content.strip():
                    documents.append(content)
                    ids.append(f"parsed_{f.stem}")
                    new_parsed += 1

    if attachments_path.exists():
        for pdf in sorted(attachments_path.glob("*.pdf")):
            if pdf.stem in parsed_stems:
                continue  # Already handled via parsed markdown
            if pdf.stat().st_mtime > last_build_time:
                text = extract_pdf_text(pdf)
                if text:
                    documents.append(text)
                    ids.append(f"pdf_{pdf.stem}")
                    new_pdfs += 1

    if not documents:
        print("No new or changed files since last build. Graph is up to date.")
        return

    print(f"Updating knowledge graph with {len(documents)} new/changed documents "
          f"({new_sources} sources + {new_parsed} parsed + {new_pdfs} PDFs)...")

    rag = create_rag()
    await rag.initialize_storages()
    from lightrag.kg.shared_storage import initialize_pipeline_status
    await initialize_pipeline_status()
    await rag.ainsert(documents, ids=ids)

    _save_build_timestamp()
    _invalidate_cache()

    print(f"Updated knowledge graph with {len(documents)} documents.")

    log_operation("Update", {
        "Tool": "scripts/knowledge.py update",
        "New sources": str(new_sources),
        "New PDFs": str(new_pdfs),
        "Total new documents": str(len(documents)),
    })


async def cmd_query(args):
    """Freeform semantic search across the knowledge graph."""
    rag = create_rag()
    await rag.initialize_storages()
    from lightrag.kg.shared_storage import initialize_pipeline_status
    await initialize_pipeline_status()

    result = await _cached_query(rag, args.question, "hybrid")

    print(f"## Results (hybrid mode)\n\n{result}")

    log_operation("Query", {
        "Tool": "scripts/knowledge.py query",
        "Query": args.question,
        "Mode": "hybrid",
        "Result": "SUCCESS" if result else "EMPTY",
    })


async def cmd_contradictions(_args):
    """Find conflicting claims across source documents."""
    rag = create_rag()
    await rag.initialize_storages()
    from lightrag.kg.shared_storage import initialize_pipeline_status
    await initialize_pipeline_status()

    prompt = (
        "Identify contradictions, tensions, and conflicting claims across the source documents "
        "in this knowledge graph. For each contradiction found, report:\n"
        "1. The specific claims that conflict\n"
        "2. Which source documents (by bibtex key) make each claim\n"
        "3. Whether the contradiction is resolved in any source, or remains open\n\n"
        "Focus on substantive intellectual disagreements, not minor differences in framing. "
        "Format each contradiction as a numbered item."
    )

    result = await _cached_query(rag, prompt, "global")

    output = (
        f"# Knowledge Graph — Contradictions Report\n\n"
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
        f"{result}"
    )
    print(output)

    Path(CONTRADICTIONS_FILE).write_text(output, encoding="utf-8")
    print(f"\nSaved to {CONTRADICTIONS_FILE}")

    log_operation("Contradictions", {
        "Tool": "scripts/knowledge.py contradictions",
        "Mode": "global",
        "Result": f"Report written to {CONTRADICTIONS_FILE}",
    })


async def cmd_evidence_for(args):
    """Find sources supporting a specific claim."""
    rag = create_rag()
    await rag.initialize_storages()
    from lightrag.kg.shared_storage import initialize_pipeline_status
    await initialize_pipeline_status()

    prompt = (
        f"Find all evidence in the source documents that SUPPORTS the following claim:\n\n"
        f"\"{args.claim}\"\n\n"
        f"For each piece of evidence, report:\n"
        f"1. The specific finding or data point\n"
        f"2. Which source document (by bibtex key) it comes from\n"
        f"3. How strongly it supports the claim (direct evidence vs. tangential)\n\n"
        f"Only include evidence that genuinely supports the claim. "
        f"Do not stretch or misrepresent findings."
    )

    result = await _cached_query(rag, prompt, "hybrid")
    print(f"## Evidence Supporting: \"{args.claim}\"\n\n{result}")

    log_operation("Evidence-For", {
        "Tool": "scripts/knowledge.py evidence-for",
        "Query": args.claim,
        "Mode": "hybrid",
        "Result": "SUCCESS" if result else "EMPTY",
    })


async def cmd_evidence_against(args):
    """Find sources challenging a specific claim."""
    rag = create_rag()
    await rag.initialize_storages()
    from lightrag.kg.shared_storage import initialize_pipeline_status
    await initialize_pipeline_status()

    prompt = (
        f"Find all evidence in the source documents that CONTRADICTS or CHALLENGES "
        f"the following claim:\n\n"
        f"\"{args.claim}\"\n\n"
        f"For each piece of evidence, report:\n"
        f"1. The specific finding or data point that conflicts\n"
        f"2. Which source document (by bibtex key) it comes from\n"
        f"3. How strongly it undermines the claim\n\n"
        f"Include alternative explanations, methodological critiques, and null findings. "
        f"Be thorough — a reviewer would use this to attack the claim."
    )

    result = await _cached_query(rag, prompt, "hybrid")
    print(f"## Evidence Against: \"{args.claim}\"\n\n{result}")

    log_operation("Evidence-Against", {
        "Tool": "scripts/knowledge.py evidence-against",
        "Query": args.claim,
        "Mode": "hybrid",
        "Result": "SUCCESS" if result else "EMPTY",
    })


async def cmd_entities(_args):
    """List all extracted entities from the knowledge graph."""
    import networkx as nx

    graph_path = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
    if not graph_path.exists():
        print("Error: Knowledge graph not built yet. Run 'build' first.", file=sys.stderr)
        sys.exit(1)

    G = nx.read_graphml(str(graph_path))

    entities = {}
    for node, data in G.nodes(data=True):
        entity_type = data.get("entity_type", "unknown")
        if entity_type not in entities:
            entities[entity_type] = []
        entities[entity_type].append(node)

    print(f"## Entities ({G.number_of_nodes()} total)\n")
    for entity_type, names in sorted(entities.items()):
        print(f"### {entity_type} ({len(names)})")
        for name in sorted(names):
            print(f"- {name}")
        print()

    log_operation("Entities", {
        "Tool": "scripts/knowledge.py entities",
        "Result": f"{G.number_of_nodes()} entities across {len(entities)} types",
    })


async def cmd_relationships(args):
    """Show how a specific entity connects to others in the graph."""
    import networkx as nx

    graph_path = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
    if not graph_path.exists():
        print("Error: Knowledge graph not built yet. Run 'build' first.", file=sys.stderr)
        sys.exit(1)

    G = nx.read_graphml(str(graph_path))

    target = args.entity.lower()
    matches = [n for n in G.nodes() if target in n.lower()]

    if not matches:
        print(f"No entity matching '{args.entity}' found in the graph.", file=sys.stderr)
        print("Try 'entities' command to see all available entities.", file=sys.stderr)
        sys.exit(1)

    for match in matches:
        print(f"## Relationships for: {match}\n")
        for neighbor in G.neighbors(match):
            data = G.edges[match, neighbor]
            rel_type = data.get("relationship", data.get("label", "related_to"))
            print(f"  -- {rel_type} -- {neighbor}")
        print()

    log_operation("Relationships", {
        "Tool": "scripts/knowledge.py relationships",
        "Query": args.entity,
        "Result": f"Found {len(matches)} matching entities",
    })


async def cmd_coverage(args):
    """Check which graph entities appear in a document."""
    import networkx as nx

    graph_path = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
    if not graph_path.exists():
        print("Error: Knowledge graph not built yet. Run 'build' first.", file=sys.stderr)
        sys.exit(1)

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: Document not found: {args.document}", file=sys.stderr)
        sys.exit(1)

    doc_text = doc_path.read_text(encoding="utf-8").lower()
    G = nx.read_graphml(str(graph_path))

    # Build entity list with connection counts
    missing = []
    present = []
    for node in G.nodes():
        degree = G.degree(node)
        if node.lower() in doc_text:
            present.append((node, degree))
        else:
            missing.append((node, degree))

    # Sort missing by degree (most connected first = most important)
    missing.sort(key=lambda x: x[1], reverse=True)

    total = len(present) + len(missing)
    print(f"## Entity Coverage for {args.document}\n")
    print(f"**Present**: {len(present)}/{total} entities found in document\n")

    if missing:
        print(f"### Missing Entities ({len(missing)}) — sorted by importance\n")
        for name, degree in missing:
            print(f"- **{name}** ({degree} connections)")
    else:
        print("All entities are covered in the document.")

    log_operation("Coverage", {
        "Tool": "scripts/knowledge.py coverage",
        "Document": args.document,
        "Present": str(len(present)),
        "Missing": str(len(missing)),
        "Total": str(total),
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Knowledge graph for research paper source extracts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("build", help="Build/update graph from research/sources/")
    subparsers.add_parser("update", help="Incremental update (new/changed files only)")

    p_query = subparsers.add_parser("query", help="Freeform semantic search")
    p_query.add_argument("question", help="Question to search for")

    subparsers.add_parser("contradictions", help="Find conflicting claims across sources")

    p_efor = subparsers.add_parser("evidence-for", help="Find sources supporting a claim")
    p_efor.add_argument("claim", help="The claim to find evidence for")

    p_eagainst = subparsers.add_parser("evidence-against", help="Find sources challenging a claim")
    p_eagainst.add_argument("claim", help="The claim to find evidence against")

    subparsers.add_parser("entities", help="List all extracted entities")

    p_rel = subparsers.add_parser("relationships", help="Show entity connections")
    p_rel.add_argument("entity", help="Entity name to look up")

    p_cov = subparsers.add_parser("coverage", help="Check entity coverage in a document")
    p_cov.add_argument("document", help="Path to document to check")

    args = parser.parse_args()

    commands = {
        "build": cmd_build,
        "update": cmd_update,
        "query": cmd_query,
        "contradictions": cmd_contradictions,
        "evidence-for": cmd_evidence_for,
        "evidence-against": cmd_evidence_against,
        "entities": cmd_entities,
        "relationships": cmd_relationships,
        "coverage": cmd_coverage,
    }

    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main()
