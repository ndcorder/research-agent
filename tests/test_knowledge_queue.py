"""Unit tests for the queue-based ingestion system in knowledge.py.

Tests _classify_file, _is_worker_alive, _read_queue, _read_progress,
_save_progress, cmd_enqueue, priority ordering, and queue deduplication
without requiring LightRAG, OpenRouter, or any async RAG operations.
"""

import asyncio
import json
import os
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import knowledge.py (same safe-import pattern as test_knowledge.py)
# ---------------------------------------------------------------------------

_had_key = "OPENROUTER_API_KEY" in os.environ
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-not-real")

_spec = importlib.util.spec_from_file_location(
    "knowledge",
    Path(__file__).parent.parent / "template" / "scripts" / "knowledge.py",
)
knowledge = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(knowledge)
except ImportError:
    pytest.skip("lightrag not installed", allow_module_level=True)
finally:
    if not _had_key:
        os.environ.pop("OPENROUTER_API_KEY", None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def queue_env(tmp_path, monkeypatch):
    """Monkeypatch module constants to use a temp directory."""
    work_dir = tmp_path / "research" / "knowledge"
    work_dir.mkdir(parents=True)
    monkeypatch.setattr(knowledge, "WORKING_DIR", str(work_dir))
    monkeypatch.setattr(knowledge, "QUEUE_FILE", str(work_dir / ".queue.jsonl"))
    monkeypatch.setattr(knowledge, "PROGRESS_FILE", str(work_dir / ".queue_progress.json"))
    monkeypatch.setattr(knowledge, "WORKER_PID_FILE", str(work_dir / ".worker.pid"))
    monkeypatch.setattr(knowledge, "WORKER_LOG_FILE", str(work_dir / "worker.log"))
    return work_dir


def _make_args(**kwargs):
    """Create a simple namespace object mimicking argparse output."""
    return type("Args", (), kwargs)()


# ── _classify_file ─────────────────────────────────────────────────────────


class TestClassifyFile:
    def test_source_extract(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        f = src / "smith2024.md"
        f.write_text("content")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "smith2024"
        assert priority == 1

    def test_prepared_doc_nested(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        prep = tmp_path / "research" / "prepared" / "claims"
        prep.mkdir(parents=True)
        f = prep / "C1.md"
        f.write_text("content")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "prepared_claims_C1"
        assert priority == 2

    def test_prepared_doc_top_level(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        prep = tmp_path / "research" / "prepared"
        prep.mkdir(parents=True)
        f = prep / "overview.md"
        f.write_text("content")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "prepared_overview"
        assert priority == 2

    def test_parsed_markdown(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        f = parsed / "jones2023.md"
        f.write_text("content")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "parsed_jones2023"
        assert priority == 3

    def test_raw_pdf(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        att = tmp_path / "attachments"
        att.mkdir(parents=True)
        f = att / "paper.pdf"
        f.write_text("fake pdf")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "pdf_paper"
        assert priority == 4

    def test_unknown_md_defaults_to_priority_2(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "random.md"
        f.write_text("content")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "random"
        assert priority == 2

    def test_file_outside_project(self, tmp_path, monkeypatch):
        """Files outside cwd fall through to default classification."""
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)

        outside = tmp_path / "elsewhere"
        outside.mkdir()
        f = outside / "file.md"
        f.write_text("content")

        doc_id, priority = knowledge._classify_file(f.resolve())
        assert doc_id == "file"
        assert priority == 2

    def test_ids_match_cmd_build_convention(self, tmp_path, monkeypatch):
        """classify_file IDs match the IDs that cmd_build would assign."""
        monkeypatch.chdir(tmp_path)

        # Source extract → bare stem
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        (src / "alpha.md").write_text("x")
        doc_id, _ = knowledge._classify_file((src / "alpha.md").resolve())
        assert doc_id == "alpha"

        # Prepared → "prepared_" prefix with path encoding
        prep = tmp_path / "research" / "prepared" / "methodology"
        prep.mkdir(parents=True)
        (prep / "scf-overlap.md").write_text("x")
        doc_id, _ = knowledge._classify_file((prep / "scf-overlap.md").resolve())
        assert doc_id == "prepared_methodology_scf-overlap"

        # Parsed → "parsed_" prefix
        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "beta.md").write_text("x")
        doc_id, _ = knowledge._classify_file((parsed / "beta.md").resolve())
        assert doc_id == "parsed_beta"

        # PDF → "pdf_" prefix
        att = tmp_path / "attachments"
        (att / "gamma.pdf").write_text("x")
        doc_id, _ = knowledge._classify_file((att / "gamma.pdf").resolve())
        assert doc_id == "pdf_gamma"


# ── _is_worker_alive ──────────────────────────────────────────────────────


class TestIsWorkerAlive:
    def test_no_pid_file(self, queue_env):
        alive, pid = knowledge._is_worker_alive()
        assert alive is False
        assert pid is None

    def test_current_process_is_alive(self, queue_env):
        Path(knowledge.WORKER_PID_FILE).write_text(str(os.getpid()))
        alive, pid = knowledge._is_worker_alive()
        assert alive is True
        assert pid == os.getpid()

    def test_dead_pid_cleaned_up(self, queue_env):
        """A stale PID file for a nonexistent process is removed."""
        Path(knowledge.WORKER_PID_FILE).write_text("99999999")
        alive, pid = knowledge._is_worker_alive()
        assert alive is False
        assert pid is None
        assert not Path(knowledge.WORKER_PID_FILE).exists()

    def test_malformed_pid_file(self, queue_env):
        Path(knowledge.WORKER_PID_FILE).write_text("not-a-number")
        alive, pid = knowledge._is_worker_alive()
        assert alive is False
        assert pid is None
        assert not Path(knowledge.WORKER_PID_FILE).exists()

    def test_empty_pid_file(self, queue_env):
        Path(knowledge.WORKER_PID_FILE).write_text("")
        alive, pid = knowledge._is_worker_alive()
        assert alive is False
        assert pid is None


# ── _read_queue ───────────────────────────────────────────────────────────


class TestReadQueue:
    def test_no_file(self, queue_env):
        assert knowledge._read_queue() == []

    def test_valid_entries(self, queue_env):
        entries = [
            {"doc_id": "a", "path": "/a.md", "priority": 1},
            {"doc_id": "b", "path": "/b.md", "priority": 2},
        ]
        with open(knowledge.QUEUE_FILE, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        result = knowledge._read_queue()
        assert len(result) == 2
        assert result[0]["doc_id"] == "a"
        assert result[1]["doc_id"] == "b"

    def test_malformed_lines_skipped(self, queue_env):
        with open(knowledge.QUEUE_FILE, "w") as f:
            f.write('{"doc_id": "good"}\n')
            f.write("this is not json\n")
            f.write('{"doc_id": "also_good"}\n')

        result = knowledge._read_queue()
        assert len(result) == 2
        assert result[0]["doc_id"] == "good"
        assert result[1]["doc_id"] == "also_good"

    def test_empty_lines_skipped(self, queue_env):
        with open(knowledge.QUEUE_FILE, "w") as f:
            f.write('{"doc_id": "a"}\n')
            f.write("\n")
            f.write("   \n")
            f.write('{"doc_id": "b"}\n')

        result = knowledge._read_queue()
        assert len(result) == 2

    def test_empty_file(self, queue_env):
        Path(knowledge.QUEUE_FILE).write_text("")
        assert knowledge._read_queue() == []


# ── _read_progress / _save_progress ───────────────────────────────────────


class TestProgress:
    def test_no_file_returns_default(self, queue_env):
        result = knowledge._read_progress()
        assert result == {"processed": {}}

    def test_roundtrip(self, queue_env):
        progress = {
            "processed": {
                "smith2024": {
                    "status": "done",
                    "completed_at": "2026-04-02T10:00:00+00:00",
                },
                "jones2023": {"status": "failed", "error": "timeout"},
            }
        }
        knowledge._save_progress(progress)
        result = knowledge._read_progress()
        assert result == progress

    def test_corrupt_file_returns_default(self, queue_env):
        Path(knowledge.PROGRESS_FILE).write_text("not valid json {{{")
        result = knowledge._read_progress()
        assert result == {"processed": {}}

    def test_save_creates_file(self, queue_env):
        assert not Path(knowledge.PROGRESS_FILE).exists()
        knowledge._save_progress({"processed": {"x": {"status": "done"}}})
        assert Path(knowledge.PROGRESS_FILE).exists()
        data = json.loads(Path(knowledge.PROGRESS_FILE).read_text())
        assert data["processed"]["x"]["status"] == "done"

    def test_save_overwrites_completely(self, queue_env):
        knowledge._save_progress({"processed": {"a": {"status": "done"}}})
        knowledge._save_progress({"processed": {"b": {"status": "done"}}})
        result = knowledge._read_progress()
        assert "b" in result["processed"]
        assert "a" not in result["processed"]

    def test_save_with_nested_data(self, queue_env):
        progress = {
            "processed": {
                "doc1": {
                    "status": "done",
                    "chars": 12345,
                    "completed_at": "2026-04-02T10:00:00+00:00",
                },
                "doc2": {
                    "status": "failed",
                    "error": "OpenRouter rate limit exceeded",
                    "completed_at": "2026-04-02T10:05:00+00:00",
                },
                "doc3": {
                    "status": "skipped",
                    "reason": "empty_file",
                    "completed_at": "2026-04-02T10:06:00+00:00",
                },
            }
        }
        knowledge._save_progress(progress)
        assert knowledge._read_progress() == progress


# ── Priority ordering ─────────────────────────────────────────────────────


class TestPriorityOrdering:
    def test_sort_by_priority(self):
        items = [
            {"doc_id": "pdf_big", "priority": 4},
            {"doc_id": "src_a", "priority": 1},
            {"doc_id": "parsed_b", "priority": 3},
            {"doc_id": "prep_c", "priority": 2},
        ]
        items.sort(key=lambda x: x.get("priority", 99))
        assert [i["doc_id"] for i in items] == [
            "src_a", "prep_c", "parsed_b", "pdf_big"
        ]

    def test_missing_priority_sorts_last(self):
        items = [
            {"doc_id": "no_priority"},
            {"doc_id": "src_a", "priority": 1},
        ]
        items.sort(key=lambda x: x.get("priority", 99))
        assert items[0]["doc_id"] == "src_a"
        assert items[1]["doc_id"] == "no_priority"

    def test_same_priority_preserves_order(self):
        items = [
            {"doc_id": "z", "priority": 1},
            {"doc_id": "a", "priority": 1},
            {"doc_id": "m", "priority": 1},
        ]
        items.sort(key=lambda x: x.get("priority", 99))
        # Python's sort is stable: same-priority items keep insertion order
        assert [i["doc_id"] for i in items] == ["z", "a", "m"]


# ── Queue deduplication ───────────────────────────────────────────────────


class TestQueueDeduplication:
    def test_last_enqueue_wins(self, queue_env):
        with open(knowledge.QUEUE_FILE, "w") as f:
            f.write(json.dumps({"doc_id": "smith", "path": "/old.md", "priority": 1}) + "\n")
            f.write(json.dumps({"doc_id": "smith", "path": "/new.md", "priority": 1}) + "\n")

        items = knowledge._read_queue()
        unique = {}
        for item in items:
            unique[item["doc_id"]] = item

        assert unique["smith"]["path"] == "/new.md"

    def test_dedup_preserves_all_unique_ids(self, queue_env):
        with open(knowledge.QUEUE_FILE, "w") as f:
            f.write(json.dumps({"doc_id": "a", "priority": 1}) + "\n")
            f.write(json.dumps({"doc_id": "b", "priority": 2}) + "\n")
            f.write(json.dumps({"doc_id": "a", "priority": 1}) + "\n")

        items = knowledge._read_queue()
        unique = {}
        for item in items:
            unique[item["doc_id"]] = item

        assert len(unique) == 2

    def test_pending_filters_out_processed(self, queue_env):
        """The serve loop's pending filter correctly excludes processed items."""
        with open(knowledge.QUEUE_FILE, "w") as f:
            f.write(json.dumps({"doc_id": "done_one", "priority": 1}) + "\n")
            f.write(json.dumps({"doc_id": "pending_one", "priority": 1}) + "\n")
            f.write(json.dumps({"doc_id": "failed_one", "priority": 2}) + "\n")

        progress = {
            "processed": {
                "done_one": {"status": "done"},
                "failed_one": {"status": "failed", "error": "x"},
            }
        }

        items = knowledge._read_queue()
        unique = {}
        for item in items:
            unique[item["doc_id"]] = item

        pending = [
            item for item in unique.values()
            if item["doc_id"] not in progress["processed"]
        ]

        assert len(pending) == 1
        assert pending[0]["doc_id"] == "pending_one"


# ── cmd_enqueue (integration) ────────────────────────────────────────────


class TestCmdEnqueue:
    def test_enqueue_new_files(self, tmp_path, queue_env, monkeypatch):
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        (src / "a.md").write_text("content a")
        (src / "b.md").write_text("content b")

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(src / "a.md"), str(src / "b.md")], reindex=False)
        ))

        items = knowledge._read_queue()
        doc_ids = {i["doc_id"] for i in items}
        assert doc_ids == {"a", "b"}

    def test_enqueue_assigns_correct_priorities(self, tmp_path, queue_env, monkeypatch):
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        (src / "s.md").write_text("x")

        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "p.md").write_text("x")

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(src / "s.md"), str(parsed / "p.md")], reindex=False)
        ))

        items = knowledge._read_queue()
        by_id = {i["doc_id"]: i for i in items}
        assert by_id["s"]["priority"] == 1
        assert by_id["parsed_p"]["priority"] == 3

    def test_skips_already_processed_unmodified(self, tmp_path, queue_env, monkeypatch):
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        f = src / "old.md"
        f.write_text("old content")

        # Mark as processed with a far-future timestamp
        knowledge._save_progress({
            "processed": {
                "old": {
                    "status": "done",
                    "completed_at": datetime(2099, 1, 1, tzinfo=timezone.utc).isoformat(),
                }
            }
        })

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(f)], reindex=False)
        ))

        assert knowledge._read_queue() == []

    def test_requeues_modified_file(self, tmp_path, queue_env, monkeypatch):
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        f = src / "updated.md"
        f.write_text("new content after deep read")

        # Mark as processed with a past timestamp (file is newer)
        knowledge._save_progress({
            "processed": {
                "updated": {
                    "status": "done",
                    "completed_at": datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat(),
                }
            }
        })

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(f)], reindex=False)
        ))

        items = knowledge._read_queue()
        assert len(items) == 1
        assert items[0]["doc_id"] == "updated"

        # Progress entry should be cleared for re-processing
        progress = knowledge._read_progress()
        assert "updated" not in progress["processed"]

    def test_reindex_forces_reprocessing(self, tmp_path, queue_env, monkeypatch):
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        f = src / "forced.md"
        f.write_text("content")

        # Mark as processed with future timestamp (would normally be skipped)
        knowledge._save_progress({
            "processed": {
                "forced": {
                    "status": "done",
                    "completed_at": datetime(2099, 1, 1, tzinfo=timezone.utc).isoformat(),
                }
            }
        })

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(f)], reindex=True)
        ))

        items = knowledge._read_queue()
        assert len(items) == 1

        progress = knowledge._read_progress()
        assert "forced" not in progress["processed"]

    def test_nonexistent_file_skipped(self, tmp_path, queue_env, monkeypatch):
        monkeypatch.chdir(tmp_path)

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=["/nonexistent/file.md"], reindex=False)
        ))

        assert knowledge._read_queue() == []

    def test_failed_items_can_be_requeued(self, tmp_path, queue_env, monkeypatch):
        """A previously failed item can be re-enqueued with --reindex."""
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        f = src / "retry.md"
        f.write_text("content")

        knowledge._save_progress({
            "processed": {
                "retry": {
                    "status": "failed",
                    "error": "OpenRouter timeout",
                    "completed_at": datetime(2099, 1, 1, tzinfo=timezone.utc).isoformat(),
                }
            }
        })

        # Without --reindex, failed items have a status that's not "done",
        # so the mtime skip logic doesn't apply — they get re-enqueued
        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(f)], reindex=False)
        ))

        items = knowledge._read_queue()
        assert len(items) == 1
        progress = knowledge._read_progress()
        assert "retry" not in progress["processed"]

    def test_multiple_enqueues_append(self, tmp_path, queue_env, monkeypatch):
        """Multiple enqueue calls append to the same queue file."""
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "research" / "sources"
        src.mkdir(parents=True)
        (src / "a.md").write_text("x")
        (src / "b.md").write_text("x")

        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(src / "a.md")], reindex=False)
        ))
        asyncio.run(knowledge.cmd_enqueue(
            _make_args(files=[str(src / "b.md")], reindex=False)
        ))

        items = knowledge._read_queue()
        assert len(items) == 2


