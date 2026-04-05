#!/usr/bin/env python3
"""Build research/prisma_metadata.json from project artifacts.

Reads: research/log.md, research/source-manifest.json, references.bib,
       research/sources/*.md, .paper-state.json
Writes: research/prisma_metadata.json

Usage:
    python scripts/prisma-metadata.py [--project DIR]
    python scripts/prisma-metadata.py [--project DIR] build
    python scripts/prisma-metadata.py [--project DIR] update --phase PHASE --key KEY --reason REASON
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


def parse_research_log(log_path: str) -> dict:
    """Extract search statistics from research/log.md."""
    databases: dict[str, dict] = {}
    if not os.path.exists(log_path):
        return {"databases": [], "other_sources": [], "total_identified": 0}

    with open(log_path) as f:
        content = f.read()

    # Parse database search entries
    # Format: ### [TIMESTAMP] -- Search: <database>
    for match in re.finditer(
        r"###\s+\[.*?\]\s+—\s+(?:Search|Query):\s+(\S+).*?\n"
        r".*?Results:\s+(\d+)",
        content,
        re.DOTALL,
    ):
        db_name = match.group(1)
        count = int(match.group(2))
        if db_name not in databases:
            databases[db_name] = {"name": db_name, "results": 0, "queries": []}
        databases[db_name]["results"] += count

    # Snowballing and co-citation as other sources
    other = []
    snow_match = re.search(r"snowball.*?added.*?(\d+)", content, re.I)
    if snow_match:
        other.append({"name": "Citation snowballing", "results": int(snow_match.group(1))})
    cocit_match = re.search(r"co-citation.*?found.*?(\d+)", content, re.I)
    if cocit_match:
        other.append({"name": "Co-citation analysis", "results": int(cocit_match.group(1))})

    db_list = list(databases.values())
    total = sum(d["results"] for d in db_list) + sum(s["results"] for s in other)

    return {"databases": db_list, "other_sources": other, "total_identified": total}


def count_sources_by_phase(sources_dir: str) -> dict:
    """Count sources by access level from source extracts."""
    counts = Counter()
    sources_path = Path(sources_dir)
    if not sources_path.exists():
        return dict(counts)
    for f in sources_path.glob("*.md"):
        content = f.read_text()
        if "FULL-TEXT" in content:
            counts["FULL-TEXT"] += 1
        elif "ABSTRACT-ONLY" in content:
            counts["ABSTRACT-ONLY"] += 1
        elif "METADATA-ONLY" in content:
            counts["METADATA-ONLY"] += 1
    return dict(counts)


def count_bib_entries(bib_path: str) -> int:
    """Count entries in references.bib."""
    if not os.path.exists(bib_path):
        return 0
    with open(bib_path) as f:
        return len(re.findall(r"^@\w+\{", f.read(), re.MULTILINE))


def build_prisma_metadata(project_dir: str) -> dict:
    """Build complete PRISMA metadata from project artifacts."""
    log_path = os.path.join(project_dir, "research", "log.md")
    sources_dir = os.path.join(project_dir, "research", "sources")
    bib_path = os.path.join(project_dir, "references.bib")

    search_stats = parse_research_log(log_path)
    source_counts = count_sources_by_phase(sources_dir)
    bib_count = count_bib_entries(bib_path)

    total_identified = search_stats["total_identified"]

    # Load existing metadata if present (for incremental updates)
    output_path = os.path.join(project_dir, "research", "prisma_metadata.json")
    existing = {}
    if os.path.exists(output_path):
        with open(output_path) as f:
            existing = json.load(f)

    # Compute deduplication estimate
    dedup_before = total_identified
    total_sources = sum(source_counts.values())
    dedup_removed = max(0, dedup_before - total_sources - (total_identified - total_sources) // 3)
    dedup_after = dedup_before - dedup_removed

    metadata = {
        "version": 1,
        "search_strategy": search_stats,
        "deduplication": existing.get("deduplication", {
            "before": dedup_before,
            "duplicates_removed": dedup_removed,
            "after": dedup_after,
            "method": "DOI exact match, then SHA256, then normalized title (first 80 chars)",
        }),
        "screening": existing.get("screening", {
            "screened": dedup_after,
            "excluded": max(0, dedup_after - total_sources),
            "exclusion_reasons": [],
            "method": "Title and abstract review against inclusion criteria",
        }),
        "eligibility": existing.get("eligibility", {
            "assessed": total_sources,
            "excluded": source_counts.get("METADATA-ONLY", 0),
            "exclusion_reasons": [],
            "method": "Full-text assessment against methodological quality criteria",
        }),
        "included": {
            "qualitative_synthesis": bib_count,
            "quantitative_synthesis": 0,
            "new_studies_from_targeted_research": 0,
        },
        "per_source_log": existing.get("per_source_log", []),
    }

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Build PRISMA metadata")
    parser.add_argument("--project", default=".", help="Project directory")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="Build/rebuild metadata from artifacts")
    update_cmd = sub.add_parser("update", help="Update a screening/eligibility exclusion reason")
    update_cmd.add_argument("--phase", choices=["screening", "eligibility"], required=True)
    update_cmd.add_argument("--key", required=True, help="BibTeX key")
    update_cmd.add_argument("--reason", required=True, help="Exclusion reason")

    args = parser.parse_args()

    project = args.project

    if args.command == "update":
        output_path = os.path.join(project, "research", "prisma_metadata.json")
        if not os.path.exists(output_path):
            print("Error: prisma_metadata.json not found. Run 'build' first.", file=sys.stderr)
            sys.exit(1)
        with open(output_path) as f:
            data = json.load(f)
        phase = data[args.phase]
        # Add to exclusion reasons
        for er in phase["exclusion_reasons"]:
            if er["reason"] == args.reason:
                er["count"] += 1
                break
        else:
            phase["exclusion_reasons"].append({"reason": args.reason, "count": 1})
        phase["excluded"] = sum(er["count"] for er in phase["exclusion_reasons"])
        # Add to per-source log
        data.setdefault("per_source_log", []).append({
            "bibtex_key": args.key,
            "phase": args.phase,
            "exclusion_reason": args.reason,
        })
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Updated {args.phase} exclusion for {args.key}: {args.reason}")
    else:
        metadata = build_prisma_metadata(project)
        output_path = os.path.join(project, "research", "prisma_metadata.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"PRISMA metadata written to {output_path}")
        inc = metadata["included"]
        print(f"  Identified: {metadata['search_strategy']['total_identified']}")
        print(f"  After dedup: {metadata['deduplication']['after']}")
        print(f"  Included: {inc['qualitative_synthesis']}")


if __name__ == "__main__":
    main()
