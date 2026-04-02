#!/usr/bin/env python3
"""
Reviewer defense knowledge base preparation.

Reads structured project files (claims matrix, assumptions, methodology notes)
and generates narrative documents optimized for knowledge graph ingestion.

Usage:
    python scripts/reviewer-kb.py prepare                    # Generate research/prepared/
    python scripts/reviewer-kb.py build                      # prepare + knowledge.py build
    python scripts/reviewer-kb.py refresh                    # Incremental prepare + kg update
    python scripts/reviewer-kb.py defense-brief              # Pre-compute defense for all claims
    python scripts/reviewer-kb.py status                     # Report graph state + coverage
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CLAIMS_MATRIX = "research/claims_matrix.md"
ASSUMPTIONS_FILE = "research/assumptions.md"
METHODOLOGY_NOTES = "research/methodology-notes.md"
REVIEWS_DIR = "reviews"
PREPARED_DIR = "research/prepared"
KNOWLEDGE_DIR = "research/knowledge"
KNOWLEDGE_SCRIPT = "scripts/knowledge.py"
MAIN_TEX = "main.tex"

REVIEW_PRIORITY = [
    "SCHOLAR_EVALUATION.md",
    "technical.md",
    "evidence_gaps_theory.md",
    "codex_adversarial_review.md",
    "codex_risk_radar.md",
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class EvidenceSource:
    bibtex_key: str
    access_level: str  # "FT", "AO", "MO"
    directness: str    # "direct", "tangential"
    score: float


@dataclass
class Claim:
    id: str
    tier: str
    statement: str
    evidence: list[EvidenceSource] = field(default_factory=list)
    warrant: str = ""
    warrant_quality: str = ""
    qualifier: str = ""
    rebuttal: str = ""
    score: float = 0.0
    strength: str = ""
    sections: list[str] = field(default_factory=list)
    status: str = ""


@dataclass
class Assumption:
    id: str
    title: str
    category: str  # "CRITICAL", "RISKY", "REASONABLE", "STANDARD"
    statement: str = ""
    justification: str = ""
    consequence: str = ""
    mitigation: str = ""
    prior_art: str = ""


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

# Regex for evidence entries: bibtex_key (ACCESS,directness)=score
EVIDENCE_RE = re.compile(r"(\w+)\s*\((\w+),\s*(\w+)\)\s*=\s*([\d.]+)")

# Regex for warrant quality tag at end of warrant text
WARRANT_QUALITY_RE = re.compile(r"\((\w+)\)\s*$")


def _expand_access(abbrev: str) -> str:
    """Expand FT/AO/MO to human-readable form."""
    return {"FT": "Full-Text", "AO": "Abstract-Only", "MO": "Metadata-Only"}.get(
        abbrev, abbrev
    )


def _split_table_row(line: str) -> list[str]:
    """Split a pipe-delimited markdown table row into cells, stripping whitespace."""
    # Remove leading/trailing pipe then split on |
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _is_separator_row(line: str) -> bool:
    """Check if a line is a markdown table separator (|-|-|...)."""
    return bool(re.match(r"^\s*\|[\s\-:|]+\|\s*$", line))


def parse_claims_matrix(path: Path) -> list[Claim]:
    """
    Parse the claims matrix markdown table.

    Expected header:
    | # | Tier | Claim | Evidence Sources | Warrant (Quality) | Qualifier | Rebuttal | Score | Strength | Section | Status |
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    claims = []
    in_table = False
    header_indices: dict[str, int] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            if in_table:
                break  # End of table
            continue

        if _is_separator_row(stripped):
            in_table = True
            continue

        cells = _split_table_row(stripped)

        # Detect header row
        if not in_table and any(c.lower() in ("#", "tier", "claim") for c in cells[:3]):
            # Map header names to indices
            for i, c in enumerate(cells):
                cl = c.strip().lower()
                if cl == "#":
                    header_indices["id"] = i
                elif cl == "tier":
                    header_indices["tier"] = i
                elif cl == "claim":
                    header_indices["claim"] = i
                elif "evidence" in cl:
                    header_indices["evidence"] = i
                elif "warrant" in cl:
                    header_indices["warrant"] = i
                elif "qualifier" in cl:
                    header_indices["qualifier"] = i
                elif "rebuttal" in cl:
                    header_indices["rebuttal"] = i
                elif cl == "score":
                    header_indices["score"] = i
                elif cl == "strength":
                    header_indices["strength"] = i
                elif cl == "section":
                    header_indices["section"] = i
                elif cl == "status":
                    header_indices["status"] = i
            continue

        if not in_table or not header_indices:
            continue

        # Parse data row
        try:
            claim = _parse_claim_row(cells, header_indices)
            if claim:
                claims.append(claim)
        except Exception as e:
            cell_id = cells[header_indices.get("id", 0)] if cells else "?"
            print(f"  Warning: skipping malformed row {cell_id}: {e}", file=sys.stderr)

    return claims