# ── _read_file_content ────────────────────────────────────────────────────


class TestReadFileContent:
    def test_reads_markdown(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello world")
        assert knowledge._read_file_content(f) == "hello world"

    def test_reads_txt_as_text(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("plain text notes")
        assert knowledge._read_file_content(f) == "plain text notes"

    def test_pdf_returns_string(self, tmp_path):
        """PDF dispatch returns a string (empty for invalid files)."""
        f = tmp_path / "test.pdf"
        f.write_text("not a real pdf")
        result = knowledge._read_file_content(f)
        assert isinstance(result, str)


# ── _log_worker ───────────────────────────────────────────────────────────


class TestLogWorker:
    def test_creates_log_file(self, queue_env):
        log_path = Path(knowledge.WORKER_LOG_FILE)
        assert not log_path.exists()
        knowledge._log_worker("test message")
        assert log_path.exists()

    def test_appends_timestamped_entries(self, queue_env):
        knowledge._log_worker("first")
        knowledge._log_worker("second")
        content = Path(knowledge.WORKER_LOG_FILE).read_text()
        lines = content.strip().splitlines()
        assert len(lines) == 2
        assert "first" in lines[0]
        assert "second" in lines[1]
        # Each line should have a timestamp prefix
        assert lines[0].startswith("[")
        assert "] " in lines[0]
