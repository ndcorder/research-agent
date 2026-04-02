"""Unit tests for document collection and ID construction logic in knowledge.py.

Since the async RAG operations require OpenRouter and LightRAG, we replicate
the pure file-scanning / ID-construction / deduplication logic from cmd_build
and test it in isolation.
"""

import os
import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import knowledge.py safely.
# get_api_key() calls sys.exit(1) if OPENROUTER_API_KEY is missing, but it
# is only invoked at RAG-creation time, not at import.  The import can still
# fail if lightrag is not installed.
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
# Helper: replicate the document-collection logic from cmd_build (lines ~205-280)
# without any async/RAG calls.
# ---------------------------------------------------------------------------

def collect_documents(root: Path):
    """Return (documents, ids) using the same rules as cmd_build.

    *root* is the paper-project directory containing research/ and attachments/.
    """
    sources_path = root / "research" / "sources"
    prepared_path = root / "research" / "prepared"
    parsed_path = root / "attachments" / "parsed"
    attachments_path = root / "attachments"

    documents: list[str] = []
    ids: list[str] = []

    # 1. Source extract markdown files (empty files ARE included)
    if sources_path.exists():
        for f in sorted(sources_path.glob("*.md")):
            documents.append(f.read_text(encoding="utf-8"))
            ids.append(f.stem)

    # 2. Prepared documents (empty/whitespace-only files are SKIPPED)
    if prepared_path.exists():
        for f in sorted(prepared_path.rglob("*.md")):
            content = f.read_text(encoding="utf-8")
            if content.strip():
                rel_path = f.relative_to(prepared_path)
                doc_id = f"prepared_{rel_path.with_suffix('').as_posix().replace('/', '_')}"
                documents.append(content)
                ids.append(doc_id)

    # 3. Parsed markdown (empty/whitespace-only files are SKIPPED)
    parsed_stems: set[str] = set()
    if parsed_path.exists():
        for f in sorted(parsed_path.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            if content.strip():
                documents.append(content)
                ids.append(f"parsed_{f.stem}")
                parsed_stems.add(f.stem)

    # 4. Raw PDFs — skipped if a parsed markdown with the same stem exists
    if attachments_path.exists():
        for pdf in sorted(attachments_path.glob("*.pdf")):
            if pdf.stem in parsed_stems:
                continue
            # We don't actually extract PDF text in the helper; just record the ID.
            doc_id = f"pdf_{pdf.stem}"
            documents.append(f"(pdf placeholder for {pdf.name})")
            ids.append(doc_id)

    return documents, ids


# ── Source extracts ─────────────────────────────────────────────────────────


class TestSourceExtracts:
    def test_stem_based_ids(self, tmp_path):
        (tmp_path / "research" / "sources").mkdir(parents=True)
        (tmp_path / "research" / "sources" / "smith2024.md").write_text("Source A")
        (tmp_path / "research" / "sources" / "jones2023.md").write_text("Source B")

        _, ids = collect_documents(tmp_path)
        assert "jones2023" in ids
        assert "smith2024" in ids

    def test_empty_source_still_collected(self, tmp_path):
        """Source extracts are collected even when empty (unlike prepared/parsed)."""
        (tmp_path / "research" / "sources").mkdir(parents=True)
        (tmp_path / "research" / "sources" / "empty.md").write_text("")

        docs, ids = collect_documents(tmp_path)
        assert "empty" in ids
        assert len(docs) == 1


# ── Prepared documents ──────────────────────────────────────────────────────


class TestPreparedDocuments:
    def test_prefix_and_path_encoding(self, tmp_path):
        prep = tmp_path / "research" / "prepared"
        (prep / "claims").mkdir(parents=True)
        (prep / "claims" / "C1.md").write_text("Claim 1 content")

        _, ids = collect_documents(tmp_path)
        assert "prepared_claims_C1" in ids

    def test_nested_path_encoding(self, tmp_path):
        prep = tmp_path / "research" / "prepared"
        (prep / "methodology").mkdir(parents=True)
        (prep / "methodology" / "scf-overlap.md").write_text("Content")

        _, ids = collect_documents(tmp_path)
        assert "prepared_methodology_scf-overlap" in ids

    def test_top_level_prepared_file(self, tmp_path):
        prep = tmp_path / "research" / "prepared"
        prep.mkdir(parents=True)
        (prep / "overview.md").write_text("Overview content")

        _, ids = collect_documents(tmp_path)
        assert "prepared_overview" in ids

    def test_empty_prepared_file_skipped(self, tmp_path):
        prep = tmp_path / "research" / "prepared"
        prep.mkdir(parents=True)
        (prep / "empty.md").write_text("")
        (prep / "whitespace.md").write_text("   \n  \n  ")

        _, ids = collect_documents(tmp_path)
        assert not any(i.startswith("prepared_") for i in ids)


# ── Parsed markdown ─────────────────────────────────────────────────────────


class TestParsedMarkdown:
    def test_parsed_prefix(self, tmp_path):
        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "smith2024.md").write_text("Parsed content")

        _, ids = collect_documents(tmp_path)
        assert "parsed_smith2024" in ids

    def test_empty_parsed_file_skipped(self, tmp_path):
        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "empty.md").write_text("  \n")

        _, ids = collect_documents(tmp_path)
        assert not any(i.startswith("parsed_") for i in ids)


