#!/usr/bin/env python3
"""Multi-dimensional quality scoring engine for research papers.

Evaluates papers across 5 dimensions: evidence, writing, structure,
research depth, and provenance coverage. Produces a structured JSON
scorecard and human-readable text report.

Usage:
    python scripts/quality.py score [--format json|text] [--dimension all|evidence|writing|...] [--project .]
    python scripts/quality.py history
    python scripts/quality.py record-outcome <outcome> [--venue V] [--notes N]
    python scripts/quality.py insights
"""

import argparse
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Cross-paper analytics persistence
# ---------------------------------------------------------------------------

ANALYTICS_DIR = Path.home() / ".research-agent" / "analytics"


def save_score(paper_name: str, scorecard: dict, checkpoint: str = "manual") -> None:
    """Append a scorecard entry to ~/.research-agent/analytics/scores.jsonl."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "paper": paper_name,
        "checkpoint": checkpoint,
        "timestamp": scorecard.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "overall": scorecard.get("overall", 0),
        "grade": scorecard.get("grade", "F"),
    }
    dims = scorecard.get("dimensions", {})
    for dim_name in ("evidence", "writing", "structure", "research", "provenance"):
        entry[dim_name] = dims.get(dim_name, {}).get("score", 0)
    scores_path = ANALYTICS_DIR / "scores.jsonl"
    with open(scores_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_history(paper_name: str | None = None) -> list[dict]:
    """Read scores.jsonl, optionally filter by paper name."""
    scores_path = ANALYTICS_DIR / "scores.jsonl"
    if not scores_path.is_file():
        return []
    entries = []
    for line in scores_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if paper_name is None or entry.get("paper") == paper_name:
            entries.append(entry)
    return entries


def save_outcome(paper_name: str, outcome: str, venue: str = "", notes: str = "") -> None:
    """Append to ~/.research-agent/analytics/outcomes.jsonl."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "paper": paper_name,
        "outcome": outcome,
        "venue": venue,
        "notes": notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    outcomes_path = ANALYTICS_DIR / "outcomes.jsonl"
    with open(outcomes_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_claims_matrix(text: str) -> list:
    """Parse a markdown table from research/claims_matrix.md.

    Expected columns: ID, Claim, Evidence, Score, Strength, Warrant,
    Qualifier, Rebuttal.  Returns list of dicts with keys: id, claim,
    score (float), strength, warrant.
    """
    if not text.strip():
        return []

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Find the header row (first line starting with |)
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|") and "ID" in line.upper():
            header_idx = i
            break

    if header_idx is None:
        return []

    # Parse header to find column indices
    header_cells = [c.strip() for c in lines[header_idx].split("|")]
    # Remove empty strings from split
    header_cells = [c for c in header_cells if c]

    col_map = {}
    for i, cell in enumerate(header_cells):
        key = cell.strip().lower()
        col_map[key] = i

    # Require at minimum: id, score, strength, warrant
    required = {"id", "score", "strength", "warrant"}
    if not required.issubset(col_map.keys()):
        return []

    # Skip header and separator rows
    data_start = header_idx + 1
    # Skip separator row(s) that look like |-|-|
    while data_start < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[data_start]):
        data_start += 1

    claims = []
    for line in lines[data_start:]:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c is not None]
        # Filter out empty from leading/trailing |
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if len(cells) <= max(col_map.values()):
            continue

        try:
            score_val = float(cells[col_map["score"]])
        except (ValueError, IndexError):
            score_val = 0.0

        claims.append({
            "id": cells[col_map["id"]].strip(),
            "claim": cells[col_map.get("claim", col_map["id"])].strip() if "claim" in col_map else "",
            "score": score_val,
            "strength": cells[col_map["strength"]].strip().upper(),
            "warrant": cells[col_map["warrant"]].strip(),
        })

    return claims


