#!/usr/bin/env python3
"""Validate .paper-state.json schema against expected structure."""

import json
import sys
from pathlib import Path
from typing import Any

# ---------- Schema definition ----------

SCHEMA = {
    "required": {
        "topic": str,
        "venue": str,
        "started_at": str,
        "current_stage": str,
        "stages": dict,
    },
    "optional": {},
    "stages_required": {
        "research": {
            "required": {"done": bool},
            "optional": {
                "completed_at": str,
                "agents_completed": list,
                "agents_pending": list,
                "notes": str,
            },
        },
        "snowballing": {
            "required": {"done": bool},
            "optional": {
                "seeds": int,
                "backward_found": int,
                "forward_found": int,
                "added_to_bib": int,
            },
        },
        "cocitation": {
            "required": {"done": bool},
            "optional": {
                "references_analyzed": int,
                "high_confidence_found": int,
                "medium_confidence_found": int,
                "auto_added": int,
            },
        },
        "outline": {
            "required": {"done": bool},
            "optional": {"completed_at": str, "evidence_gate": dict},
        },
        "codex_cross_check": {
            "required": {"done": bool},
            "optional": {"completed_at": str, "file": str},
        },
        "source_acquisition": {
            "required": {"done": bool},
            "optional": {
                "full_text": int,
                "abstract_only": int,
                "metadata_only": int,
            },
        },
        "codex_thesis": {
            "required": {"done": bool},
            "optional": {"completed_at": str, "file": str},
        },
        "novelty_check": {
            "required": {"done": bool},
            "optional": {"completed_at": str, "file": str, "status": str},
        },
        "assumptions": {
            "required": {"done": bool},
            "optional": {
                "completed_at": str,
                "file": str,
                "total": int,
                "critical": int,
                "risky": int,
            },
        },
        "writing": {
            "required": {"done": bool},
            "optional": {"current_substep": (str, type(None)), "sections": dict},
        },
        "figures": {
            "required": {"done": bool},
            "optional": {},
        },
        "qa": {
            "required": {"done": bool},
            "optional": {},
        },
        "finalization": {
            "required": {"done": bool},
            "optional": {},
        },
    },
    "stages_optional": {
        "qa_iteration": int,
        "codex_risk_radar": dict,
        "auto_iterations": dict,
        "targeted_research": dict,
        "deep_read": dict,
        "literature_synthesis": dict,
        "coherence": dict,
        "post_qa": dict,
        "reference_integrity": dict,
        "quality_scores": dict,
    },
    "auto_iterations_schema": {
        "required": {"completed": int, "requested": int, "history": list},
        "optional": {},
    },
    "writing_section_schema": {
        "required": {"done": bool},
        "optional": {"words": int, "current_substep": (str, type(None))},
    },
}

EVIDENCE_GATE_SCHEMA = {
    "required": {
        "total_claims": int,
        "strong": int,
        "moderate": int,
        "weak": int,
        "critical": int,
        "gate_passed": bool,
    },
    "optional": {},
}


# ---------- Disagreement Registry Schema ----------

DISAGREEMENT_SCHEMA = {
    "required_top": {"version": int, "disagreements": list},
    "entry_required": {
        "id": str,
        "theme": str,
        "type": str,  # empirical | interpretive | methodological | scope
        "position_a": dict,
        "position_b": dict,
        "resolution_strategy": str,  # comparative_analysis | hedge | scope_limit | defer | remove_claim
        "status": str,  # identified | resolved | deferred
    },
    "entry_optional": {
        "resolution_notes": str,
        "addressed_in_sections": list,
    },
    "position_required": {
        "claim": str,
        "sources": list,
        "evidence_quality": str,  # strong | moderate | weak
    },
}


def validate_disagreements(data: dict) -> list[str]:
    """Validate research/disagreements.json."""
    errors = []
    for field, typ in DISAGREEMENT_SCHEMA["required_top"].items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], typ):
            errors.append(f"Field '{field}' should be {typ.__name__}")
    for i, entry in enumerate(data.get("disagreements", [])):
        prefix = f"disagreements[{i}]"
        for field, typ in DISAGREEMENT_SCHEMA["entry_required"].items():
            if field not in entry:
                errors.append(f"{prefix}: missing '{field}'")
            elif not isinstance(entry[field], typ):
                errors.append(f"{prefix}.{field}: expected {typ.__name__}")
        for side in ("position_a", "position_b"):
            pos = entry.get(side, {})
            for field, typ in DISAGREEMENT_SCHEMA["position_required"].items():
                if field not in pos:
                    errors.append(f"{prefix}.{side}: missing '{field}'")
    return errors


