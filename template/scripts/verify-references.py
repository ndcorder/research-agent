#!/usr/bin/env python3
"""Verify reference integrity: every citation has backing artifacts.

Checks that each \\cite/\\citep/\\citet key in main.tex has a BibTeX entry,
source extract, content snapshot, and appropriate access level. Optionally
removes fabricated references (--fix) and reports results as JSON (--json).

Usage:
    python3 scripts/verify-references.py                    # verify
    python3 scripts/verify-references.py --fix              # verify + auto-remediate
    python3 scripts/verify-references.py --json             # JSON output
    python3 scripts/verify-references.py --check            # exit 1 if FABRICATED found

Exit codes:
    0 — all references verified (or only warnings)
    1 — FABRICATED references found (with --check)
    2 — error (missing files, parse failure)
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TEX_FILE = "main.tex"
BIB_FILE = "references.bib"
SOURCES_DIR = "research/sources"
ATTACHMENTS_DIR = "attachments"
PARSED_DIR = "attachments/parsed"
OUTPUT_FILE = "research/reference_integrity.json"
PROVENANCE_FILE = "research/provenance.jsonl"

# Matches \cite{keys}, \citep{keys}, \citet{keys} — not in comments
CITE_RE = re.compile(r"\\cite[pt]?\{([^}]+)\}")


def _strip_latex_comment(line: str) -> str:
    """Strip the portion of a LaTeX line after an unescaped % comment character."""
    i = 0
    while i < len(line):
        if line[i] == "%" and (i == 0 or line[i - 1] != "\\"):
            return line[:i]
        i += 1
    return line


def parse_citations(tex_path: Path) -> list[dict]:
    """Extract all citation keys from a LaTeX file with line numbers and context.

    Returns a list of dicts: {"key": str, "line": int, "context": str, "cmd": str}
    Each key in a multi-key citation (e.g., \\citep{a,b,c}) produces a separate entry.
    Commented-out lines (starting with %) are skipped, and mid-line comments
    (text after an unescaped %) are stripped before matching.
    """
    results = []
    text = tex_path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue
        # Strip mid-line comments: find first unescaped %
        active = _strip_latex_comment(line)
        for match in CITE_RE.finditer(active):
            keys_str = match.group(1)
            cmd = match.group(0).split("{")[0]  # e.g., \citep
            context = line.strip()
            for key in keys_str.split(","):
                key = key.strip()
                if key:
                    results.append({
                        "key": key,
                        "line": lineno,
                        "context": context,
                        "cmd": cmd,
                    })
    return results


# Matches @type{key, ... } blocks
BIB_ENTRY_RE = re.compile(
    r"@(\w+)\s*\{([^,]+),\s*(.*?)\n\s*\}",
    re.DOTALL,
)
BIB_FIELD_RE = re.compile(
    r"(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}",
)


def parse_bib(bib_path: Path) -> dict[str, dict]:
    """Parse a BibTeX file into a dict keyed by citation key.

    Each value is a dict with fields: type, title, author, year, doi, eprint, etc.
    Field values have outer braces stripped.
    """
    entries = {}
    text = bib_path.read_text(encoding="utf-8")
    for match in BIB_ENTRY_RE.finditer(text):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()
        body = match.group(3)
        fields = {"type": entry_type}
        for field_match in BIB_FIELD_RE.finditer(body):
            field_name = field_match.group(1).lower()
            field_value = field_match.group(2).strip()
            # Strip one layer of outer braces if present
            if field_value.startswith("{") and field_value.endswith("}"):
                field_value = field_value[1:-1]
            fields[field_name] = field_value
        entries[key] = fields
    return entries


ACCESS_LEVEL_RE = re.compile(r"\*\*Access Level\*\*:\s*(FULL-TEXT|ABSTRACT-ONLY|METADATA-ONLY)")
SNAPSHOT_HEADER_RE = re.compile(r"^##\s+Content Snapshot", re.MULTILINE)
# Phrases that indicate an empty/placeholder snapshot
EMPTY_SNAPSHOT_PHRASES = [
    "no content accessed",
    "metadata only",
    "no content available",
]


def check_source_extract(key: str, sources_dir: Path) -> dict:
    """Check if a source extract exists and has meaningful content.

    Returns: {"has_extract": bool, "has_snapshot": bool, "access_level": str|None}
    """
    extract_path = sources_dir / f"{key}.md"
    if not extract_path.exists():
        return {"has_extract": False, "has_snapshot": False, "access_level": None}

    text = extract_path.read_text(encoding="utf-8")

    # Access level
    access_match = ACCESS_LEVEL_RE.search(text)
    access_level = access_match.group(1) if access_match else None

    # Content snapshot — must exist and have real content
    has_snapshot = False
    snapshot_match = SNAPSHOT_HEADER_RE.search(text)
    if snapshot_match:
        # Get text after the header until the next ## or end of file
        after_header = text[snapshot_match.end():]
        next_section = re.search(r"^##\s", after_header, re.MULTILINE)
        snapshot_text = after_header[:next_section.start()] if next_section else after_header
        snapshot_text = snapshot_text.strip()
        # Check it's not just a placeholder
        if snapshot_text and not any(
            phrase in snapshot_text.lower() for phrase in EMPTY_SNAPSHOT_PHRASES
        ):
            has_snapshot = True

    return {"has_extract": True, "has_snapshot": has_snapshot, "access_level": access_level}


def check_artifacts(key: str, attachments_dir: Path, parsed_dir: Path) -> dict:
    """Check if a source has a PDF and/or parsed markdown.

    Returns: {"has_pdf": bool, "has_parsed": bool}
    """
    has_pdf = (attachments_dir / f"{key}.pdf").exists()
    has_parsed = parsed_dir.exists() and (parsed_dir / f"{key}.md").exists()
    return {"has_pdf": has_pdf, "has_parsed": has_parsed}


def classify_reference(
    key: str,  # noqa: ARG001 — kept for API surface / logging
    in_bib: bool,
    extract: dict,
    artifacts: dict,  # noqa: ARG001 — reserved for future artifact-level checks
) -> str:
    """Classify a reference's integrity status.

    Returns one of: VERIFIED, MISSING_BIB, MISSING_EXTRACT, EMPTY_SNAPSHOT,
    METADATA_OVERCLAIM, FABRICATED.
    """
    if not in_bib:
        return "MISSING_BIB"
    if not extract["has_extract"]:
        return "MISSING_EXTRACT"
    if extract["access_level"] == "METADATA-ONLY":
        return "METADATA_OVERCLAIM"
    if not extract["has_snapshot"]:
        return "EMPTY_SNAPSHOT"
    return "VERIFIED"


CROSSREF_API = "https://api.crossref.org/works/"
ARXIV_API = "https://export.arxiv.org/api/query?id_list="


def verify_crossref(doi: str) -> dict:
    """Check if a DOI exists in CrossRef.

    Returns: {"found": bool|None, "error": str|None}
    None means indeterminate (network error).
    """
    url = f"{CROSSREF_API}{doi}"
    req = urllib.request.Request(url, headers={"User-Agent": "research-agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return {"found": data.get("status") == "ok"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"found": False}
        return {"found": None, "error": f"HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"found": None, "error": str(e)}


def verify_arxiv(arxiv_id: str) -> dict:
    """Check if an arXiv ID exists.

    Returns: {"found": bool|None, "error": str|None}
    """
    url = f"{ARXIV_API}{arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "research-agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            # arXiv API returns <entry> elements for found papers
            return {"found": "<entry>" in content}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"found": None, "error": str(e)}


def remediate_fabricated(tex_path: Path, bib_path: Path, fabricated_keys: list[str]):
    """Remove fabricated references from main.tex and references.bib.

    - In tex: removes the key from \\cite commands. If it was the only key,
      replaces the entire \\cite{key} with a REMOVED comment.
    - In bib: removes the entire @type{key, ...} entry.
    """
    if not fabricated_keys:
        return

    fab_set = set(fabricated_keys)

    # --- Fix tex ---
    tex_text = tex_path.read_text(encoding="utf-8")

    def _replace_cite(match):
        cmd = match.group(0).split("{")[0]
        keys_str = match.group(1)
        keys = [k.strip() for k in keys_str.split(",")]
        remaining = [k for k in keys if k not in fab_set]
        removed = [k for k in keys if k in fab_set]
        if not remaining:
            # All keys fabricated — replace with comment
            comment = "% REMOVED: fabricated reference " + ", ".join(removed)
            return comment
        else:
            return f"{cmd}{{{','.join(remaining)}}}"

    tex_text = CITE_RE.sub(_replace_cite, tex_text)
    tex_path.write_text(tex_text, encoding="utf-8")

    # --- Fix bib ---
    bib_text = bib_path.read_text(encoding="utf-8")
    for key in fabricated_keys:
        # Remove @type{key, ... } block
        pattern = re.compile(
            r"@\w+\s*\{" + re.escape(key) + r"\s*,.*?\n\}\s*\n?",
            re.DOTALL,
        )
        bib_text = pattern.sub("", bib_text)
    bib_path.write_text(bib_text, encoding="utf-8")


def verify_all(
    tex_path: Path,
    bib_path: Path,
    sources_dir: Path,
    attachments_dir: Path,
    parsed_dir: Path,
    use_api: bool = True,
) -> dict:
    """Run the full verification pipeline.

    Returns a report dict suitable for JSON serialization.
    """
    citations = parse_citations(tex_path)
    bib_entries = parse_bib(bib_path) if bib_path.exists() else {}

    # Group citations by key
    unique_keys = sorted(set(c["key"] for c in citations))
    citations_by_key = {}
    for c in citations:
        citations_by_key.setdefault(c["key"], []).append(
            {"line": c["line"], "context": c["context"]}
        )

    results = {}
    summary = {
        "VERIFIED": 0,
        "MISSING_BIB": 0,
        "MISSING_EXTRACT": 0,
        "EMPTY_SNAPSHOT": 0,
        "METADATA_OVERCLAIM": 0,
        "FABRICATED": 0,
    }

    for key in unique_keys:
        in_bib = key in bib_entries
        extract = check_source_extract(key, sources_dir)
        artifacts = check_artifacts(key, attachments_dir, parsed_dir)

        status = classify_reference(key, in_bib, extract, artifacts)

        # API fallback for MISSING_EXTRACT: maybe the bib entry is real
        # but no one created a source extract
        api_check = None
        if use_api and status in ("MISSING_EXTRACT", "EMPTY_SNAPSHOT"):
            bib_entry = bib_entries.get(key, {})
            doi = bib_entry.get("doi")
            eprint = bib_entry.get("eprint")
            if doi:
                api_check = verify_crossref(doi)
                if api_check.get("found") is False:
                    status = "FABRICATED"
            elif eprint:
                api_check = verify_arxiv(eprint)
                if api_check.get("found") is False:
                    status = "FABRICATED"

        entry = {
            "status": status,
            "has_bib": in_bib,
            "has_extract": extract["has_extract"],
            "has_snapshot": extract["has_snapshot"],
            "access_level": extract["access_level"],
            "has_pdf": artifacts["has_pdf"],
            "has_parsed": artifacts["has_parsed"],
            "citations_in_tex": citations_by_key.get(key, []),
        }
        if api_check is not None:
            entry["api_check"] = api_check
        results[key] = entry
        summary[status] = summary.get(status, 0) + 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_citations": len(citations),
        "unique_keys": len(unique_keys),
        "results": results,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify reference integrity: every citation has backing artifacts.",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-remediate fabricated references (remove from tex and bib)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output JSON report to stdout",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit with code 1 if any FABRICATED references found",
    )
    parser.add_argument(
        "--no-api", action="store_true",
        help="Skip CrossRef/arXiv API verification (local checks only)",
    )
    parser.add_argument(
        "--tex", default=TEX_FILE,
        help=f"Path to LaTeX file (default: {TEX_FILE})",
    )
    parser.add_argument(
        "--bib", default=BIB_FILE,
        help=f"Path to BibTeX file (default: {BIB_FILE})",
    )
    args = parser.parse_args()

    tex_path = Path(args.tex)
    bib_path = Path(args.bib)
    sources_dir = Path(SOURCES_DIR)
    attachments_dir = Path(ATTACHMENTS_DIR)
    parsed_dir = Path(PARSED_DIR)

    if not tex_path.exists():
        print(f"Error: {tex_path} not found", file=sys.stderr)
        raise SystemExit(2)

    report = verify_all(
        tex_path=tex_path,
        bib_path=bib_path,
        sources_dir=sources_dir,
        attachments_dir=attachments_dir,
        parsed_dir=parsed_dir,
        use_api=not args.no_api,
    )

    # Write report JSON
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    fabricated = [k for k, v in report["results"].items() if v["status"] == "FABRICATED"]

    # Auto-remediate if requested
    if args.fix and fabricated:
        remediate_fabricated(tex_path, bib_path, fabricated)
        # Log to provenance
        prov_path = Path(PROVENANCE_FILE)
        if prov_path.parent.exists():
            with open(prov_path, "a") as f:
                for key in fabricated:
                    entry = {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "stage": "3c",
                        "agent": "verify-references",
                        "action": "cut",
                        "target": f"references/{key}",
                        "reasoning": f"Reference {key} classified as FABRICATED — "
                                     f"no source extract, failed API verification",
                        "diff_summary": f"Removed fabricated reference {key} from bib and tex",
                    }
                    f.write(json.dumps(entry) + "\n")
        print(f"Remediated {len(fabricated)} fabricated reference(s): {', '.join(fabricated)}")

    # Print summary
    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        total = report["unique_keys"]
        print(f"Reference integrity: {total} unique keys checked")
        for status, count in sorted(s.items()):
            if count > 0:
                marker = "✓" if status == "VERIFIED" else "✗" if status == "FABRICATED" else "⚠"
                print(f"  {marker} {status}: {count}")

    if args.check and fabricated:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
