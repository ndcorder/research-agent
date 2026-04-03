"""Validate pipeline stage files: headings, prerequisites, model references, and orchestrator coverage."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PIPELINE_DIR = REPO_ROOT / "template" / "claude" / "pipeline"
WRITE_PAPER = REPO_ROOT / "template" / "claude" / "commands" / "write-paper.md"
AUTO_CMD = REPO_ROOT / "template" / "claude" / "commands" / "auto.md"


def _pipeline_files():
    """Return all .md files in the pipeline directory."""
    return sorted(PIPELINE_DIR.glob("*.md"))


def _stage_files():
    """Return pipeline files excluding shared-protocols.md and auto-phase files."""
    return [f for f in _pipeline_files()
            if f.name != "shared-protocols.md" and not f.name.startswith("auto-phase-")]


def _auto_phase_files():
    """Return auto-phase pipeline files."""
    return [f for f in _pipeline_files() if f.name.startswith("auto-phase-")]


# ---------------------------------------------------------------------------
# Heading checks
# ---------------------------------------------------------------------------


class TestStageHeadings:
    """Every stage file should start with a proper heading."""

    def test_stage_files_start_with_heading(self):
        for f in _stage_files():
            text = f.read_text(encoding="utf-8")
            first_line = text.strip().split("\n")[0]
            assert first_line.startswith("# "), (
                f"{f.name} does not start with a '# ' heading: {first_line!r}"
            )

    def test_auto_phase_files_start_with_heading(self):
        for f in _auto_phase_files():
            text = f.read_text(encoding="utf-8")
            first_line = text.strip().split("\n")[0]
            assert first_line.startswith("# "), (
                f"{f.name} does not start with a '# ' heading: {first_line!r}"
            )

    def test_shared_protocols_starts_with_heading(self):
        f = PIPELINE_DIR / "shared-protocols.md"
        text = f.read_text(encoding="utf-8")
        first_line = text.strip().split("\n")[0]
        assert first_line.startswith("# "), (
            f"shared-protocols.md does not start with a heading: {first_line!r}"
        )


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------


class TestPrerequisites:
    """Every stage/phase file (except shared-protocols.md) should reference shared-protocols.md."""

    def test_stage_files_reference_shared_protocols(self):
        for f in _stage_files():
            text = f.read_text(encoding="utf-8")
            # Check first 10 lines for a prerequisites reference
            head = "\n".join(text.split("\n")[:10]).lower()
            assert "shared-protocols" in head, (
                f"{f.name} does not reference shared-protocols.md in first 10 lines"
            )

    def test_auto_phase_files_reference_shared_protocols(self):
        for f in _auto_phase_files():
            text = f.read_text(encoding="utf-8")
            head = "\n".join(text.split("\n")[:10]).lower()
            assert "shared-protocols" in head, (
                f"{f.name} does not reference shared-protocols.md in first 10 lines"
            )


# ---------------------------------------------------------------------------
# Model references
# ---------------------------------------------------------------------------


class TestModelReferences:
    """Model references should use [1m] variants."""

    def test_no_bare_model_refs_in_pipeline(self):
        bare_pattern = re.compile(r"claude-(?:opus|sonnet)-4-6(?!\[1m\])")
        for f in _pipeline_files():
            text = f.read_text(encoding="utf-8")
            matches = bare_pattern.findall(text)
            assert not matches, (
                f"{f.name} has bare model reference(s) without [1m]: {matches}"
            )

    def test_no_bare_model_refs_in_write_paper(self):
        bare_pattern = re.compile(r"claude-(?:opus|sonnet)-4-6(?!\[1m\])")
        text = WRITE_PAPER.read_text(encoding="utf-8")
        matches = bare_pattern.findall(text)
        assert not matches, (
            f"write-paper.md has bare model reference(s) without [1m]: {matches}"
        )


# ---------------------------------------------------------------------------
# Orchestrator references every stage file
# ---------------------------------------------------------------------------


class TestOrchestratorCoverage:
    """write-paper.md should reference every stage file; auto.md should reference every auto-phase file."""

    def test_write_paper_references_all_stages(self):
        wp_text = WRITE_PAPER.read_text(encoding="utf-8")
        for f in _stage_files():
            # Check for the filename (with or without pipeline/ prefix)
            assert f.name in wp_text, (
                f"write-paper.md does not reference pipeline file: {f.name}"
            )

    def test_auto_references_all_phases(self):
        auto_text = AUTO_CMD.read_text(encoding="utf-8")
        for f in _auto_phase_files():
            assert f.name in auto_text, (
                f"auto.md does not reference auto phase file: {f.name}"
            )

    def test_write_paper_references_shared_protocols(self):
        wp_text = WRITE_PAPER.read_text(encoding="utf-8")
        assert "shared-protocols.md" in wp_text, (
            "write-paper.md does not reference shared-protocols.md"
        )


# ---------------------------------------------------------------------------
# No dangling file references
# ---------------------------------------------------------------------------


class TestNoDanglingReferences:
    """Pipeline files should not reference non-existent pipeline files."""

    def test_no_dangling_pipeline_refs(self):
        existing = {f.name for f in _pipeline_files()}
        ref_pattern = re.compile(r"(?:pipeline/|`)([a-z0-9._-]+\.md)")

        for f in _pipeline_files():
            text = f.read_text(encoding="utf-8")
            for m in ref_pattern.finditer(text):
                ref_name = m.group(1)
                # Only check references that look like pipeline files
                if ref_name.startswith("stage-") or ref_name.startswith("auto-") or ref_name == "shared-protocols.md":
                    assert ref_name in existing, (
                        f"{f.name} references non-existent pipeline file: {ref_name}"
                    )