# ── PDF deduplication ───────────────────────────────────────────────────────


class TestPdfDeduplication:
    def test_pdf_skipped_when_parsed_exists(self, tmp_path):
        """A PDF is skipped if attachments/parsed/ has a .md with the same stem."""
        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "smith2024.md").write_text("Parsed version")

        att = tmp_path / "attachments"
        (att / "smith2024.pdf").write_text("(fake pdf bytes)")

        _, ids = collect_documents(tmp_path)
        assert "parsed_smith2024" in ids
        assert "pdf_smith2024" not in ids

    def test_pdf_collected_when_no_parsed(self, tmp_path):
        att = tmp_path / "attachments"
        att.mkdir(parents=True)
        (att / "novel2025.pdf").write_text("(fake pdf bytes)")

        _, ids = collect_documents(tmp_path)
        assert "pdf_novel2025" in ids


# ── ID uniqueness and collision avoidance ───────────────────────────────────


class TestIdUniqueness:
    def test_no_collision_between_source_and_prepared(self, tmp_path):
        """A source 'foo.md' and a prepared 'foo.md' produce distinct IDs."""
        (tmp_path / "research" / "sources").mkdir(parents=True)
        (tmp_path / "research" / "sources" / "foo.md").write_text("Source foo")

        prep = tmp_path / "research" / "prepared"
        prep.mkdir(parents=True)
        (prep / "foo.md").write_text("Prepared foo")

        _, ids = collect_documents(tmp_path)
        assert "foo" in ids
        assert "prepared_foo" in ids
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"

    def test_all_ids_unique_mixed(self, tmp_path):
        """Full scenario with all four tiers: no duplicate IDs."""
        (tmp_path / "research" / "sources").mkdir(parents=True)
        (tmp_path / "research" / "sources" / "alpha.md").write_text("src alpha")

        prep = tmp_path / "research" / "prepared" / "claims"
        prep.mkdir(parents=True)
        (prep / "C1.md").write_text("claim C1")

        parsed = tmp_path / "attachments" / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "beta.md").write_text("parsed beta")

        att = tmp_path / "attachments"
        (att / "gamma.pdf").write_text("(fake pdf)")

        docs, ids = collect_documents(tmp_path)
        assert len(ids) == 4
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"
        assert set(ids) == {"alpha", "prepared_claims_C1", "parsed_beta", "pdf_gamma"}


# ── extract_pdf_text ────────────────────────────────────────────────────────


class TestExtractPdfText:
    def test_nonexistent_file_returns_empty(self):
        """extract_pdf_text returns '' for a nonexistent path (pymupdf raises)."""
        try:
            import fitz  # noqa: F401
        except ImportError:
            pytest.skip("pymupdf (fitz) not installed")

        result = knowledge.extract_pdf_text(Path("/nonexistent/file.pdf"))
        assert result == ""

    def test_returns_string(self):
        """Smoke check: the function always returns a string."""
        result = knowledge.extract_pdf_text(Path("/nonexistent/file.pdf"))
        assert isinstance(result, str)
