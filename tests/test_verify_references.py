"""Unit tests for verify-references.py."""

import json
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.request
import urllib.error

# Import the module under test (will be created in Task 2)
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "verify_references",
    Path(__file__).parent.parent / "template" / "scripts" / "verify-references.py",
)


def _load_module():
    mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Citation parsing
# ---------------------------------------------------------------------------

class TestParseCitations:
    """Test extraction of \\cite, \\citep, \\citet from LaTeX."""

    def test_citep_single(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text(r"shown previously \citep{smith2024}.")
        result = vr.parse_citations(tex)
        assert len(result) == 1
        assert result[0]["key"] == "smith2024"
        assert result[0]["line"] == 1

    def test_citep_multiple_keys(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text(r"as shown \citep{smith2024,jones2025,lee2023}.")
        result = vr.parse_citations(tex)
        keys = [r["key"] for r in result]
        assert keys == ["smith2024", "jones2025", "lee2023"]

    def test_citet(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text(r"\citet{smith2024} showed that...")
        result = vr.parse_citations(tex)
        assert len(result) == 1
        assert result[0]["key"] == "smith2024"

    def test_plain_cite(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text(r"see \cite{smith2024}.")
        result = vr.parse_citations(tex)
        assert len(result) == 1
        assert result[0]["key"] == "smith2024"

    def test_context_captured(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text(r"The method improves accuracy by 15\% \citep{smith2024}.")
        result = vr.parse_citations(tex)
        assert "improves accuracy" in result[0]["context"]

    def test_multiple_lines(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("line one\nresult \\citep{a2024}\nline three\nmore \\citet{b2025}\n")
        result = vr.parse_citations(tex)
        assert result[0]["line"] == 2
        assert result[1]["line"] == 4

    def test_commented_out_citations_ignored(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("% \\citep{commented2024}\nreal \\citep{real2024}\n")
        result = vr.parse_citations(tex)
        assert len(result) == 1
        assert result[0]["key"] == "real2024"

    def test_no_citations(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("No citations here.")
        result = vr.parse_citations(tex)
        assert result == []

    def test_deduplication_preserves_all_occurrences(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("first \\citep{smith2024}\nsecond \\citep{smith2024}\n")
        result = vr.parse_citations(tex)
        assert len(result) == 2  # both occurrences kept

    def test_mid_line_comment_ignored(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("real \\citep{real2024} % \\citep{fake2024}\n")
        result = vr.parse_citations(tex)
        assert len(result) == 1
        assert result[0]["key"] == "real2024"

    def test_escaped_percent_not_treated_as_comment(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("improved by 15\\% \\citep{smith2024}\n")
        result = vr.parse_citations(tex)
        assert len(result) == 1
        assert result[0]["key"] == "smith2024"


# ---------------------------------------------------------------------------
# BibTeX parsing
# ---------------------------------------------------------------------------

class TestParseBib:
    """Test BibTeX entry extraction."""

    def test_parse_article(self, tmp_path):
        vr = _load_module()
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @article{smith2024,
              author = {Smith, John and Doe, Jane},
              title = {A Great Paper},
              journal = {Nature},
              year = {2024},
              doi = {10.1234/example},
            }
        """))
        result = vr.parse_bib(bib)
        assert "smith2024" in result
        assert result["smith2024"]["title"] == "A Great Paper"
        assert result["smith2024"]["doi"] == "10.1234/example"
        assert result["smith2024"]["year"] == "2024"

    def test_parse_multiple_entries(self, tmp_path):
        vr = _load_module()
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @article{smith2024,
              title = {Paper A},
              year = {2024},
            }
            @inproceedings{jones2025,
              title = {Paper B},
              year = {2025},
            }
        """))
        result = vr.parse_bib(bib)
        assert len(result) == 2
        assert "smith2024" in result
        assert "jones2025" in result

    def test_entry_with_arxiv_id(self, tmp_path):
        vr = _load_module()
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @misc{chen2024,
              title = {ArXiv Paper},
              year = {2024},
              eprint = {2401.12345},
              archiveprefix = {arXiv},
            }
        """))
        result = vr.parse_bib(bib)
        assert result["chen2024"]["eprint"] == "2401.12345"

    def test_empty_bib(self, tmp_path):
        vr = _load_module()
        bib = tmp_path / "references.bib"
        bib.write_text("")
        result = vr.parse_bib(bib)
        assert result == {}

    def test_braced_values(self, tmp_path):
        vr = _load_module()
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @article{smith2024,
              title = {{Deep Learning for {NLP}}},
              year = {2024},
            }
        """))
        result = vr.parse_bib(bib)
        assert "Deep Learning" in result["smith2024"]["title"]

    def test_indented_closing_brace(self, tmp_path):
        vr = _load_module()
        bib = tmp_path / "references.bib"
        bib.write_text("@article{smith2024,\n  title = {A Paper},\n  year = {2024},\n  }\n")
        result = vr.parse_bib(bib)
        assert "smith2024" in result
        assert result["smith2024"]["title"] == "A Paper"


# ---------------------------------------------------------------------------
# Source extract checking
# ---------------------------------------------------------------------------

class TestCheckSourceExtract:
    """Test source extract verification (existence, snapshot, access level)."""

    def test_full_text_with_snapshot(self, tmp_path):
        vr = _load_module()
        sources = tmp_path / "research" / "sources"
        sources.mkdir(parents=True)
        (sources / "smith2024.md").write_text(textwrap.dedent("""\
            # A Great Paper
            **Access Level**: FULL-TEXT

            ## Content Snapshot
            This paper presents a novel method for...
        """))
        result = vr.check_source_extract("smith2024", sources)
        assert result["has_extract"] is True
        assert result["has_snapshot"] is True
        assert result["access_level"] == "FULL-TEXT"

    def test_metadata_only(self, tmp_path):
        vr = _load_module()
        sources = tmp_path / "research" / "sources"
        sources.mkdir(parents=True)
        (sources / "jones2025.md").write_text(textwrap.dedent("""\
            # Some Paper
            **Access Level**: METADATA-ONLY

            ## Content Snapshot
            No content accessed.
        """))
        result = vr.check_source_extract("jones2025", sources)
        assert result["access_level"] == "METADATA-ONLY"
        assert result["has_snapshot"] is False  # "No content accessed" = empty

    def test_missing_extract(self, tmp_path):
        vr = _load_module()
        sources = tmp_path / "research" / "sources"
        sources.mkdir(parents=True)
        result = vr.check_source_extract("missing2024", sources)
        assert result["has_extract"] is False
        assert result["has_snapshot"] is False
        assert result["access_level"] is None

    def test_extract_without_snapshot_section(self, tmp_path):
        vr = _load_module()
        sources = tmp_path / "research" / "sources"
        sources.mkdir(parents=True)
        (sources / "old2023.md").write_text("# Old Paper\n**Access Level**: ABSTRACT-ONLY\n")
        result = vr.check_source_extract("old2023", sources)
        assert result["has_extract"] is True
        assert result["has_snapshot"] is False
        assert result["access_level"] == "ABSTRACT-ONLY"

    def test_abstract_only_with_real_content(self, tmp_path):
        vr = _load_module()
        sources = tmp_path / "research" / "sources"
        sources.mkdir(parents=True)
        (sources / "abs2024.md").write_text(textwrap.dedent("""\
            # Paper
            **Access Level**: ABSTRACT-ONLY

            ## Content Snapshot
            We propose a framework for scalable analysis of...
        """))
        result = vr.check_source_extract("abs2024", sources)
        assert result["has_extract"] is True
        assert result["has_snapshot"] is True
        assert result["access_level"] == "ABSTRACT-ONLY"


# ---------------------------------------------------------------------------
# Artifact checking
# ---------------------------------------------------------------------------

class TestCheckArtifacts:
    """Test PDF and parsed markdown artifact verification."""

    def test_has_pdf(self, tmp_path):
        vr = _load_module()
        attachments = tmp_path / "attachments"
        attachments.mkdir()
        (attachments / "smith2024.pdf").write_text("fake pdf")
        result = vr.check_artifacts("smith2024", attachments, tmp_path / "attachments" / "parsed")
        assert result["has_pdf"] is True

    def test_has_parsed_markdown(self, tmp_path):
        vr = _load_module()
        attachments = tmp_path / "attachments"
        parsed = attachments / "parsed"
        parsed.mkdir(parents=True)
        (parsed / "smith2024.md").write_text("parsed content")
        result = vr.check_artifacts("smith2024", attachments, parsed)
        assert result["has_parsed"] is True

    def test_no_artifacts(self, tmp_path):
        vr = _load_module()
        attachments = tmp_path / "attachments"
        attachments.mkdir()
        parsed = tmp_path / "attachments" / "parsed"
        result = vr.check_artifacts("missing2024", attachments, parsed)
        assert result["has_pdf"] is False
        assert result["has_parsed"] is False

    def test_symlinked_pdf(self, tmp_path):
        vr = _load_module()
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "smith2024.pdf").write_text("cached pdf")
        attachments = tmp_path / "attachments"
        attachments.mkdir()
        (attachments / "smith2024.pdf").symlink_to(cache / "smith2024.pdf")
        result = vr.check_artifacts("smith2024", attachments, tmp_path / "attachments" / "parsed")
        assert result["has_pdf"] is True


# ---------------------------------------------------------------------------
# Reference classification
# ---------------------------------------------------------------------------

class TestClassifyReference:
    """Test reference status classification."""

    def test_verified_full_text(self):
        vr = _load_module()
        status = vr.classify_reference(
            key="smith2024",
            in_bib=True,
            extract={"has_extract": True, "has_snapshot": True, "access_level": "FULL-TEXT"},
            artifacts={"has_pdf": True, "has_parsed": True},
        )
        assert status == "VERIFIED"

    def test_verified_abstract_only(self):
        vr = _load_module()
        status = vr.classify_reference(
            key="abs2024",
            in_bib=True,
            extract={"has_extract": True, "has_snapshot": True, "access_level": "ABSTRACT-ONLY"},
            artifacts={"has_pdf": False, "has_parsed": False},
        )
        assert status == "VERIFIED"

    def test_missing_bib(self):
        vr = _load_module()
        status = vr.classify_reference(
            key="ghost2024",
            in_bib=False,
            extract={"has_extract": False, "has_snapshot": False, "access_level": None},
            artifacts={"has_pdf": False, "has_parsed": False},
        )
        assert status == "MISSING_BIB"

    def test_missing_extract(self):
        vr = _load_module()
        status = vr.classify_reference(
            key="noextract2024",
            in_bib=True,
            extract={"has_extract": False, "has_snapshot": False, "access_level": None},
            artifacts={"has_pdf": False, "has_parsed": False},
        )
        assert status == "MISSING_EXTRACT"

    def test_empty_snapshot(self):
        vr = _load_module()
        status = vr.classify_reference(
            key="empty2024",
            in_bib=True,
            extract={"has_extract": True, "has_snapshot": False, "access_level": "ABSTRACT-ONLY"},
            artifacts={"has_pdf": False, "has_parsed": False},
        )
        assert status == "EMPTY_SNAPSHOT"

    def test_metadata_overclaim(self):
        vr = _load_module()
        status = vr.classify_reference(
            key="meta2024",
            in_bib=True,
            extract={"has_extract": True, "has_snapshot": False, "access_level": "METADATA-ONLY"},
            artifacts={"has_pdf": False, "has_parsed": False},
        )
        assert status == "METADATA_OVERCLAIM"

    def test_full_text_missing_pdf_still_verified(self):
        """FULL-TEXT with snapshot but no PDF is still VERIFIED (PDF may have been deleted)."""
        vr = _load_module()
        status = vr.classify_reference(
            key="nopdf2024",
            in_bib=True,
            extract={"has_extract": True, "has_snapshot": True, "access_level": "FULL-TEXT"},
            artifacts={"has_pdf": False, "has_parsed": False},
        )
        assert status == "VERIFIED"


# ---------------------------------------------------------------------------
# API verification
# ---------------------------------------------------------------------------

class TestApiVerification:
    """Test CrossRef and arXiv API fallback verification."""

    def test_crossref_found(self):
        vr = _load_module()
        response_data = json.dumps({
            "status": "ok",
            "message": {"title": ["A Great Paper"], "DOI": "10.1234/example"},
        }).encode()
        mock_response = MagicMock()
        mock_response.read.return_value = response_data
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch.object(urllib.request, "urlopen", return_value=mock_response):
            result = vr.verify_crossref("10.1234/example")
        assert result["found"] is True

    def test_crossref_not_found(self):
        vr = _load_module()
        with patch.object(
            urllib.request, "urlopen",
            side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None),
        ):
            result = vr.verify_crossref("10.9999/fake")
        assert result["found"] is False

    def test_crossref_network_error(self):
        vr = _load_module()
        with patch.object(
            urllib.request, "urlopen",
            side_effect=urllib.error.URLError("Network unreachable"),
        ):
            result = vr.verify_crossref("10.1234/example")
        assert result["found"] is None  # indeterminate
        assert "error" in result

    def test_arxiv_found(self):
        vr = _load_module()
        response_data = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry><title>A Paper</title></entry>
        </feed>"""
        mock_response = MagicMock()
        mock_response.read.return_value = response_data
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch.object(urllib.request, "urlopen", return_value=mock_response):
            result = vr.verify_arxiv("2401.12345")
        assert result["found"] is True

    def test_arxiv_not_found(self):
        vr = _load_module()
        response_data = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
        </feed>"""
        mock_response = MagicMock()
        mock_response.read.return_value = response_data
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch.object(urllib.request, "urlopen", return_value=mock_response):
            result = vr.verify_arxiv("9999.99999")
        assert result["found"] is False


# ---------------------------------------------------------------------------
# Auto-remediation
# ---------------------------------------------------------------------------

class TestRemediate:
    """Test auto-remediation of fabricated references."""

    def test_remove_citation_from_tex(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("shown previously \\citep{fake2024}.\n")
        bib = tmp_path / "references.bib"
        bib.write_text("@article{fake2024,\n  title = {Fake},\n  year = {2024},\n}\n")
        vr.remediate_fabricated(tex, bib, ["fake2024"])
        content = tex.read_text()
        assert "fake2024" not in content or "REMOVED" in content
        bib_content = bib.read_text()
        assert "fake2024" not in bib_content

    def test_remove_from_multi_cite(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("results \\citep{real2024,fake2024,other2024}.\n")
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @article{real2024,
              title = {Real},
              year = {2024},
            }
            @article{fake2024,
              title = {Fake},
              year = {2024},
            }
            @article{other2024,
              title = {Other},
              year = {2024},
            }
        """))
        vr.remediate_fabricated(tex, bib, ["fake2024"])
        content = tex.read_text()
        # Should keep real2024 and other2024, remove fake2024
        assert "real2024" in content
        assert "other2024" in content
        assert "\\citep{real2024,other2024}" in content or "\\citep{real2024, other2024}" in content

    def test_remove_bib_entry(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("text \\citep{fake2024}.\n")
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @article{keep2024,
              title = {Keep This},
              year = {2024},
            }
            @article{fake2024,
              title = {Remove This},
              year = {2024},
            }
        """))
        vr.remediate_fabricated(tex, bib, ["fake2024"])
        bib_content = bib.read_text()
        assert "keep2024" in bib_content
        assert "fake2024" not in bib_content

    def test_empty_fabricated_list(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("text \\citep{real2024}.\n")
        bib = tmp_path / "references.bib"
        bib.write_text("@article{real2024,\n  title = {Real},\n}\n")
        original = tex.read_text()
        vr.remediate_fabricated(tex, bib, [])
        assert tex.read_text() == original

    def test_sole_citation_removed_leaves_marker(self, tmp_path):
        vr = _load_module()
        tex = tmp_path / "main.tex"
        tex.write_text("This was established \\citep{fake2024}.\n")
        bib = tmp_path / "references.bib"
        bib.write_text("@article{fake2024,\n  title = {Fake},\n  year = {2024},\n}\n")
        vr.remediate_fabricated(tex, bib, ["fake2024"])
        content = tex.read_text()
        assert "REMOVED" in content or "NEEDS-CITATION" in content


# ---------------------------------------------------------------------------
# Integration: full verification pipeline
# ---------------------------------------------------------------------------

class TestVerifyAll:
    """Integration test: full verification pipeline."""

    def _setup_project(self, tmp_path):
        """Create a minimal paper project with mixed reference states."""
        # main.tex
        tex = tmp_path / "main.tex"
        tex.write_text(textwrap.dedent(r"""
            \begin{document}
            Prior work \citep{good2024} established the baseline.
            Others showed \citep{noextract2024} similar results.
            We build on \citet{meta2024} and \citep{good2024}.
            \end{document}
        """).lstrip())

        # references.bib
        bib = tmp_path / "references.bib"
        bib.write_text(textwrap.dedent("""\
            @article{good2024,
              title = {Good Paper},
              year = {2024},
              doi = {10.1234/good},
            }
            @article{noextract2024,
              title = {No Extract},
              year = {2024},
            }
            @article{meta2024,
              title = {Metadata Only},
              year = {2024},
            }
        """))

        # Source extracts
        sources = tmp_path / "research" / "sources"
        sources.mkdir(parents=True)
        (sources / "good2024.md").write_text(textwrap.dedent("""\
            # Good Paper
            **Access Level**: FULL-TEXT
            ## Content Snapshot
            This paper presents a solid method...
        """))
        (sources / "meta2024.md").write_text(textwrap.dedent("""\
            # Metadata Only
            **Access Level**: METADATA-ONLY
            ## Content Snapshot
            No content accessed.
        """))
        # noextract2024 — deliberately no source extract

        # Attachments
        (tmp_path / "attachments").mkdir()
        (tmp_path / "attachments" / "parsed").mkdir()
        (tmp_path / "attachments" / "good2024.pdf").write_text("fake pdf")

        return tex, bib, sources

    def test_verify_all_produces_report(self, tmp_path):
        vr = _load_module()
        tex, bib, sources = self._setup_project(tmp_path)
        report = vr.verify_all(
            tex_path=tex,
            bib_path=bib,
            sources_dir=sources,
            attachments_dir=tmp_path / "attachments",
            parsed_dir=tmp_path / "attachments" / "parsed",
            use_api=False,
        )
        assert report["summary"]["VERIFIED"] == 1
        assert report["summary"]["MISSING_EXTRACT"] == 1
        assert report["summary"]["METADATA_OVERCLAIM"] == 1
        assert "good2024" in report["results"]
        assert report["results"]["good2024"]["status"] == "VERIFIED"
        assert report["results"]["noextract2024"]["status"] == "MISSING_EXTRACT"
        assert report["results"]["meta2024"]["status"] == "METADATA_OVERCLAIM"

    def test_verify_all_counts_citations(self, tmp_path):
        vr = _load_module()
        tex, bib, sources = self._setup_project(tmp_path)
        report = vr.verify_all(
            tex_path=tex, bib_path=bib, sources_dir=sources,
            attachments_dir=tmp_path / "attachments",
            parsed_dir=tmp_path / "attachments" / "parsed",
            use_api=False,
        )
        assert report["total_citations"] == 4  # good2024 appears twice
        assert report["unique_keys"] == 3

    def test_json_output(self, tmp_path):
        vr = _load_module()
        tex, bib, sources = self._setup_project(tmp_path)
        report = vr.verify_all(
            tex_path=tex, bib_path=bib, sources_dir=sources,
            attachments_dir=tmp_path / "attachments",
            parsed_dir=tmp_path / "attachments" / "parsed",
            use_api=False,
        )
        # Should be JSON-serializable
        output = json.dumps(report, indent=2)
        parsed = json.loads(output)
        assert parsed["summary"]["VERIFIED"] == 1