def _parse_claim_row(cells: list[str], idx: dict[str, int]) -> Claim | None:
    """Parse a single table row into a Claim."""
    def get(key: str, default: str = "") -> str:
        i = idx.get(key)
        if i is None or i >= len(cells):
            return default
        return cells[i].strip()

    claim_id = get("id")
    if not claim_id or not claim_id.startswith("C"):
        return None

    # Parse evidence sources
    evidence_raw = get("evidence")
    evidence = []
    for m in EVIDENCE_RE.finditer(evidence_raw):
        evidence.append(EvidenceSource(
            bibtex_key=m.group(1),
            access_level=m.group(2),
            directness=m.group(3),
            score=float(m.group(4)),
        ))

    # Parse warrant and quality
    warrant_raw = get("warrant")
    warrant_quality = ""
    warrant_text = warrant_raw
    quality_match = WARRANT_QUALITY_RE.search(warrant_raw)
    if quality_match:
        warrant_quality = quality_match.group(1)
        warrant_text = warrant_raw[: quality_match.start()].strip()

    # Parse score
    score_str = get("score", "0")
    try:
        score = float(score_str)
    except ValueError:
        score = 0.0

    # Parse sections
    section_str = get("section")
    sections = [s.strip() for s in section_str.split(",") if s.strip()]

    return Claim(
        id=claim_id,
        tier=get("tier"),
        statement=get("claim"),
        evidence=evidence,
        warrant=warrant_text,
        warrant_quality=warrant_quality,
        qualifier=get("qualifier"),
        rebuttal=get("rebuttal"),
        score=score,
        strength=get("strength"),
        sections=sections,
        status=get("status"),
    )


