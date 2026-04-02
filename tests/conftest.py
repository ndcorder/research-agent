"""Shared pytest fixtures for the research-agent test suite."""

import sys
from pathlib import Path

import pytest

# Add template/scripts/ to sys.path so helper modules are importable.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "template" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal paper-project directory tree and return its root."""
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "prepared").mkdir()
    (tmp_path / "reviews").mkdir()
    return tmp_path
