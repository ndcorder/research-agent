#!/usr/bin/env python3
"""Rebuild or update research/source-manifest.json from current project state.

Scans references.bib, research/sources/, attachments/, and attachments/parsed/
to build a manifest of all source artifacts and their relationships.

Usage:
    python3 scripts/update-manifest.py              # Full rebuild from disk
    python3 scripts/update-manifest.py --key smith2024  # Update one entry only

Exit codes:
    0 — success
    1 — error
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_PATH = "research/source-manifest.json"
SOURCES_DIR = "research/sources"
ATTACHMENTS_DIR = "attachments"
PARSED_DIR = "attachments/parsed"
BIB_FILE = "references.bib"


def load_manifest() -> dict:
    path = Path(MANIFEST_PATH)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict):
    Path(MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written: {MANIFEST_PATH} ({len(manifest)} sources)")


def extract_bib_keys() -> set[str]:
    bib_path = Path(BIB_FILE)
    if not bib_path.exists():
        return set()
    content = bib_path.read_text(encoding="utf-8")
    return set(re.findall(r"@\w+\{(\w+),", content))


def extract_field_from_source(source_path: Path, field: str) -> str:
    """Extract a metadata field value from a source extract markdown file."""
    try:
        content = source_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    pattern = rf"\*\*{re.escape(field)}\*\*:\s*(.+)"
    match = re.search(pattern, content)
    return match.group(1).strip() if match else ""


def file_mtime_iso(path: Path) -> str:
    """Return the file's modification time as ISO-8601, following symlinks."""
    try:
        mtime = path.resolve().stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except Exception:
        return ""


def build_entry(key: str, existing: dict | None = None) -> dict:
    """Build a manifest entry for a single source key."""
    entry = existing.copy() if existing else {}
    entry["bib_key"] = key

    pdf_path = Path(ATTACHMENTS_DIR) / f"{key}.pdf"
    parsed_md_path = Path(PARSED_DIR) / f"{key}.md"
    figures_dir_path = Path(PARSED_DIR) / f"{key}_figures"
    source_path = Path(SOURCES_DIR) / f"{key}.md"

    # PDF
    if pdf_path.exists():
        entry["pdf"] = str(pdf_path)
        entry["pdf_cached"] = pdf_path.is_symlink()
    else:
        entry.pop("pdf", None)
        entry.pop("pdf_cached", None)

    # Parsed markdown
    if parsed_md_path.exists():
        entry["parsed_md"] = str(parsed_md_path)
        entry["parsed_at"] = entry.get("parsed_at") or file_mtime_iso(parsed_md_path)
    else:
        entry.pop("parsed_md", None)
        entry.pop("parsed_at", None)

    # Figures directory
    if figures_dir_path.exists() and (
        figures_dir_path.is_symlink() or any(figures_dir_path.iterdir())
    ):
        entry["figures_dir"] = str(figures_dir_path)
    else:
        entry.pop("figures_dir", None)

    # Source extract
    if source_path.exists():
        entry["source_extract"] = str(source_path)
        entry["access_level"] = (
            extract_field_from_source(source_path, "Access Level") or
            entry.get("access_level", "")
        )
        entry["source_type"] = (
            extract_field_from_source(source_path, "Source Type") or
            entry.get("source_type", "")
        )
        deep_read = extract_field_from_source(source_path, "Deep-Read")
        entry["deep_read"] = deep_read.lower() == "true"
        if entry["deep_read"]:
            deep_read_date = extract_field_from_source(source_path, "Deep-Read Date")
            entry["deep_read_at"] = deep_read_date or entry.get("deep_read_at", "")
        else:
            entry.pop("deep_read_at", None)
    else:
        entry.pop("source_extract", None)
        entry.pop("access_level", None)
        entry.pop("source_type", None)
        entry.pop("deep_read", None)
        entry.pop("deep_read_at", None)

    return entry


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild or update research/source-manifest.json"
    )
    parser.add_argument(
        "--key",
        type=str,
        default=None,
        help="Update only this BibTeX key (default: full rebuild)",
    )
    args = parser.parse_args()

    manifest = load_manifest()

    if args.key:
        # Single key update
        manifest[args.key] = build_entry(args.key, manifest.get(args.key))
        save_manifest(manifest)
        return

    # Full rebuild — collect all known keys from all sources
    all_keys = set()
    all_keys.update(extract_bib_keys())

    sources_path = Path(SOURCES_DIR)
    if sources_path.exists():
        all_keys.update(f.stem for f in sources_path.glob("*.md"))

    attachments_path = Path(ATTACHMENTS_DIR)
    if attachments_path.exists():
        all_keys.update(f.stem for f in attachments_path.glob("*.pdf"))

    parsed_path = Path(PARSED_DIR)
    if parsed_path.exists():
        all_keys.update(f.stem for f in parsed_path.glob("*.md"))

    if not all_keys:
        print("No sources found. Nothing to manifest.")
        return

    new_manifest = {}
    for key in sorted(all_keys):
        new_manifest[key] = build_entry(key, manifest.get(key))

    save_manifest(new_manifest)

    # Summary
    stats = {
        "total": len(new_manifest),
        "with_pdf": sum(1 for e in new_manifest.values() if "pdf" in e),
        "with_parsed_md": sum(1 for e in new_manifest.values() if "parsed_md" in e),
        "with_source_extract": sum(1 for e in new_manifest.values() if "source_extract" in e),
        "deep_read": sum(1 for e in new_manifest.values() if e.get("deep_read")),
        "full_text": sum(1 for e in new_manifest.values() if e.get("access_level") == "FULL-TEXT"),
        "abstract_only": sum(1 for e in new_manifest.values() if e.get("access_level") == "ABSTRACT-ONLY"),
        "metadata_only": sum(1 for e in new_manifest.values() if e.get("access_level") == "METADATA-ONLY"),
    }
    print(
        f"  {stats['total']} sources | "
        f"{stats['with_pdf']} PDFs | "
        f"{stats['with_parsed_md']} parsed | "
        f"{stats['deep_read']} deep-read | "
        f"{stats['full_text']} full-text / "
        f"{stats['abstract_only']} abstract / "
        f"{stats['metadata_only']} metadata"
    )


if __name__ == "__main__":
    main()