def parse_assumptions(path: Path) -> list[Assumption]:
    """
    Parse assumptions.md by ### headings.

    Expected structure per assumption:
    ### XX-N: Title
    **Statement.** ...
    **Category.** CRITICAL|RISKY|REASONABLE|STANDARD
    **Justification.** ...
    **Consequence if violated.** ...
    **Mitigation.** ...
    **Prior art.** ...
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    assumptions: list[Assumption] = []
    current: Assumption | None = None

    heading_re = re.compile(r"^###\s+([\w-]+):\s+(.+)")
    field_re = re.compile(r"^\*\*(.+?)\.\*\*\s*(.*)")

    for line in lines:
        hm = heading_re.match(line)
        if hm:
            if current:
                assumptions.append(current)
            current = Assumption(id=hm.group(1), title=hm.group(2).strip(), category="")
            continue

        if current is None:
            continue

        fm = field_re.match(line)
        if fm:
            field_name = fm.group(1).lower()
            value = fm.group(2).strip()
            if "statement" in field_name:
                current.statement = value
            elif "category" in field_name:
                current.category = value.upper()
            elif "justification" in field_name:
                current.justification = value
            elif "consequence" in field_name:
                current.consequence = value
            elif "mitigation" in field_name:
                current.mitigation = value
            elif "prior art" in field_name:
                current.prior_art = value
        elif line.strip():
            # Continuation line — append to the last populated field
            _append_continuation(current, line.strip())

    if current:
        assumptions.append(current)

    return assumptions


def _append_continuation(assumption: Assumption, text: str):
    """Append continuation text to the last non-empty field of an assumption."""
    for field_name in ("prior_art", "mitigation", "consequence", "justification", "statement"):
        val = getattr(assumption, field_name)
        if val:
            setattr(assumption, field_name, val + " " + text)
            return


def decompose_methodology_notes(path: Path) -> list[tuple[str, str]]:
    """
    Split methodology-notes.md by ## headings.
    Returns list of (slug, content) tuples.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## ") and not line.startswith("###"):
            if current_title:
                sections.append((_slugify(current_title), "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = [line]
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections.append((_slugify(current_title), "\n".join(current_lines).strip()))

    return sections


def _slugify(title: str) -> str:
    """Convert a heading to a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:60]


# ---------------------------------------------------------------------------
# Document generators
# ---------------------------------------------------------------------------


def generate_claim_document(claim: Claim, all_claims: list[Claim]) -> str:
    """Generate a narrative .md document for a single claim."""
    tier_desc = {
        "A": "Empirically grounded descriptive claim",
        "B": "Mechanism claim with triangulated evidence",
        "C": "System-level claim / proposition",
    }.get(claim.tier, claim.tier)

    lines = [
        f"# Claim {claim.id}: {_short_title(claim.statement)}",
        "",
        f"**Claim ID**: {claim.id}",
        f"**Tier**: {claim.tier} — {tier_desc}",
        f"**Evidence Score**: {claim.score} ({claim.strength})",
        f"**Paper Sections**: {', '.join(claim.sections)}",
        "",
        "## Statement",
        "",
        claim.statement,
        "",
        "## Evidence Sources",
        "",
    ]

    for ev in claim.evidence:
        access = _expand_access(ev.access_level)
        lines.append(f"### {ev.bibtex_key} ({access}, {ev.directness}) — Score: {ev.score}")
        lines.append("")
        lines.append(
            f"{ev.bibtex_key} provides {ev.directness} evidence "
            f"at the {access.lower()} level (score {ev.score})."
        )
        lines.append("")

    lines.extend([
        "## Warrant",
        "",
        claim.warrant,
        "",
        f"**Quality**: {claim.warrant_quality}",
        "",
        "## Qualifier",
        "",
        claim.qualifier or "[No qualifier specified]",
        "",
        "## Rebuttal",
        "",
        claim.rebuttal or "[No rebuttal specified]",
        "",
        "## Connections",
        "",
    ])

    # Find connections: shared evidence sources with other claims
    my_keys = {ev.bibtex_key for ev in claim.evidence}
    related = []
    for other in all_claims:
        if other.id == claim.id:
            continue
        other_keys = {ev.bibtex_key for ev in other.evidence}
        shared = my_keys & other_keys
        if shared:
            related.append(
                f"- **{other.id}** ({_short_title(other.statement)}): "
                f"shared sources: {', '.join(sorted(shared))}"
            )

    if related:
        lines.extend(related)
    else:
        lines.append("- No shared evidence sources with other claims detected.")

    lines.append("")
    return "\n".join(lines)


def _short_title(statement: str) -> str:
    """Extract a short title from a claim statement (first ~60 chars to word boundary)."""
    if len(statement) <= 60:
        return statement
    truncated = statement[:60]
    last_space = truncated.rfind(" ")
    if last_space > 30:
        truncated = truncated[:last_space]
    return truncated + "..."


def generate_assumption_document(assumption: Assumption) -> str:
    """Generate a narrative .md document for a CRITICAL or RISKY assumption."""
    lines = [
        f"# Assumption: {assumption.title} ({assumption.id})",
        "",
        f"**Risk Level**: {assumption.category}",
        f"**If violated**: {assumption.consequence[:200]}..."
        if len(assumption.consequence) > 200
        else f"**If violated**: {assumption.consequence}",
        "",
        "## The Assumption",
        "",
        assumption.statement,
        "",
        "## Why This Choice",
        "",
        assumption.justification or "[No justification provided]",
        "",
        "## What Could Go Wrong",
        "",
        assumption.consequence or "[No consequence specified]",
        "",
        "## How the Paper Addresses This",
        "",
        assumption.mitigation or "[No mitigation specified]",
        "",
        "## What the Literature Says",
        "",
        assumption.prior_art or "[No prior art cited]",
        "",
    ]
    return "\n".join(lines)


def generate_bundled_assumptions(assumptions: list[Assumption]) -> str:
    """Bundle REASONABLE and STANDARD assumptions into a single document."""
    lines = [
        "# Standard and Reasonable Assumptions",
        "",
        f"This document bundles {len(assumptions)} assumptions that are "
        "standard practice or reasonable choices in the field.",
        "",
    ]

    for a in assumptions:
        lines.extend([
            f"## {a.id}: {a.title}",
            "",
            f"**Category**: {a.category}",
            "",
            a.statement,
            "",
            f"**Justification**: {a.justification}" if a.justification else "",
            f"**If violated**: {a.consequence}" if a.consequence else "",
            "",
        ])

    return "\n".join(lines)


def generate_methodology_template(main_tex: Path) -> str:
    """
    Scan main.tex for dataset/analysis references and generate a template
    methodology notes file with section headers and prompts.
    """
    lines = [
        "# Methodology Notes",
        "",
        "This document records every analytical decision that involved a judgment call.",
        "Each section covers one analysis. For each decision within an analysis, document:",
        "- What you chose",
        "- What alternatives existed",
        "- Why you chose this option",
        "- How sensitive results are to this choice",
        "",
        "The reviewer-kb system decomposes this into per-analysis files for knowledge",
        "graph ingestion.",
        "",
        "---",
        "",
    ]

    # Heuristic: scan main.tex for analysis-related patterns
    if main_tex.exists():
        tex = main_tex.read_text(encoding="utf-8", errors="replace")
        # Find section headings that might be methods/analysis
        section_re = re.compile(r"\\(?:sub)*section\{([^}]+)\}")
        data_indicators = re.compile(
            r"(?:dataset|sample|n\s*=\s*\d|chi-square|regression|CAGR|"
            r"Monte\s*Carlo|Jaccard|statistical|classification|coding|"
            r"analysis|methodology)",
            re.IGNORECASE,
        )
        found_sections = []
        for m in section_re.finditer(tex):
            title = m.group(1)
            # Check surrounding context (~500 chars) for data indicators
            start = max(0, m.start() - 100)
            end = min(len(tex), m.end() + 500)
            context = tex[start:end]
            if data_indicators.search(context):
                found_sections.append(title)

        if found_sections:
            for section_title in found_sections:
                lines.extend([
                    f"## {section_title}",
                    "",
                    "### Data source",
                    "- Dataset: [TODO]",
                    "- Access: [TODO]",
                    "",
                    "### Decision: [TODO: name the decision]",
                    "- **Choice**: [TODO]",
                    "- **Alternatives**: [TODO]",
                    "- **Rationale**: [TODO]",
                    "- **Sensitivity**: [TODO]",
                    "",
                    "---",
                    "",
                ])
        else:
            lines.extend([
                "## [Analysis Name]",
                "",
                "### Data source",
                "- Dataset: [TODO]",
                "",
                "### Decision: [TODO]",
                "- **Choice**: [TODO]",
                "- **Alternatives**: [TODO]",
                "- **Rationale**: [TODO]",
                "- **Sensitivity**: [TODO]",
                "",
            ])

    return "\n".join(lines)


def select_reviews(reviews_dir: Path) -> list[Path]:
    """
    Select high-value review artifacts for ingestion.
    Priority files are always included. Latest iteration files are included.
    """
    if not reviews_dir.is_dir():
        return []

    selected: list[Path] = []

    # Priority files
    for name in REVIEW_PRIORITY:
        p = reviews_dir / name
        if p.exists():
            selected.append(p)

    # Find latest auto_iter files
    iter_re = re.compile(r"auto_iter(\d+)_(.+)\.md$")
    max_iter = 0
    for f in reviews_dir.iterdir():
        m = iter_re.match(f.name)
        if m:
            max_iter = max(max_iter, int(m.group(1)))

    if max_iter > 0:
        for f in sorted(reviews_dir.iterdir()):
            if f.name.startswith(f"auto_iter{max_iter}_") and f.suffix == ".md":
                if f not in selected:
                    selected.append(f)

    return selected


def prepare_review_document(review_path: Path) -> str:
    """Wrap a review file with a header for graph ingestion."""
    content = review_path.read_text(encoding="utf-8")
    stat = review_path.stat()
    mod_date = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")

    # Determine type from filename
    name = review_path.stem
    type_map = {
        "SCHOLAR_EVALUATION": "Comprehensive quality assessment",
        "technical": "Technical critique",
        "evidence_gaps_theory": "Evidence gap analysis",
        "codex_adversarial_review": "Adversarial AI review (Codex)",
        "codex_risk_radar": "Risk assessment (Codex)",
    }
    review_type = type_map.get(name, f"Auto-iteration review ({name})")

    header = (
        f"# Internal Review: {name.replace('_', ' ').title()}\n\n"
        f"**Type**: {review_type}\n"
        f"**Generated**: {mod_date}\n"
        f"**Role in paper**: Pre-submission self-review\n\n"
    )
    return header + content


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_prepare(args):
    """Generate research/prepared/ from project files."""
    prepared = Path(PREPARED_DIR)
    counts = {"claims": 0, "methodology": 0, "assumptions": 0, "reviews": 0}
    skipped = []

    # --- Claims ---
    claims_path = Path(CLAIMS_MATRIX)
    all_claims: list[Claim] = []
    if claims_path.exists():
        print(f"Parsing {CLAIMS_MATRIX}...")
        all_claims = parse_claims_matrix(claims_path)
        if all_claims:
            claims_dir = prepared / "claims"
            claims_dir.mkdir(parents=True, exist_ok=True)
            for claim in all_claims:
                doc = generate_claim_document(claim, all_claims)
                out = claims_dir / f"{claim.id}.md"
                out.write_text(doc, encoding="utf-8")
                counts["claims"] += 1
            print(f"  Generated {counts['claims']} claim documents")
        else:
            print("  Warning: no claims parsed from matrix", file=sys.stderr)
    else:
        skipped.append("claims_matrix.md (not found)")

    # --- Methodology notes ---
    meth_path = Path(METHODOLOGY_NOTES)
    if meth_path.exists():
        print(f"Parsing {METHODOLOGY_NOTES}...")
        sections = decompose_methodology_notes(meth_path)
        if sections:
            meth_dir = prepared / "methodology"
            meth_dir.mkdir(parents=True, exist_ok=True)
            for slug, content in sections:
                out = meth_dir / f"{slug}.md"
                out.write_text(content, encoding="utf-8")
                counts["methodology"] += 1
            print(f"  Generated {counts['methodology']} methodology documents")
    else:
        # Generate template
        main_tex_path = Path(MAIN_TEX)
        template = generate_methodology_template(main_tex_path)
        meth_path.parent.mkdir(parents=True, exist_ok=True)
        meth_path.write_text(template, encoding="utf-8")
        print(f"  Generated template: {METHODOLOGY_NOTES}")
        print("  Fill in methodology-notes.md and re-run prepare.")
        skipped.append("methodology-notes.md (template generated)")

    # --- Assumptions ---
    assumptions_path = Path(ASSUMPTIONS_FILE)
    if assumptions_path.exists():
        print(f"Parsing {ASSUMPTIONS_FILE}...")
        all_assumptions = parse_assumptions(assumptions_path)
        if all_assumptions:
            assumptions_dir = prepared / "assumptions"
            assumptions_dir.mkdir(parents=True, exist_ok=True)

            critical_risky = []
            standard_reasonable = []
            for a in all_assumptions:
                if a.category in ("CRITICAL", "RISKY"):
                    critical_risky.append(a)
                else:
                    standard_reasonable.append(a)

            for a in critical_risky:
                doc = generate_assumption_document(a)
                slug = _slugify(f"{a.category.lower()}-{a.id}-{a.title}")
                out = assumptions_dir / f"{slug}.md"
                out.write_text(doc, encoding="utf-8")
                counts["assumptions"] += 1

            if standard_reasonable:
                doc = generate_bundled_assumptions(standard_reasonable)
                out = assumptions_dir / "standard-and-reasonable.md"
                out.write_text(doc, encoding="utf-8")
                counts["assumptions"] += 1

            print(
                f"  Generated {counts['assumptions']} assumption documents "
                f"({len(critical_risky)} individual + "
                f"{'1 bundle' if standard_reasonable else '0 bundles'})"
            )
        else:
            print("  Warning: no assumptions parsed", file=sys.stderr)
    else:
        skipped.append("assumptions.md (not found)")

    # --- Reviews ---
    reviews_path = Path(REVIEWS_DIR)
    selected = select_reviews(reviews_path)
    if selected:
        print(f"Selecting {len(selected)} review artifacts...")
        reviews_out = prepared / "reviews"
        reviews_out.mkdir(parents=True, exist_ok=True)
        for review_file in selected:
            doc = prepare_review_document(review_file)
            out = reviews_out / review_file.name
            out.write_text(doc, encoding="utf-8")
            counts["reviews"] += 1
        print(f"  Prepared {counts['reviews']} review documents")
    else:
        skipped.append("reviews/ (no review files found)")

    # Summary
    total = sum(counts.values())
    print(f"\nPrepare complete: {total} documents in {PREPARED_DIR}/")
    if skipped:
        print(f"Skipped: {', '.join(skipped)}")

    return all_claims


def cmd_build(args):
    """Run prepare, then call knowledge.py build."""
    cmd_prepare(args)

    print(f"\nRunning knowledge.py build...")
    result = subprocess.run(
        [sys.executable, KNOWLEDGE_SCRIPT, "build"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Error: knowledge.py build failed", file=sys.stderr)
        sys.exit(1)

    _print_graph_summary()


def cmd_refresh(args):
    """Incremental prepare (check mtimes) + knowledge.py update."""
    prepared = Path(PREPARED_DIR)

    # Check if prepared/ exists and get its newest file mtime
    newest_prepared = 0.0
    if prepared.exists():
        for f in prepared.rglob("*.md"):
            newest_prepared = max(newest_prepared, f.stat().st_mtime)

    # Check source file mtimes
    needs_refresh = False
    for src in (CLAIMS_MATRIX, ASSUMPTIONS_FILE, METHODOLOGY_NOTES):
        p = Path(src)
        if p.exists() and p.stat().st_mtime > newest_prepared:
            needs_refresh = True
            break

    # Check review files
    reviews_path = Path(REVIEWS_DIR)
    if reviews_path.is_dir():
        for f in reviews_path.iterdir():
            if f.suffix == ".md" and f.stat().st_mtime > newest_prepared:
                needs_refresh = True
                break

    if needs_refresh or not prepared.exists():
        print("Source files changed, running prepare...")
        cmd_prepare(args)
    else:
        print("Prepared documents are up to date.")

    print(f"\nRunning knowledge.py update...")
    result = subprocess.run(
        [sys.executable, KNOWLEDGE_SCRIPT, "update"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Error: knowledge.py update failed", file=sys.stderr)
        sys.exit(1)

    _print_graph_summary()


def cmd_defense_brief(args):
    """Pre-compute defense for all claims."""
    # Verify graph exists
    kg_dir = Path(KNOWLEDGE_DIR)
    if not kg_dir.exists() or not any(kg_dir.iterdir()):
        print(
            "Error: Knowledge graph not found. Run 'build' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse claims
    claims_path = Path(CLAIMS_MATRIX)
    if not claims_path.exists():
        print(f"Error: {CLAIMS_MATRIX} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing claims matrix...")
    claims = parse_claims_matrix(claims_path)
    if not claims:
        print("Error: no claims found in matrix.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(claims)} claims. Generating defense brief...\n")

    # Create output directories
    defense_dir = Path(PREPARED_DIR) / "defense"
    defense_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Collect per-claim defense content
    brief_sections = []
    for claim in claims:
        print(f"  Querying graph for {claim.id}: {_short_title(claim.statement)}")

        evidence_for = _query_knowledge("evidence-for", claim.statement)
        evidence_against = _query_knowledge("evidence-against", claim.statement)

        # Build per-claim defense sheet
        sheet = _build_claim_defense_sheet(claim, evidence_for, evidence_against)

        # Write individual claim sheet
        sheet_path = defense_dir / f"claim-{claim.id}.md"
        sheet_path.write_text(sheet, encoding="utf-8")

        brief_sections.append(sheet)

    # Global analyses
    print("\n  Running global contradiction analysis...")
    contradictions = _query_knowledge("contradictions", "")

    print("  Running manuscript coverage analysis...")
    main_tex_path = Path(MAIN_TEX)
    if main_tex_path.exists():
        coverage = _query_knowledge("coverage", MAIN_TEX)
    else:
        coverage = "[main.tex not found — coverage analysis skipped]"

    # Global assumption vulnerabilities
    print("  Analyzing methodology vulnerabilities...")
    assumption_queries = []
    assumptions_path = Path(ASSUMPTIONS_FILE)
    if assumptions_path.exists():
        all_assumptions = parse_assumptions(assumptions_path)
        for a in all_assumptions:
            if a.category in ("CRITICAL", "RISKY"):
                result = _query_knowledge(
                    "query",
                    f"challenges to assumption: {a.title}. {a.statement}",
                )
                assumption_queries.append((a, result))

    # Assemble full defense brief
    brief_lines = [
        "# Reviewer Defense Brief",
        "",
        f"Generated: {timestamp}",
        f"Claims analyzed: {len(claims)}",
        "",
        "---",
        "",
        "## Per-Claim Defense",
        "",
    ]

    for section in brief_sections:
        brief_lines.append(section)
        brief_lines.append("\n---\n")

    brief_lines.extend([
        "## Global: Methodology Vulnerabilities",
        "",
    ])
    if assumption_queries:
        for a, result in assumption_queries:
            brief_lines.extend([
                f"### {a.id}: {a.title} ({a.category})",
                "",
                result or "[No evidence found in graph]",
                "",
            ])
    else:
        brief_lines.append("[No CRITICAL or RISKY assumptions to analyze]")
        brief_lines.append("")

    brief_lines.extend([
        "---",
        "",
        "## Global: Uncovered Entities",
        "",
        coverage or "[No coverage data]",
        "",
        "---",
        "",
        "## Global: Contradiction Summary",
        "",
        contradictions or "[No contradictions detected]",
        "",
    ])

    # Write the full brief
    brief_path = defense_dir / "defense-brief.md"
    brief_path.write_text("\n".join(brief_lines), encoding="utf-8")

    print(f"\nDefense brief written to {brief_path}")
    print(f"Per-claim sheets: {defense_dir}/claim-C*.md")


def _build_claim_defense_sheet(
    claim: Claim, evidence_for: str, evidence_against: str
) -> str:
    """Assemble a per-claim defense sheet."""
    lines = [
        f"### {claim.id}: {_short_title(claim.statement)}",
        "",
        f"**Tier**: {claim.tier} | **Score**: {claim.score} ({claim.strength})"
        f" | **Sections**: {', '.join(claim.sections)}",
        "",
        "#### Supporting Evidence (from graph)",
        "",
        evidence_for or "[No evidence found in graph]",
        "",
        "#### Potential Challenges (from graph)",
        "",
        evidence_against or "[No evidence found in graph]",
        "",
        "#### Warrant and Known Rebuttals",
        "",
        f"**Warrant** ({claim.warrant_quality}): {claim.warrant[:300]}"
        + ("..." if len(claim.warrant) > 300 else ""),
        "",
        f"**Qualifier**: {claim.qualifier or '[None]'}",
        "",
        f"**Rebuttal**: {claim.rebuttal or '[None]'}",
        "",
    ]
    return "\n".join(lines)


def _query_knowledge(command: str, argument: str) -> str:
    """Run a knowledge.py query command and return stdout."""
    cmd = [sys.executable, KNOWLEDGE_SCRIPT, command]
    if argument:
        cmd.append(argument)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                print(f"    Warning: {command} returned error: {stderr[:100]}", file=sys.stderr)
            return "[Query failed]"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"    Warning: {command} timed out", file=sys.stderr)
        return "[Query timed out]"
    except Exception as e:
        print(f"    Warning: {command} error: {e}", file=sys.stderr)
        return "[Query error]"


def cmd_status(args):
    """Report on knowledge graph state."""
    print("Reviewer Knowledge Base Status")
    print("=" * 40)

    # Claims matrix
    claims_path = Path(CLAIMS_MATRIX)
    if claims_path.exists():
        claims = parse_claims_matrix(claims_path)
        print(f"\nClaims matrix: found ({len(claims)} claims)")
        by_strength: dict[str, int] = {}
        for c in claims:
            by_strength[c.strength] = by_strength.get(c.strength, 0) + 1
        for strength, count in sorted(by_strength.items()):
            print(f"  {strength}: {count}")
    else:
        print(f"\nClaims matrix: not found")

    # Assumptions
    assumptions_path = Path(ASSUMPTIONS_FILE)
    if assumptions_path.exists():
        assumptions = parse_assumptions(assumptions_path)
        print(f"\nAssumptions: found ({len(assumptions)} total)")
        by_cat: dict[str, int] = {}
        for a in assumptions:
            by_cat[a.category] = by_cat.get(a.category, 0) + 1
        for cat in ("CRITICAL", "RISKY", "REASONABLE", "STANDARD"):
            if cat in by_cat:
                print(f"  {cat}: {by_cat[cat]}")
    else:
        print(f"\nAssumptions: not found")

    # Methodology notes
    meth_path = Path(METHODOLOGY_NOTES)
    print(f"\nMethodology notes: {'found' if meth_path.exists() else 'not found'}")

    # Prepared directory
    prepared = Path(PREPARED_DIR)
    if prepared.exists():
        file_counts: dict[str, int] = {}
        for f in prepared.rglob("*.md"):
            subdir = f.relative_to(prepared).parts[0] if len(f.relative_to(prepared).parts) > 1 else "root"
            file_counts[subdir] = file_counts.get(subdir, 0) + 1
        total = sum(file_counts.values())
        print(f"\nPrepared directory: {total} files")
        for subdir, count in sorted(file_counts.items()):
            print(f"  {subdir}/: {count}")
    else:
        print(f"\nPrepared directory: not created (run 'prepare')")

    # Knowledge graph
    kg_dir = Path(KNOWLEDGE_DIR)
    if kg_dir.exists():
        last_build_file = kg_dir / ".last_build"
        if last_build_file.exists():
            build_time = last_build_file.read_text(encoding="utf-8").strip()
            print(f"\nKnowledge graph: built ({build_time})")
        else:
            print(f"\nKnowledge graph: directory exists (no build timestamp)")

        # Count files in the graph directory
        graph_files = list(kg_dir.glob("*"))
        non_hidden = [f for f in graph_files if not f.name.startswith(".")]
        print(f"  Graph files: {len(non_hidden)}")
    else:
        print(f"\nKnowledge graph: not built (run 'build')")

    # Defense brief
    defense_path = Path(PREPARED_DIR) / "defense" / "defense-brief.md"
    if defense_path.exists():
        stat = defense_path.stat()
        age = datetime.now(timezone.utc) - datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        )
        age_str = f"{age.days}d {age.seconds // 3600}h ago" if age.days else f"{age.seconds // 3600}h ago"
        print(f"\nDefense brief: exists ({age_str})")
        # Count per-claim sheets
        defense_dir = Path(PREPARED_DIR) / "defense"
        claim_sheets = list(defense_dir.glob("claim-C*.md"))
        print(f"  Per-claim sheets: {len(claim_sheets)}")
    else:
        print(f"\nDefense brief: not generated (run 'defense-brief')")

    # Source documents
    sources_dir = Path("research/sources")
    if sources_dir.is_dir():
        source_count = len(list(sources_dir.glob("*.md")))
        print(f"\nSource extracts: {source_count}")

    parsed_dir = Path("attachments/parsed")
    if parsed_dir.is_dir():
        parsed_count = len(list(parsed_dir.glob("*.md")))
        print(f"Parsed PDFs: {parsed_count}")

    pdf_dir = Path("attachments")
    if pdf_dir.is_dir():
        pdf_count = len(list(pdf_dir.glob("*.pdf")))
        print(f"PDF files: {pdf_count}")


def _print_graph_summary():
    """Print a brief summary after build/update."""
    prepared = Path(PREPARED_DIR)
    if prepared.exists():
        total = len(list(prepared.rglob("*.md")))
        print(f"\nPrepared documents ingested: {total}")

    kg_dir = Path(KNOWLEDGE_DIR)
    if kg_dir.exists():
        last_build_file = kg_dir / ".last_build"
        if last_build_file.exists():
            print(f"Last build: {last_build_file.read_text(encoding='utf-8').strip()}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Reviewer defense knowledge base preparation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare", help="Generate research/prepared/ from project files")
    subparsers.add_parser("build", help="Run prepare + knowledge.py build")
    subparsers.add_parser("refresh", help="Incremental prepare + knowledge.py update")
    subparsers.add_parser("defense-brief", help="Pre-compute defense for all claims")
    subparsers.add_parser("status", help="Report on graph state + coverage")

    args = parser.parse_args()

    commands = {
        "prepare": cmd_prepare,
        "build": cmd_build,
        "refresh": cmd_refresh,
        "defense-brief": cmd_defense_brief,
        "status": cmd_status,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
