"""Validate command files: existence, model specs, and cross-references with CLAUDE.md."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
COMMANDS_DIR = REPO_ROOT / "template" / "claude" / "commands"
CLAUDE_MD = REPO_ROOT / "template" / "claude" / "CLAUDE.md"
PIPELINE_DIR = REPO_ROOT / "template" / "claude" / "pipeline"

# Commands that are purely instruction-dispatchers (read a pipeline file and
# execute it) and may not themselves contain a model reference.
ORCHESTRATOR_COMMANDS = {"write-paper", "auto", "init", "preview-pipeline"}

# Commands that are lightweight / don't spawn agents
NO_AGENT_COMMANDS = {
    "status", "compile", "clean", "health", "provenance", "outline",
    "add-citation", "export-sources", "import-sources", "ask",
    "knowledge", "codex-telemetry", "archive",
}

# Commands that exist as files but are intentionally unlisted in CLAUDE.md
# (internal/utility commands not exposed in the user-facing command list)
UNLISTED_COMMANDS = {"prisma-flowchart", "reviewer-kb"}


def _command_files():
    """Return all .md files in the commands directory."""
    return sorted(COMMANDS_DIR.glob("*.md"))


def _commands_listed_in_claude_md():
    """Extract command names listed in template/claude/CLAUDE.md."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    # Pattern: `/<command-name>` or `/command-name` in list items or text
    names = set()
    for m in re.finditer(r"`/([a-z][-a-z0-9]*)`", text):
        names.add(m.group(1))
    return names


# ---------------------------------------------------------------------------
# Valid markdown
# ---------------------------------------------------------------------------


class TestCommandMarkdown:
    """Every command file should be non-empty valid markdown."""

    def test_command_files_are_nonempty(self):
        for f in _command_files():
            text = f.read_text(encoding="utf-8")
            assert text.strip(), f"{f.name} is empty"

    def test_command_files_start_with_heading_or_frontmatter(self):
        for f in _command_files():
            text = f.read_text(encoding="utf-8")
            first_line = text.strip().split("\n")[0]
            # Commands may start with a heading or YAML frontmatter
            assert first_line.startswith("#") or first_line == "---", (
                f"{f.name} does not start with a heading or frontmatter: {first_line!r}"
            )


# ---------------------------------------------------------------------------
# Agent commands specify a model
# ---------------------------------------------------------------------------


class TestAgentModelSpec:
    """Commands that spawn agents should specify a model."""

    def _spawns_agents(self, text):
        """Heuristic: file mentions spawning agents or model-tier keywords.

        Excludes "agent" appearing only in JSON provenance log entries.
        """
        patterns = [
            r"[Ss]pawn.*agent",
            r"\*\*Agent\s+\d",
            r"[Ss]ubagent",
        ]
        # Also check for agent model spec patterns like `model: "claude-..."`
        # but not prose uses of the word "model" (e.g., "PRISMA model:")
        if re.search(r'model:\s*["`\'"]?claude-', text):
            return True
        return any(re.search(p, text) for p in patterns)

    def _delegates_to_pipeline(self, text):
        """Check if command delegates to a pipeline stage file for its logic."""
        return bool(re.search(r"Read `pipeline/stage-.*\.md`", text))

    def test_agent_commands_have_model_ref(self):
        model_pattern = re.compile(r"claude-(?:opus|sonnet)-4-6\[1m\]")
        for f in _command_files():
            name = f.stem
            if name in ORCHESTRATOR_COMMANDS or name in NO_AGENT_COMMANDS:
                continue
            text = f.read_text(encoding="utf-8")
            if self._spawns_agents(text):
                # Commands that delegate to a pipeline stage file inherit the
                # model spec from that stage file, so they don't need their own.
                if self._delegates_to_pipeline(text):
                    continue
                assert model_pattern.search(text), (
                    f"{f.name} spawns agents but has no model reference with [1m]"
                )


# ---------------------------------------------------------------------------
# Cross-reference: CLAUDE.md <-> command files
# ---------------------------------------------------------------------------


class TestCrossReferences:
    """Commands referenced in CLAUDE.md should exist as files, and vice versa."""

    def test_claude_md_commands_have_files(self):
        listed = _commands_listed_in_claude_md()
        for cmd_name in sorted(listed):
            cmd_file = COMMANDS_DIR / f"{cmd_name}.md"
            assert cmd_file.exists(), (
                f"CLAUDE.md references /{cmd_name} but {cmd_file.name} does not exist"
            )

    def test_command_files_are_listed_in_claude_md(self):
        listed = _commands_listed_in_claude_md()
        for f in _command_files():
            cmd_name = f.stem
            if cmd_name in UNLISTED_COMMANDS:
                continue
            assert cmd_name in listed, (
                f"{f.name} exists but /{cmd_name} is not listed in CLAUDE.md"
            )


# ---------------------------------------------------------------------------
# No bare model references
# ---------------------------------------------------------------------------


class TestNoBareModeRefs:
    """Command files should not use bare model refs without [1m]."""

    def test_no_bare_model_refs(self):
        bare_pattern = re.compile(r"claude-(?:opus|sonnet)-4-6(?!\[1m\])")
        for f in _command_files():
            text = f.read_text(encoding="utf-8")
            matches = bare_pattern.findall(text)
            assert not matches, (
                f"{f.name} has bare model reference(s) without [1m]: {matches}"
            )