def test_disagreements_fixture():
    fixture = Path(__file__).parent / "fixtures" / "disagreements_sample.json"
    data = json.loads(fixture.read_text())
    errors = validate_disagreements(data)
    assert errors == [], f"Disagreement schema errors: {errors}"


# ---------- Validation ----------

def validate_evidence_gate(gate: dict) -> list[str]:
    """Validate evidence_gate dict structure. Returns list of error strings."""
    errors: list[str] = []
    for key, expected_type in EVIDENCE_GATE_SCHEMA["required"].items():
        if key not in gate:
            errors.append(f"evidence_gate missing required key '{key}'")
        elif not isinstance(gate[key], expected_type):
            errors.append(
                f"evidence_gate['{key}'] should be {expected_type.__name__}, "
                f"got {type(gate[key]).__name__}"
            )
    for key in gate:
        if key not in EVIDENCE_GATE_SCHEMA["required"] and key not in EVIDENCE_GATE_SCHEMA["optional"]:
            errors.append(f"evidence_gate has unexpected key '{key}'")
    return errors


def validate(data: Any, schema: dict = SCHEMA) -> list[str]:
    """Validate data against the schema. Returns list of error strings (empty = valid)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Root must be a JSON object"]

    # Check top-level required fields
    for field, expected_type in schema["required"].items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(
                f"Field '{field}' should be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    # Check stages
    stages = data.get("stages", {})
    if not isinstance(stages, dict):
        errors.append("'stages' must be a dict")
        return errors

    # Check required stage keys
    for stage_name, stage_schema in schema["stages_required"].items():
        if stage_name not in stages:
            errors.append(f"Missing required stage: stages.{stage_name}")
            continue

        stage_data = stages[stage_name]
        if not isinstance(stage_data, dict):
            errors.append(f"stages.{stage_name} must be a dict")
            continue

        for field, expected_type in stage_schema["required"].items():
            if field not in stage_data:
                errors.append(f"Missing required field: stages.{stage_name}.{field}")
            elif not isinstance(stage_data[field], expected_type):
                errors.append(
                    f"stages.{stage_name}.{field} should be "
                    f"{expected_type.__name__}, got {type(stage_data[field]).__name__}"
                )

        for field, expected_type in stage_schema["optional"].items():
            if field in stage_data:
                if isinstance(expected_type, tuple):
                    if not isinstance(stage_data[field], expected_type):
                        type_names = "/".join(
                            t.__name__ if t is not type(None) else "null"
                            for t in expected_type
                        )
                        errors.append(
                            f"stages.{stage_name}.{field} should be "
                            f"{type_names}, got {type(stage_data[field]).__name__}"
                        )
                elif not isinstance(stage_data[field], expected_type):
                    errors.append(
                        f"stages.{stage_name}.{field} should be "
                        f"{expected_type.__name__}, got {type(stage_data[field]).__name__}"
                    )

    # Check evidence_gate structure if present in outline
    outline_data = stages.get("outline", {})
    if isinstance(outline_data, dict) and "evidence_gate" in outline_data:
        gate = outline_data["evidence_gate"]
        if isinstance(gate, dict):
            errors.extend(validate_evidence_gate(gate))

    # Check auto_iterations shape if present
    auto_iter = stages.get("auto_iterations")
    if auto_iter is not None and isinstance(auto_iter, dict):
        ai_schema = schema["auto_iterations_schema"]
        for field, expected_type in ai_schema["required"].items():
            if field not in auto_iter:
                errors.append(f"Missing: stages.auto_iterations.{field}")
            elif not isinstance(auto_iter[field], expected_type):
                errors.append(
                    f"stages.auto_iterations.{field} should be "
                    f"{expected_type.__name__}, got {type(auto_iter[field]).__name__}"
                )

    # Check writing sections shape if present
    writing = stages.get("writing", {})
    sections = writing.get("sections", {}) if isinstance(writing, dict) else {}
    if isinstance(sections, dict):
        ws_schema = schema["writing_section_schema"]
        for sec_name, sec_data in sections.items():
            if not isinstance(sec_data, dict):
                errors.append(f"stages.writing.sections.{sec_name} must be a dict")
                continue
            for field, expected_type in ws_schema["required"].items():
                if field not in sec_data:
                    errors.append(
                        f"Missing: stages.writing.sections.{sec_name}.{field}"
                    )
                elif not isinstance(sec_data[field], expected_type):
                    errors.append(
                        f"stages.writing.sections.{sec_name}.{field} should be "
                        f"{expected_type.__name__}"
                    )

    return errors


# ---------- Example generator ----------

def generate_example() -> dict:
    """Generate a valid .paper-state.json example."""
    return {
        "topic": "Example Research Topic",
        "venue": "generic",
        "started_at": "2026-03-21T14:00:00Z",
        "current_stage": "writing",
        "stages": {
            "research": {
                "done": True,
                "completed_at": "2026-03-21T15:00:00Z",
                "agents_completed": ["survey", "methods", "empirical", "theory", "gaps"],
                "agents_pending": [],
                "notes": "45 refs found",
            },
            "snowballing": {
                "done": True,
                "seeds": 10,
                "backward_found": 23,
                "forward_found": 15,
                "added_to_bib": 8,
            },
            "cocitation": {
                "done": True,
                "references_analyzed": 30,
                "high_confidence_found": 5,
                "medium_confidence_found": 8,
                "auto_added": 3,
            },
            "outline": {
                "done": True,
                "completed_at": "2026-03-21T16:00:00Z",
                "evidence_gate": {
                    "total_claims": 15,
                    "strong": 8,
                    "moderate": 4,
                    "weak": 2,
                    "critical": 1,
                    "gate_passed": True,
                },
            },
            "codex_cross_check": {
                "done": True,
                "completed_at": "2026-03-21T15:30:00Z",
                "file": "research/codex_cross_check.md",
            },
            "source_acquisition": {
                "done": True,
                "full_text": 12,
                "abstract_only": 8,
                "metadata_only": 3,
            },
            "codex_thesis": {
                "done": True,
                "completed_at": "2026-03-21T16:30:00Z",
                "file": "research/codex_thesis_review.md",
            },
            "novelty_check": {
                "done": True,
                "completed_at": "2026-03-21T16:45:00Z",
                "file": "research/novelty_check.md",
                "status": "NOVEL",
            },
            "assumptions": {
                "done": True,
                "completed_at": "2026-03-21T17:00:00Z",
                "file": "research/assumptions.md",
                "total": 12,
                "critical": 1,
                "risky": 3,
            },
            "writing": {
                "done": False,
                "current_substep": "evidence_check",
                "sections": {
                    "introduction": {"done": True, "words": 1250, "current_substep": None},
                    "related_work": {"done": True, "words": 2100, "current_substep": None},
                    "methods": {"done": False, "words": 0, "current_substep": "expansion"},
                },
            },
            "literature_synthesis": {
                "done": True,
                "completed_at": "2026-03-21T15:45:00Z",
                "agents_completed": ["conflicts", "methods", "frameworks"],
                "agents_pending": [],
            },
            "coherence": {
                "done": True,
                "completed_at": "2026-03-21T18:00:00Z",
                "issues_found": 5,
                "critical_fixed": 2,
            },
            "figures": {"done": False},
            "qa_iteration": 0,
            "qa": {"done": False},
            "codex_risk_radar": {"done": False},
            "finalization": {"done": False},
            "auto_iterations": {
                "completed": 0,
                "requested": 0,
                "history": [],
            },
            "quality_scores": {
                "pre_qa": {"overall": 45, "timestamp": "2026-03-21T17:30:00Z"},
                "final": {"overall": 78, "timestamp": "2026-03-21T20:00:00Z"},
                "history": [],
            },
        },
    }


# ---------- Main ----------

def main():
    # Self-test: validate the built-in example
    example = generate_example()
    example_errors = validate(example)
    if example_errors:
        print("FAIL: Built-in example failed validation:")
        for e in example_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS: Built-in example validates correctly")

    # Self-test: evidence_gate validation
    good_gate = {
        "total_claims": 15, "strong": 8, "moderate": 4,
        "weak": 2, "critical": 1, "gate_passed": True,
    }
    gate_errors = validate_evidence_gate(good_gate)
    if gate_errors:
        print("FAIL: Valid evidence_gate rejected:")
        for e in gate_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS: evidence_gate schema validates correctly")

    bad_gate = {"total_claims": "not_int", "gate_passed": True}
    gate_errors = validate_evidence_gate(bad_gate)
    expected_bad = 5  # missing: strong, moderate, weak, critical; wrong type: total_claims
    if len(gate_errors) != expected_bad:
        print(f"FAIL: Bad evidence_gate should have {expected_bad} errors, got {len(gate_errors)}")
        for e in gate_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS: evidence_gate rejects invalid data correctly")

    # If a file argument is provided, validate that file
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"FAIL: {filepath} — invalid JSON: {exc}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"FAIL: {filepath} — file not found")
            sys.exit(1)

        errors = validate(data)
        if errors:
            print(f"FAIL: {filepath} — {len(errors)} error(s):")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"PASS: {filepath} validates correctly")

    # If --generate flag, print the example
    if "--generate" in sys.argv:
        print(json.dumps(example, indent=2))


if __name__ == "__main__":
    main()
