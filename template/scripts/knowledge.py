#!/usr/bin/env python3
"""
Knowledge graph for research paper source extracts.

Uses LightRAG to build a queryable knowledge graph from research/sources/*.md files.
All LLM and embedding calls go through OpenRouter (OPENROUTER_API_KEY env var).

Usage:
    python scripts/knowledge.py build                        # Build/update graph from sources
    python scripts/knowledge.py query "question"             # Freeform semantic search
    python scripts/knowledge.py contradictions               # Find conflicting claims
    python scripts/knowledge.py evidence-for "claim"         # Sources supporting a claim
    python scripts/knowledge.py evidence-against "claim"     # Sources challenging a claim
    python scripts/knowledge.py entities                     # List extracted entities
    python scripts/knowledge.py relationships "entity"       # Show entity connections
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
LOG_FILE = "research/log.md"
CONTRADICTIONS_FILE = "research/knowledge_contradictions.md"

LLM_MODEL = "google/gemini-3-flash-preview"
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"
EMBEDDING_DIM = 4096
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


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


# ---------------------------------------------------------------------------
# LightRAG initialization
# ---------------------------------------------------------------------------

def create_rag():
    """Create and return a LightRAG instance configured for OpenRouter."""
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed

    api_key = get_api_key()

    try:
        from lightrag.utils import EmbeddingFunc
    except ImportError:
        from lightrag.base import EmbeddingFunc

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=openai_complete_if_cache,
        llm_model_name=LLM_MODEL,
        llm_model_kwargs={
            "base_url": OPENROUTER_BASE_URL,
            "api_key": api_key,
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM,
            max_token_size=8192,
            func=partial(
                openai_embed,
                model=EMBEDDING_MODEL,
                base_url=OPENROUTER_BASE_URL,
                api_key=api_key,
            ),
        ),
    )
    return rag


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

async def cmd_build(args):
    """Build or update the knowledge graph from research/sources/*.md."""
    sources_path = Path(SOURCES_DIR)
    if not sources_path.exists():
        print(f"Error: {SOURCES_DIR} directory not found.", file=sys.stderr)
        sys.exit(1)

    source_files = sorted(sources_path.glob("*.md"))
    if not source_files:
        print(f"No .md files found in {SOURCES_DIR}.", file=sys.stderr)
        sys.exit(1)

    print(f"Building knowledge graph from {len(source_files)} source extracts...")

    documents = []
    ids = []
    for f in source_files:
        content = f.read_text(encoding="utf-8")
        documents.append(content)
        ids.append(f.stem)

    os.makedirs(WORKING_DIR, exist_ok=True)
    rag = create_rag()
    await rag.initialize_storages()
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
        f"{relation_count} relationships from {len(source_files)} source documents"
    )
    print(summary)

    log_operation("Build", {
        "Tool": "scripts/knowledge.py build",
        "Sources ingested": f"{len(source_files)} documents from {SOURCES_DIR}",
        "Entities extracted": str(entity_count),
        "Relationships extracted": str(relation_count),
        "Storage": WORKING_DIR,
    })


async def cmd_query(args):
    """Freeform semantic search across the knowledge graph."""
    from lightrag import QueryParam

    rag = create_rag()
    await rag.initialize_storages()

    result = await rag.aquery(
        args.question,
        param=QueryParam(mode="hybrid"),
    )

    print(f"## Results (hybrid mode)\n\n{result}")

    log_operation("Query", {
        "Tool": "scripts/knowledge.py query",
        "Query": args.question,
        "Mode": "hybrid",
        "Result": "SUCCESS" if result else "EMPTY",
    })


async def cmd_contradictions(args):
    """Find conflicting claims across source documents."""
    from lightrag import QueryParam

    rag = create_rag()
    await rag.initialize_storages()

    prompt = (
        "Identify contradictions, tensions, and conflicting claims across the source documents "
        "in this knowledge graph. For each contradiction found, report:\n"
        "1. The specific claims that conflict\n"
        "2. Which source documents (by bibtex key) make each claim\n"
        "3. Whether the contradiction is resolved in any source, or remains open\n\n"
        "Focus on substantive intellectual disagreements, not minor differences in framing. "
        "Format each contradiction as a numbered item."
    )

    result = await rag.aquery(prompt, param=QueryParam(mode="global"))

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
    from lightrag import QueryParam

    rag = create_rag()
    await rag.initialize_storages()

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

    result = await rag.aquery(prompt, param=QueryParam(mode="hybrid"))
    print(f"## Evidence Supporting: \"{args.claim}\"\n\n{result}")

    log_operation("Evidence-For", {
        "Tool": "scripts/knowledge.py evidence-for",
        "Query": args.claim,
        "Mode": "hybrid",
        "Result": "SUCCESS" if result else "EMPTY",
    })


async def cmd_evidence_against(args):
    """Find sources challenging a specific claim."""
    from lightrag import QueryParam

    rag = create_rag()
    await rag.initialize_storages()

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

    result = await rag.aquery(prompt, param=QueryParam(mode="hybrid"))
    print(f"## Evidence Against: \"{args.claim}\"\n\n{result}")

    log_operation("Evidence-Against", {
        "Tool": "scripts/knowledge.py evidence-against",
        "Query": args.claim,
        "Mode": "hybrid",
        "Result": "SUCCESS" if result else "EMPTY",
    })


async def cmd_entities(args):
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
        for _, target_node, data in G.edges(match, data=True):
            rel_type = data.get("relationship", data.get("label", "related_to"))
            print(f"  -> {rel_type} -> {target_node}")
        for source_node, _, data in G.in_edges(match, data=True):
            rel_type = data.get("relationship", data.get("label", "related_to"))
            print(f"  <- {rel_type} <- {source_node}")
        print()

    log_operation("Relationships", {
        "Tool": "scripts/knowledge.py relationships",
        "Query": args.entity,
        "Result": f"Found {len(matches)} matching entities",
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

    args = parser.parse_args()

    commands = {
        "build": cmd_build,
        "query": cmd_query,
        "contradictions": cmd_contradictions,
        "evidence-for": cmd_evidence_for,
        "evidence-against": cmd_evidence_against,
        "entities": cmd_entities,
        "relationships": cmd_relationships,
    }

    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main()
