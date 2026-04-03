"""Verify .paper-state.json schema covers all stages in write-paper.md."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WRITE_PAPER = REPO_ROOT / "template" / "claude" / "commands" / "write-paper.md"

# Import the schema from test_schema.py
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "test_schema",
    Path(__file__).parent / "test_schema.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SCHEMA = _mod.SCHEMA

PIPELINE_DIR = REPO_ROOT / "template" / "claude" / "pipeline"


def _extract_state_keys_from_write_paper():
    """Extract all stages.X.done references from write-paper.md."""
    text = WRITE_PAPER.read_text(encoding="utf-8")
    # Match patterns like `stages.research.done` or `stages.deep_read.done`
    keys = set()
    for m in re.finditer(r"stages\.([a-z_]+)\.done", text):
        keys.add(m.group(1))
    return keys


def _schema_stage_names():
    """Return all stage names known to the schema (required + optional)."""
    names = set(SCHEMA["stages_required"].keys())
    # Optional stages that are dicts (have a .done field)
    for name, typ in SCHEMA["stages_optional"].items():
        if typ is dict:
            names.add(name)
    return names


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStateCompleteness:
    """Schema should cover all stages referenced in write-paper.md."""

    def test_all_write_paper_stages_in_schema(self):
        """Every stages.X.done in write-paper.md should be in the schema."""
        wp_keys = _extract_state_keys_from_write_paper()
        schema_keys = _schema_stage_names()
        missing = wp_keys - schema_keys
        assert not missing, (
            f"write-paper.md references stage keys not in schema: {sorted(missing)}"
        )

    def test_all_schema_stages_in_write_paper(self):
        """Every stage in the schema should be referenced in write-paper.md (no dead stages)."""
        wp_keys = _extract_state_keys_from_write_paper()
        schema_keys = _schema_stage_names()
        # Exclude special keys that are pipeline-internal or optional
        # auto_iterations and codex_risk_radar are managed by /auto and post-qa, not write-paper directly
        # quality_scores is managed by stage-5-qa, stage-6-finalization, and /auto, not write-paper
        internal_keys = {"auto_iterations", "codex_risk_radar", "quality_scores"}
        dead = (schema_keys - wp_keys) - internal_keys
        assert not dead, (
            f"Schema has stage keys not referenced in write-paper.md: {sorted(dead)}"
        )

    def test_stage_names_match_pipeline_files(self):
        """Stage names in the schema should correspond to existing pipeline files."""
        # Build expected mapping from write-paper.md table:
        # Each row has a pipeline file and a state key
        text = WRITE_PAPER.read_text(encoding="utf-8")
        file_to_key = {}
        for m in re.finditer(
            r"`pipeline/(stage-[a-z0-9._-]+\.md)`\s*\|\s*`stages\.([a-z_]+)\.done`",
            text,
        ):
            file_to_key[m.group(1)] = m.group(2)

        pipeline_files = {f.name for f in PIPELINE_DIR.glob("stage-*.md")}

        # Every pipeline stage file in the table should exist on disk
        for fname in file_to_key:
            assert fname in pipeline_files, (
                f"write-paper.md table references {fname} but file does not exist"
            )

    def test_example_validates(self):
        """The built-in example from test_schema should pass validation."""
        example = _mod.generate_example()
        errors = _mod.validate(example)
        assert not errors, f"Built-in example failed: {errors}"