def parse_source_extracts(sources_dir: Path) -> list:
    """Parse source extract .md files in research/sources/.

    Each has '**Access Level**: FULL-TEXT | ABSTRACT-ONLY | METADATA-ONLY'.
    Returns list of dicts with keys: key (filename stem), access_level.
    """
    if not sources_dir.is_dir():
        return []

    results = []
    for md_file in sorted(sources_dir.glob("*.md")):
        text = md_file.read_text(errors="replace")
        access_level = "METADATA-ONLY"  # default
        m = re.search(r"\*\*Access Level\*\*:\s*(FULL-TEXT|ABSTRACT-ONLY|METADATA-ONLY)", text)
        if m:
            access_level = m.group(1)
        results.append({"key": md_file.stem, "access_level": access_level})

    return results


def _strip_latex_commands(tex: str) -> str:
    """Strip LaTeX commands, leaving readable text for analysis."""
    # Remove comments
    text = re.sub(r"(?<!\\)%.*$", "", tex, flags=re.MULTILINE)
    # Remove math environments
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\$.*?\$", " ", text)
    text = re.sub(r"\\begin\{(?:equation|align|gather|math)\*?\}.*?\\end\{(?:equation|align|gather|math)\*?\}", " ", text, flags=re.DOTALL)
    # Remove cite/ref commands
    text = re.sub(r"\\(?:cite[pt]?|ref|cref|eqref|label)\{[^}]*\}", "", text)
    # Remove \begin{...} and \end{...}
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", text)
    # Keep text arguments of formatting commands like \textbf{foo} -> foo
    text = re.sub(r"\\(?:textbf|textit|emph|underline|textsc|textrm|texttt)\{([^}]*)\}", r"\1", text)
    # Remove remaining commands with arguments
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", text)
    # Remove remaining commands without arguments
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    # Remove braces
    text = re.sub(r"[{}]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_sentences(text: str) -> list:
    """Naive sentence splitter on .!? followed by space or end."""
    if not text.strip():
        return []
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


def _extract_provenance_targets(provenance_path: Path) -> set:
    """Extract unique 'target' values from provenance.jsonl.

    Only includes targets containing '/' that aren't 'all'.
    """
    targets = set()
    if not provenance_path.is_file():
        return targets
    for line in provenance_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            target = entry.get("target", "")
            if "/" in target and target != "all":
                targets.add(target)
        except (json.JSONDecodeError, AttributeError):
            continue
    return targets


def _estimate_paragraph_targets(tex: str) -> set:
    """Estimate paragraph targets from LaTeX using section/pN format.

    Track section headers and count text blocks per section.
    """
    targets = set()
    current_section = None
    para_count = 0
    in_text_block = False

    for line in tex.splitlines():
        stripped = line.strip()

        # Detect section and subsection headers
        m = re.match(r"\\(?:sub)*section\{([^}]+)\}", stripped)
        if m:
            section_name = m.group(1).lower().replace(" ", "-")
            # Simplified: map common names
            section_name = re.sub(r"[^a-z0-9-]", "", section_name)
            # Only top-level \section resets the current section for target keys
            if stripped.startswith(r"\section{"):
                current_section = section_name
                para_count = 0
                in_text_block = False
            # Subsections: keep parent section name, just reset text block tracking
            else:
                in_text_block = False
            continue

        if current_section is None:
            continue

        # Count paragraphs: non-empty, non-command lines start text blocks
        if stripped and not stripped.startswith("\\") and not stripped.startswith("%"):
            if not in_text_block:
                para_count += 1
                targets.add(f"{current_section}/p{para_count}")
                in_text_block = True
        elif not stripped:
            in_text_block = False

    return targets


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------

_STRENGTH_SCORES = {
    "STRONG": 100,
    "MODERATE": 60,
    "WEAK": 25,
    "CRITICAL": 0,
}

_WARRANT_ADJUSTMENTS = {
    "Sound": 5,
    "Reasonable": 0,
    "Weak": -5,
    "Missing": -15,
    "Invalid": -20,
}


def write_heatmap(claims: list, output_path: str = "research/evidence_heatmap.md") -> None:
    """Write a per-claim evidence heatmap for writing agents."""
    lines = [
        "# Evidence Density Heatmap",
        "",
        "Generated by `quality.py heatmap`. Writing agents: use this to calibrate confidence language.",
        "",
        "| Claim ID | Claim (truncated) | Score | Strength | Warrant | Writing Guidance |",
        "|-|-|-|-|-|-|",
    ]
    for c in claims:
        claim_text = c.get("claim", "")[:60]
        score = c.get("score", 0)
        strength = c.get("strength", "UNKNOWN")
        warrant = c.get("warrant", "Missing")
        if strength == "STRONG":
            guidance = "Write with full confidence. Use 'demonstrates', 'establishes', 'confirms'."
        elif strength == "MODERATE":
            guidance = "Write with measured confidence. Use 'shows', 'indicates', 'supports'."
        elif strength == "WEAK":
            guidance = "HEDGE required. Use 'suggests', 'may indicate', 'preliminary evidence points to'. Acknowledge limitation."
        elif strength == "CRITICAL":
            guidance = "DO NOT assert this claim as established. Frame as hypothesis or open question. Consider removing."
        else:
            guidance = "Score not available — use conservative language."
        lines.append(f"| {c.get('id', '?')} | {claim_text} | {score} | {strength} | {warrant} | {guidance} |")

    lines.extend([
        "",
        "## Summary",
        f"- STRONG claims: {sum(1 for c in claims if c.get('strength') == 'STRONG')}",
        f"- MODERATE claims: {sum(1 for c in claims if c.get('strength') == 'MODERATE')}",
        f"- WEAK claims: {sum(1 for c in claims if c.get('strength') == 'WEAK')}",
        f"- CRITICAL claims: {sum(1 for c in claims if c.get('strength') == 'CRITICAL')}",
        "",
        "WEAK and CRITICAL claims are vulnerability points. Prioritize strengthening evidence or hedging language.",
    ])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def score_evidence(claims: list) -> dict:
    """Score evidence quality from claims matrix.

    Returns {"score": 0-100, "details": {...}}.
    """
    if not claims:
        return {"score": 0, "details": {
            "claim_distribution": {},
            "total_claims": 0,
            "critical_count": 0,
            "avg_warrant_adjustment": 0,
            "base_score": 0,
        }}

    # Count distribution
    distribution = {}
    for c in claims:
        s = c.get("strength", "WEAK")
        distribution[s] = distribution.get(s, 0) + 1

    total = len(claims)
    critical_count = distribution.get("CRITICAL", 0)

    # Base score: weighted average of claim strengths
    base_score = sum(_STRENGTH_SCORES.get(c.get("strength", "WEAK"), 25) for c in claims) / total

    # Warrant adjustment: average across claims
    warrant_adjustments = []
    for c in claims:
        w = c.get("warrant", "Reasonable")
        warrant_adjustments.append(_WARRANT_ADJUSTMENTS.get(w, 0))
    avg_warrant_adj = sum(warrant_adjustments) / len(warrant_adjustments) if warrant_adjustments else 0

    # CRITICAL penalty
    critical_penalty = critical_count * 20

    score = base_score + avg_warrant_adj - critical_penalty
    score = max(0, min(100, round(score)))

    return {
        "score": score,
        "details": {
            "claim_distribution": distribution,
            "total_claims": total,
            "critical_count": critical_count,
            "avg_warrant_adjustment": round(avg_warrant_adj, 2),
            "base_score": round(base_score, 2),
        },
    }


# AI writing patterns to detect
_AI_PATTERNS = [
    # Single words / phrases
    r"\bdelve\b",
    r"\brealm\b",
    r"\blandscape\b",
    r"\btapestry\b",
    r"\bmultifaceted\b",
    r"\bgroundbreaking\b",
    r"\bcutting[\s-]edge\b",
    # Sentence-start patterns with comma
    r"(?:^|\.\s+)Furthermore,",
    r"(?:^|\.\s+)Moreover,",
    r"(?:^|\.\s+)Additionally,",
    # Filler phrases
    r"\bit is worth noting\b",
    r"\bit should be noted\b",
    r"\bit is important to\b",
    r"\bin order to\b",
    r"\bthe fact that\b",
    r"\ba total of\b",
    r"\bit can be observed that\b",
    r"\bit is evident that\b",
    # Em dashes (typographic and LaTeX)
    r"\u2014",        # —
    r"---",           # LaTeX em dash
    # En dashes not between numbers
    r"(?<!\d)\u2013(?!\d)",
]


def score_writing(tex: str) -> dict:
    """Score writing quality from LaTeX source.

    Returns {"score": 0-100, "details": {...}}.
    """
    text = _strip_latex_commands(tex)

    if not text.strip():
        return {"score": 0, "details": {
            "ai_pattern_count": 0,
            "ai_pattern_density_per_1k": 0,
            "sentence_length_stddev": 0,
            "sentence_count": 0,
            "word_count": 0,
            "bullet_count": 0,
        }}

    words = text.split()
    word_count = len(words)
    sentences = _split_sentences(text)
    sentence_count = len(sentences)

    # AI pattern detection (0-50 points)
    # Em dash patterns run against raw tex (LaTeX convention); word-level
    # patterns run against stripped plain text to avoid false positives on
    # LaTeX commands (e.g. \section{Furthermore}).
    _EM_DASH_PATTERNS = {r"\u2014", r"---", r"(?<!\d)\u2013(?!\d)"}
    ai_pattern_count = 0
    for pattern in _AI_PATTERNS:
        target = tex if pattern in _EM_DASH_PATTERNS else text
        ai_pattern_count += len(re.findall(pattern, target, re.IGNORECASE | re.MULTILINE))

    density = (ai_pattern_count / max(word_count, 1)) * 1000
    ai_score = max(0, 50 - density * 5)

    # Sentence variety (0-25 points)
    if sentence_count >= 2:
        lengths = [len(s.split()) for s in sentences]
        stddev = statistics.stdev(lengths)
    else:
        stddev = 0.0
    variety_score = min(25, stddev * 5)

    # Paragraph quality (0-25 points): penalize bullet points
    bullet_count = tex.count("\\item")
    para_score = max(0, 25 - bullet_count * 3)

    score = max(0, min(100, round(ai_score + variety_score + para_score)))

    return {
        "score": score,
        "details": {
            "ai_pattern_count": ai_pattern_count,
            "ai_pattern_density_per_1k": round(density, 2),
            "sentence_length_stddev": round(stddev, 2),
            "sentence_count": sentence_count,
            "word_count": word_count,
            "bullet_count": bullet_count,
        },
    }


def score_structure(tex: str, venue: dict, compile_ok: bool, compile_warnings: int) -> dict:
    """Score structural integrity of the paper.

    Returns {"score": 0-100, "details": {...}}.
    """
    required_sections = venue.get("sections", [])

    # Find section headings in tex
    found_sections = re.findall(r"\\section\{([^}]+)\}", tex)
    found_set = {s.strip().lower() for s in found_sections}
    required_set = {s.strip().lower() for s in required_sections}

    sections_found = [s for s in required_sections if s.strip().lower() in found_set]
    sections_missing = [s for s in required_sections if s.strip().lower() not in found_set]

    # Section completeness (0-30)
    if required_set:
        section_score = (len(sections_found) / len(required_set)) * 30
    else:
        section_score = 30  # No requirements = full marks

    # Compilation (0-30)
    if not compile_ok:
        compile_score = 0
    else:
        compile_score = max(0, 30 - compile_warnings * 2)

    # Placeholder absence (0-20)
    placeholder_count = 0
    for pattern in [r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\\lipsum"]:
        placeholder_count += len(re.findall(pattern, tex, re.IGNORECASE))
    placeholder_score = max(0, 20 - placeholder_count * 5)

    # Cross-ref health (0-20)
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    refs = set(re.findall(r"\\(?:ref|cref|eqref)\{([^}]+)\}", tex))
    unresolved = refs - labels
    if refs:
        ref_score = ((len(refs) - len(unresolved)) / len(refs)) * 20
    else:
        ref_score = 20  # No refs = no penalty

    score = max(0, min(100, round(section_score + compile_score + placeholder_score + ref_score)))

    return {
        "score": score,
        "details": {
            "sections_required": required_sections,
            "sections_found": sections_found,
            "sections_missing": sections_missing,
            "compile_ok": compile_ok,
            "compile_warnings": compile_warnings,
            "placeholder_count": placeholder_count,
            "labels": sorted(labels),
            "refs": sorted(refs),
            "unresolved_refs": sorted(unresolved),
        },
    }


def score_research(sources: list, citation_count: int, word_count: int, kg_available: bool) -> dict:
    """Score research depth.

    Returns {"score": 0-100, "details": {...}}.
    """
    if not sources:
        return {"score": 0, "details": {
            "total_sources": 0,
            "full_text": 0,
            "abstract_only": 0,
            "metadata_only": 0,
            "full_text_ratio": 0,
            "citation_count": citation_count,
            "citation_density_per_1k": 0,
            "knowledge_graph_available": kg_available,
        }}

    total = len(sources)
    full_text = sum(1 for s in sources if s.get("access_level") == "FULL-TEXT")
    abstract_only = sum(1 for s in sources if s.get("access_level") == "ABSTRACT-ONLY")
    metadata_only = sum(1 for s in sources if s.get("access_level") == "METADATA-ONLY")

    # Source access quality (0-35)
    access_weights = {"FULL-TEXT": 1.0, "ABSTRACT-ONLY": 0.4, "METADATA-ONLY": 0.1}
    weighted_sum = sum(access_weights.get(s.get("access_level", "METADATA-ONLY"), 0.1) for s in sources)
    access_score = (weighted_sum / total) * 35

    # Citation density (0-30): per 1000 words, target 15+
    citation_density = (citation_count / max(word_count, 1)) * 1000
    density_score = min(30, (citation_density / 15) * 30)

    # Source count (0-20): scaled to 30 sources = full score
    source_score = min(20, (total / 30) * 20)

    # Knowledge graph (0-15)
    kg_score = 15 if kg_available else 0

    score = max(0, min(100, round(access_score + density_score + source_score + kg_score)))

    return {
        "score": score,
        "details": {
            "total_sources": total,
            "full_text": full_text,
            "abstract_only": abstract_only,
            "metadata_only": metadata_only,
            "full_text_ratio": round(full_text / total, 2) if total else 0,
            "citation_count": citation_count,
            "citation_density_per_1k": round(citation_density, 2),
            "knowledge_graph_available": kg_available,
        },
    }


def score_provenance(traced_targets: set, all_targets: set) -> dict:
    """Score provenance coverage.

    Returns {"score": 0-100, "details": {...}}.
    """
    if not all_targets:
        return {"score": 0, "details": {
            "paragraphs_traced": 0,
            "paragraphs_total": 0,
            "coverage_ratio": 0,
            "untraced": [],
        }}

    intersection = traced_targets & all_targets
    coverage = len(intersection) / len(all_targets)
    score = max(0, min(100, round(coverage * 100)))

    untraced = sorted(all_targets - traced_targets)[:10]

    return {
        "score": score,
        "details": {
            "paragraphs_traced": len(intersection),
            "paragraphs_total": len(all_targets),
            "coverage_ratio": round(coverage, 4),
            "untraced": untraced,
        },
    }


# ---------------------------------------------------------------------------
# Scorecard computation
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "evidence": 0.30,
    "writing": 0.20,
    "structure": 0.15,
    "research": 0.20,
    "provenance": 0.15,
}


def _grade(score: int) -> str:
    """Map numeric score to letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C+"
    if score >= 50:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def compute_scorecard(project: Path) -> dict:
    """Orchestrate all scorers and produce a full scorecard."""
    # Read main.tex
    tex_path = project / "main.tex"
    tex = tex_path.read_text(errors="replace") if tex_path.is_file() else ""

    # Read .venue.json
    venue_path = project / ".venue.json"
    venue = {}
    if venue_path.is_file():
        try:
            venue = json.loads(venue_path.read_text(errors="replace"))
        except json.JSONDecodeError:
            pass

    # Read claims matrix
    claims_path = project / "research" / "claims_matrix.md"
    claims_text = claims_path.read_text(errors="replace") if claims_path.is_file() else ""
    claims = parse_claims_matrix(claims_text)

    # Read source extracts
    sources_dir = project / "research" / "sources"
    sources = parse_source_extracts(sources_dir)

    # Read provenance
    prov_path = project / "research" / "provenance.jsonl"
    traced_targets = _extract_provenance_targets(prov_path)

    # Estimate paragraph targets
    all_targets = _estimate_paragraph_targets(tex)

    # Parse compile status from main.log
    log_path = project / "main.log"
    compile_ok = False
    compile_warnings = 0
    if log_path.is_file():
        log_text = log_path.read_text(errors="replace")
        compile_ok = "Output written on" in log_text
        compile_warnings = len(re.findall(r"LaTeX Warning:", log_text))

    # Count citations in tex
    citation_count = len(re.findall(r"\\cite\w*\{[^}]*\}", tex))

    # Count words in stripped text
    stripped = _strip_latex_commands(tex)
    word_count = len(stripped.split()) if stripped.strip() else 0

    # Check knowledge graph availability
    kg_available = (project / "research" / "knowledge").is_dir()

    # Score each dimension
    ev = score_evidence(claims)
    wr = score_writing(tex)
    st = score_structure(tex, venue, compile_ok, compile_warnings)
    re_score = score_research(sources, citation_count, word_count, kg_available)
    pv = score_provenance(traced_targets, all_targets)

    dimensions = {
        "evidence": ev,
        "writing": wr,
        "structure": st,
        "research": re_score,
        "provenance": pv,
    }

    overall = round(
        ev["score"] * _WEIGHTS["evidence"]
        + wr["score"] * _WEIGHTS["writing"]
        + st["score"] * _WEIGHTS["structure"]
        + re_score["score"] * _WEIGHTS["research"]
        + pv["score"] * _WEIGHTS["provenance"]
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "dimensions": dimensions,
        "overall": overall,
        "grade": _grade(overall),
    }


def format_scorecard_text(scorecard: dict) -> str:
    """Format scorecard as human-readable text with bar charts."""
    lines = []
    lines.append("Paper Quality Scorecard")
    lines.append("=" * 40)
    lines.append("")

    dims = scorecard["dimensions"]
    for name in ("evidence", "writing", "structure", "research", "provenance"):
        s = dims[name]["score"]
        filled = round(s / 5)  # 20-char bar, each char = 5 points
        bar = "#" * filled + "." * (20 - filled)
        lines.append(f"  {name:<16} [{bar}] {s:>3}/100")

    lines.append("")
    lines.append(f"  {'OVERALL':<16}                       {scorecard['overall']:>3}/100  ({scorecard['grade']})")
    lines.append("")

    # Evidence details
    if dims["evidence"]["details"].get("total_claims", 0) > 0:
        lines.append("Evidence Details:")
        dist = dims["evidence"]["details"]["claim_distribution"]
        for strength in ("STRONG", "MODERATE", "WEAK", "CRITICAL"):
            if strength in dist:
                lines.append(f"  {strength}: {dist[strength]} claims")
        lines.append("")

    # Writing details
    wd = dims["writing"]["details"]
    if wd.get("word_count", 0) > 0:
        lines.append("Writing Details:")
        lines.append(f"  Words: {wd['word_count']}, Sentences: {wd['sentence_count']}")
        lines.append(f"  AI patterns: {wd['ai_pattern_count']} ({wd['ai_pattern_density_per_1k']:.1f}/1k words)")
        lines.append("")

    # Structure details
    sd = dims["structure"]["details"]
    if sd.get("sections_missing"):
        lines.append("Structure Details:")
        lines.append(f"  Missing sections: {', '.join(sd['sections_missing'])}")
        lines.append("")

    # Research details
    rd = dims["research"]["details"]
    if rd.get("total_sources", 0) > 0:
        lines.append("Research Details:")
        lines.append(f"  Sources: {rd['total_sources']} ({rd['full_text']} full-text, "
                     f"{rd['abstract_only']} abstract, {rd['metadata_only']} metadata)")
        lines.append(f"  Citation density: {rd['citation_density_per_1k']:.1f}/1k words")
        lines.append("")

    # Provenance details
    pd = dims["provenance"]["details"]
    if pd.get("paragraphs_total", 0) > 0:
        lines.append("Provenance Details:")
        lines.append(f"  Coverage: {pd['paragraphs_traced']}/{pd['paragraphs_total']} "
                     f"paragraphs ({pd['coverage_ratio']:.1%})")
        if pd.get("untraced"):
            lines.append(f"  Untraced: {', '.join(pd['untraced'][:5])}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_score(args):
    project = Path(args.project).resolve()
    if not (project / "main.tex").is_file():
        print(f"Error: {project / 'main.tex'} not found. Are you in a paper project?", file=sys.stderr)
        sys.exit(1)

    scorecard = compute_scorecard(project)

    if args.dimension != "all":
        dim = args.dimension
        if dim not in scorecard["dimensions"]:
            print(f"Error: unknown dimension '{dim}'", file=sys.stderr)
            sys.exit(1)
        # Filter to single dimension
        scorecard["dimensions"] = {dim: scorecard["dimensions"][dim]}

    if args.format == "json":
        print(json.dumps(scorecard, indent=2))
    else:
        print(format_scorecard_text(scorecard))


def _cmd_history(args):
    history = load_history(getattr(args, "paper", None))
    if not history:
        print("No scoring history found.")
        return
    # Header
    print(f"{'Paper':<30} {'Checkpoint':<12} {'Overall':>7} {'Grade':>5}  "
          f"{'Ev':>3} {'Wr':>3} {'St':>3} {'Re':>3} {'Pv':>3}  {'Timestamp'}")
    print("-" * 110)
    for entry in history:
        print(f"{entry.get('paper', '?'):<30} {entry.get('checkpoint', '?'):<12} "
              f"{entry.get('overall', 0):>7} {entry.get('grade', '?'):>5}  "
              f"{entry.get('evidence', 0):>3} {entry.get('writing', 0):>3} "
              f"{entry.get('structure', 0):>3} {entry.get('research', 0):>3} "
              f"{entry.get('provenance', 0):>3}  {entry.get('timestamp', '?')}")


def _cmd_record_outcome(args):
    project = Path(args.project).resolve() if hasattr(args, "project") else Path.cwd().resolve()
    paper_name = getattr(args, "name", None) or project.name
    venue = getattr(args, "venue", "") or ""
    notes = getattr(args, "notes", "") or ""
    save_outcome(paper_name, args.outcome, venue=venue, notes=notes)
    print(f"Recorded outcome '{args.outcome}' for paper '{paper_name}'.")


def _cmd_save(args):
    project = Path(args.project).resolve()
    if not (project / "main.tex").is_file():
        print(f"Error: {project / 'main.tex'} not found. Are you in a paper project?", file=sys.stderr)
        sys.exit(1)
    paper_name = args.name or project.name
    scorecard = compute_scorecard(project)
    save_score(paper_name, scorecard, checkpoint=args.checkpoint)
    print(f"Saved scores for '{paper_name}' (checkpoint: {args.checkpoint}, overall: {scorecard['overall']}/{scorecard['grade']})")


def _cmd_heatmap(args):
    project = Path(args.project).resolve()
    claims_path = project / "research" / "claims_matrix.md"
    if not claims_path.is_file():
        print(f"Error: {claims_path} not found. Run Stage 2 first.", file=sys.stderr)
        sys.exit(1)
    claims = parse_claims_matrix(claims_path.read_text(errors="replace"))
    if not claims:
        print("No claims found in claims matrix.", file=sys.stderr)
        sys.exit(1)
    output = str(project / "research" / "evidence_heatmap.md")
    write_heatmap(claims, output)
    strong = sum(1 for c in claims if c.get("strength") == "STRONG")
    moderate = sum(1 for c in claims if c.get("strength") == "MODERATE")
    weak = sum(1 for c in claims if c.get("strength") == "WEAK")
    critical = sum(1 for c in claims if c.get("strength") == "CRITICAL")
    print(f"Heatmap written to {output}")
    print(f"  {len(claims)} claims: {strong} STRONG, {moderate} MODERATE, {weak} WEAK, {critical} CRITICAL")


def _cmd_insights(args):
    """Analyze trends across all scored papers."""
    history = load_history()
    if not history:
        print("No quality scores recorded yet. Run /score on a paper project first.")
        return

    # Group by paper (use latest score per paper)
    papers = {}
    for entry in history:
        name = entry.get("paper", "unknown")
        papers[name] = entry  # latest wins

    print(f"Quality Analytics — {len(papers)} paper(s) scored\n")

    # Dimension header
    dims = ["evidence", "writing", "structure", "research", "provenance"]
    header = f"{'Paper':<30} {'Overall':>7} {'Grade':>5}"
    for d in dims:
        header += f" {d[:8]:>8}"
    print(header)
    print("-" * len(header))

    dim_totals = {d: [] for d in dims}
    for name, entry in sorted(papers.items()):
        overall = entry.get("overall", 0)
        grade = entry.get("grade", "?")
        row = f"{name:<30} {overall:>7} {grade:>5}"
        for d in dims:
            val = entry.get("dimensions", {}).get(d, {}).get("score", entry.get(d, 0))
            dim_totals[d].append(val)
            row += f" {val:>8}"
        print(row)

    # Averages
    if len(papers) >= 2:
        print(f"\n{'Averages':<30} ", end="")
        all_avgs = {}
        for d in dims:
            vals = dim_totals[d]
            avg = sum(vals) / len(vals) if vals else 0
            all_avgs[d] = avg
        overall_avg = sum(all_avgs[d] * w for d, w in [("evidence", 0.30), ("writing", 0.20), ("structure", 0.15), ("research", 0.20), ("provenance", 0.15)])
        print(f"{overall_avg:>7.0f}      ", end="")
        weakest = min(all_avgs, key=all_avgs.get)
        for d in dims:
            marker = " <-weak" if d == weakest else ""
            print(f" {all_avgs[d]:>5.0f}{marker}", end="")
        print()

    # Load outcomes
    outcomes_path = ANALYTICS_DIR / "outcomes.jsonl"
    if outcomes_path.exists():
        outcomes = []
        for line in outcomes_path.read_text().splitlines():
            if line.strip():
                try:
                    outcomes.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        if outcomes:
            print(f"\nOutcomes: {len(outcomes)} recorded")
            for status in ["accepted", "rejected", "revision", "withdrawn"]:
                count = sum(1 for o in outcomes if o.get("outcome") == status)
                if count:
                    print(f"  {status}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Paper quality scoring engine")
    sub = parser.add_subparsers(dest="command")

    p_score = sub.add_parser("score", help="Score a paper project")
    p_score.add_argument("--format", choices=["json", "text"], default="text")
    p_score.add_argument("--dimension", default="all",
                         choices=["all", "evidence", "writing", "structure", "research", "provenance"])
    p_score.add_argument("--project", default=".", help="Path to paper project")
    p_score.set_defaults(func=_cmd_score)

    p_save = sub.add_parser("save", help="Compute scorecard and save to analytics")
    p_save.add_argument("--project", default=".", help="Path to paper project")
    p_save.add_argument("--name", default=None, help="Paper name (defaults to directory basename)")
    p_save.add_argument("--checkpoint", default="manual", help="Checkpoint label")
    p_save.set_defaults(func=_cmd_save)

    p_history = sub.add_parser("history", help="Show scoring history")
    p_history.add_argument("--paper", default=None, help="Filter by paper name")
    p_history.set_defaults(func=_cmd_history)

    p_record = sub.add_parser("record-outcome", help="Record submission outcome")
    p_record.add_argument("outcome", help="Outcome (accepted, rejected, etc.)")
    p_record.add_argument("--project", default=".", help="Path to paper project")
    p_record.add_argument("--name", default=None, help="Paper name (defaults to directory basename)")
    p_record.add_argument("--venue", "-v", default="")
    p_record.add_argument("--notes", "-n", default="")
    p_record.set_defaults(func=_cmd_record_outcome)

    p_heatmap = sub.add_parser("heatmap", help="Generate per-claim evidence density heatmap")
    p_heatmap.add_argument("--project", default=".", help="Path to paper project")
    p_heatmap.set_defaults(func=_cmd_heatmap)

    p_insights = sub.add_parser("insights", help="Show quality insights")
    p_insights.set_defaults(func=_cmd_insights)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
