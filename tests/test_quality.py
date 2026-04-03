"""Unit tests for quality.py — multi-dimensional paper quality scoring."""

import importlib.util
import json
import os
import tempfile
import textwrap
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "quality",
    Path(__file__).parent.parent / "template" / "scripts" / "quality.py",
)


def _load():
    mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Claims matrix parsing
# ---------------------------------------------------------------------------


class TestClaimsMatrixParsing:
    """Tests for parse_claims_matrix."""

    def test_parse_standard_table(self):
        q = _load()
        text = textwrap.dedent("""\
            # Claims Matrix

            | ID | Claim | Evidence | Score | Strength | Warrant | Qualifier | Rebuttal |
            |-|-|-|-|-|-|-|-|
            | C1 | First claim | Some evidence | 0.85 | STRONG | Sound | likely | None |
            | C2 | Second claim | More evidence | 0.50 | MODERATE | Reasonable | possibly | Some rebuttal |
            | C3 | Third claim | Weak evidence | 0.20 | WEAK | Weak | tentatively | Strong rebuttal |
        """)
        claims = q.parse_claims_matrix(text)
        assert len(claims) == 3
        assert claims[0]["id"] == "C1"
        assert claims[0]["score"] == 0.85
        assert claims[0]["strength"] == "STRONG"
        assert claims[0]["warrant"] == "Sound"
        assert claims[1]["strength"] == "MODERATE"
        assert claims[2]["strength"] == "WEAK"

    def test_handle_missing_columns_gracefully(self):
        q = _load()
        # Table with fewer columns than expected
        text = textwrap.dedent("""\
            | ID | Claim | Score |
            |-|-|-|
            | C1 | Only claim | 0.5 |
        """)
        claims = q.parse_claims_matrix(text)
        # Should not crash; may return empty or partial results
        assert isinstance(claims, list)

    def test_empty_input(self):
        q = _load()
        claims = q.parse_claims_matrix("")
        assert claims == []


# ---------------------------------------------------------------------------
# Source extract parsing
# ---------------------------------------------------------------------------


class TestSourceExtractParsing:
    def test_parse_source_extracts(self):
        q = _load()
        with tempfile.TemporaryDirectory() as d:
            sources = Path(d)
            (sources / "smith2024.md").write_text(
                "# Smith 2024\n**Access Level**: FULL-TEXT\nContent here."
            )
            (sources / "jones2023.md").write_text(
                "# Jones 2023\n**Access Level**: ABSTRACT-ONLY\nAbstract content."
            )
            (sources / "doe2022.md").write_text(
                "# Doe 2022\n**Access Level**: METADATA-ONLY\n"
            )
            result = q.parse_source_extracts(sources)
            assert len(result) == 3
            levels = {s["key"]: s["access_level"] for s in result}
            assert levels["smith2024"] == "FULL-TEXT"
            assert levels["jones2023"] == "ABSTRACT-ONLY"
            assert levels["doe2022"] == "METADATA-ONLY"

    def test_empty_dir(self):
        q = _load()
        with tempfile.TemporaryDirectory() as d:
            result = q.parse_source_extracts(Path(d))
            assert result == []


# ---------------------------------------------------------------------------
# Evidence quality
# ---------------------------------------------------------------------------


class TestEvidenceQuality:
    def test_all_strong(self):
        q = _load()
        claims = [
            {"id": "C1", "claim": "A", "score": 0.9, "strength": "STRONG", "warrant": "Sound"},
            {"id": "C2", "claim": "B", "score": 0.8, "strength": "STRONG", "warrant": "Sound"},
        ]
        result = q.score_evidence(claims)
        assert result["score"] >= 90
        assert "claim_distribution" in result["details"]

    def test_mixed_strengths(self):
        q = _load()
        claims = [
            {"id": "C1", "claim": "A", "score": 0.9, "strength": "STRONG", "warrant": "Sound"},
            {"id": "C2", "claim": "B", "score": 0.5, "strength": "MODERATE", "warrant": "Reasonable"},
            {"id": "C3", "claim": "C", "score": 0.2, "strength": "WEAK", "warrant": "Weak"},
        ]
        result = q.score_evidence(claims)
        assert 30 < result["score"] < 80

    def test_critical_penalty(self):
        q = _load()
        claims = [
            {"id": "C1", "claim": "A", "score": 0.9, "strength": "STRONG", "warrant": "Sound"},
            {"id": "C2", "claim": "B", "score": 0.0, "strength": "CRITICAL", "warrant": "Invalid"},
        ]
        result = q.score_evidence(claims)
        # CRITICAL should severely lower the score
        assert result["score"] < 60
        assert result["details"]["critical_count"] == 1

    def test_no_claims(self):
        q = _load()
        result = q.score_evidence([])
        assert result["score"] == 0

    def test_warrant_effect(self):
        q = _load()
        # Same strength, different warrants
        good = [{"id": "C1", "claim": "A", "score": 0.8, "strength": "STRONG", "warrant": "Sound"}]
        bad = [{"id": "C1", "claim": "A", "score": 0.8, "strength": "STRONG", "warrant": "Missing"}]
        r_good = q.score_evidence(good)
        r_bad = q.score_evidence(bad)
        assert r_good["score"] > r_bad["score"]

    def test_output_structure(self):
        q = _load()
        claims = [{"id": "C1", "claim": "A", "score": 0.9, "strength": "STRONG", "warrant": "Sound"}]
        result = q.score_evidence(claims)
        assert "score" in result
        assert "details" in result
        assert isinstance(result["score"], (int, float))
        assert 0 <= result["score"] <= 100
        d = result["details"]
        for key in ("claim_distribution", "total_claims", "critical_count",
                     "avg_warrant_adjustment", "base_score"):
            assert key in d, f"Missing detail key: {key}"


# ---------------------------------------------------------------------------
# Writing quality
# ---------------------------------------------------------------------------


class TestWritingQuality:
    def test_clean_prose_high(self):
        q = _load()
        tex = (
            "We propose a novel method for detecting anomalies in network traffic. "
            "The approach uses statistical models to identify deviations from normal behavior. "
            "Our experiments show a significant improvement over baseline methods. "
            "The results demonstrate that the technique generalizes across diverse datasets. "
            "Performance metrics confirm the robustness of our framework."
        )
        result = q.score_writing(tex)
        assert result["score"] >= 50

    def test_ai_patterns_low(self):
        q = _load()
        tex = (
            "We delve into the multifaceted landscape of this realm. "
            "Furthermore, the tapestry of results is groundbreaking. "
            "Moreover, it is worth noting that this cutting-edge approach "
            "is truly a paradigm shift. Additionally, the fact that "
            "it is evident that this works is remarkable."
        )
        result = q.score_writing(tex)
        assert result["score"] < 45
        assert result["details"]["ai_pattern_count"] > 5

    def test_em_dashes_detected(self):
        q = _load()
        tex = (
            "This approach — while novel — provides significant improvements. "
            "The method --- which we describe below --- outperforms baselines. "
            "Results show clear benefits for all test cases."
        )
        result = q.score_writing(tex)
        assert result["details"]["ai_pattern_count"] >= 2

    def test_empty_text(self):
        q = _load()
        result = q.score_writing("")
        assert result["score"] == 0

    def test_sentence_variety_tracked(self):
        q = _load()
        tex = (
            "Short. "
            "Also short. "
            "This is a much longer sentence that contains many more words than the short ones. "
            "Tiny. "
            "Another long sentence with substantial variation in word count compared to others."
        )
        result = q.score_writing(tex)
        assert result["details"]["sentence_length_stddev"] > 0
        assert result["details"]["sentence_count"] >= 4


# ---------------------------------------------------------------------------
# Structural integrity
# ---------------------------------------------------------------------------


class TestStructuralIntegrity:
    def test_complete_paper_high(self):
        q = _load()
        tex = textwrap.dedent(r"""
            \documentclass{article}
            \begin{document}
            \section{Introduction} Intro text.
            \section{Related Work} Related text.
            \section{Methods} Method text.
            \section{Results} Results text.
            \section{Discussion} Discussion text.
            \section{Conclusion} Conclusion text.
            \label{fig:example}
            See \ref{fig:example}.
            \end{document}
        """)
        venue = {"sections": ["Introduction", "Related Work", "Methods", "Results", "Discussion", "Conclusion"]}
        result = q.score_structure(tex, venue, compile_ok=True, compile_warnings=0)
        assert result["score"] >= 80

    def test_missing_sections_low(self):
        q = _load()
        tex = r"\section{Introduction} Only intro."
        venue = {"sections": ["Introduction", "Related Work", "Methods", "Results", "Discussion", "Conclusion"]}
        # A paper missing 5/6 sections should score significantly below a complete one
        full_tex = (
            r"\section{Introduction} a. \section{Related Work} b. "
            r"\section{Methods} c. \section{Results} d. "
            r"\section{Discussion} e. \section{Conclusion} f."
        )
        full = q.score_structure(full_tex, venue, compile_ok=True, compile_warnings=0)
        result = q.score_structure(tex, venue, compile_ok=True, compile_warnings=0)
        assert result["score"] < full["score"]
        assert result["details"]["sections_missing"] == [
            "Related Work", "Methods", "Results", "Discussion", "Conclusion"
        ]

    def test_compile_failure_penalty(self):
        q = _load()
        tex = r"\section{Introduction} Text."
        venue = {"sections": ["Introduction"]}
        ok = q.score_structure(tex, venue, compile_ok=True, compile_warnings=0)
        fail = q.score_structure(tex, venue, compile_ok=False, compile_warnings=0)
        assert ok["score"] > fail["score"]

    def test_placeholders_detected(self):
        q = _load()
        tex_dirty = textwrap.dedent(r"""
            \section{Introduction} TODO: write this.
            \section{Methods} TBD method.
            \section{Results} FIXME results.
            \lipsum[1]
        """)
        tex_clean = textwrap.dedent(r"""
            \section{Introduction} We propose a method.
            \section{Methods} Our approach works.
            \section{Results} Results are strong.
        """)
        venue = {"sections": ["Introduction", "Methods", "Results"]}
        dirty = q.score_structure(tex_dirty, venue, compile_ok=True, compile_warnings=0)
        clean = q.score_structure(tex_clean, venue, compile_ok=True, compile_warnings=0)
        assert dirty["details"]["placeholder_count"] >= 4
        assert dirty["score"] < clean["score"]


# ---------------------------------------------------------------------------
# Research depth
# ---------------------------------------------------------------------------


class TestResearchDepth:
    def test_high_full_text_ratio(self):
        q = _load()
        sources = [
            {"key": "a", "access_level": "FULL-TEXT"},
            {"key": "b", "access_level": "FULL-TEXT"},
            {"key": "c", "access_level": "FULL-TEXT"},
        ]
        result = q.score_research(sources, citation_count=30, word_count=2000, kg_available=True)
        assert result["score"] >= 80

    def test_all_metadata_only(self):
        q = _load()
        sources = [
            {"key": "a", "access_level": "METADATA-ONLY"},
            {"key": "b", "access_level": "METADATA-ONLY"},
        ]
        result = q.score_research(sources, citation_count=5, word_count=2000, kg_available=False)
        assert result["score"] < 30

    def test_citation_density_effect(self):
        q = _load()
        sources = [{"key": "a", "access_level": "FULL-TEXT"}] * 10
        sparse = q.score_research(sources, citation_count=2, word_count=5000, kg_available=False)
        dense = q.score_research(sources, citation_count=75, word_count=5000, kg_available=False)
        assert dense["score"] > sparse["score"]

    def test_no_sources(self):
        q = _load()
        result = q.score_research([], citation_count=0, word_count=1000, kg_available=False)
        assert result["score"] == 0


# ---------------------------------------------------------------------------
# Provenance coverage
# ---------------------------------------------------------------------------


class TestProvenanceCoverage:
    def test_full_coverage(self):
        q = _load()
        targets = {"introduction/p1", "methods/p2", "results/p3"}
        result = q.score_provenance(targets, targets)
        assert result["score"] == 100

    def test_no_provenance(self):
        q = _load()
        result = q.score_provenance(set(), {"introduction/p1", "methods/p2"})
        assert result["score"] == 0

    def test_partial_coverage(self):
        q = _load()
        traced = {"introduction/p1"}
        total = {"introduction/p1", "methods/p2", "results/p3", "discussion/p4"}
        result = q.score_provenance(traced, total)
        assert result["score"] == 25

    def test_empty_paper(self):
        q = _load()
        result = q.score_provenance(set(), set())
        assert result["score"] == 0


# ---------------------------------------------------------------------------
# Full scorecard
# ---------------------------------------------------------------------------


class TestFullScorecard:
    def _make_project(self, tmpdir: Path):
        """Create minimal paper project artifacts in tmpdir."""
        # main.tex
        (tmpdir / "main.tex").write_text(textwrap.dedent(r"""
            \documentclass{article}
            \begin{document}
            \section{Introduction}
            We propose a method for analysis.
            This paper describes our approach.
            \label{sec:intro}
            See \ref{sec:intro}.
            \section{Related Work}
            Prior work exists.
            \section{Methods}
            Our method works as follows.
            \section{Results}
            Results are strong.
            \section{Discussion}
            We discuss implications.
            \section{Conclusion}
            In conclusion, the method works.
            \end{document}
        """))

        # .venue.json
        (tmpdir / ".venue.json").write_text(json.dumps({
            "sections": ["Introduction", "Related Work", "Methods",
                         "Results", "Discussion", "Conclusion"]
        }))

        # research/claims_matrix.md
        research = tmpdir / "research"
        research.mkdir()
        (research / "claims_matrix.md").write_text(textwrap.dedent("""\
            | ID | Claim | Evidence | Score | Strength | Warrant | Qualifier | Rebuttal |
            |-|-|-|-|-|-|-|-|
            | C1 | Main claim | Strong evidence | 0.9 | STRONG | Sound | likely | None |
            | C2 | Secondary | Moderate evidence | 0.6 | MODERATE | Reasonable | possibly | Minor |
        """))

        # research/sources/
        sources = research / "sources"
        sources.mkdir()
        (sources / "smith2024.md").write_text("**Access Level**: FULL-TEXT\nContent.")
        (sources / "jones2023.md").write_text("**Access Level**: ABSTRACT-ONLY\nAbstract.")

        # research/provenance.jsonl
        (research / "provenance.jsonl").write_text(
            json.dumps({"action": "write", "target": "introduction/p1"}) + "\n"
            + json.dumps({"action": "revise", "target": "methods/p1"}) + "\n"
        )

        # main.log (compile success indicator)
        (tmpdir / "main.log").write_text("Output written on main.pdf\n")

    def test_has_all_dimensions(self):
        q = _load()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            self._make_project(p)
            sc = q.compute_scorecard(p)
            for dim in ("evidence", "writing", "structure", "research", "provenance"):
                assert dim in sc["dimensions"], f"Missing dimension: {dim}"
                assert "score" in sc["dimensions"][dim]
                assert "details" in sc["dimensions"][dim]

    def test_overall_is_weighted_average(self):
        q = _load()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            self._make_project(p)
            sc = q.compute_scorecard(p)
            dims = sc["dimensions"]
            expected = round(
                dims["evidence"]["score"] * 0.30
                + dims["writing"]["score"] * 0.20
                + dims["structure"]["score"] * 0.15
                + dims["research"]["score"] * 0.20
                + dims["provenance"]["score"] * 0.15
            )
            assert abs(sc["overall"] - expected) <= 1

    def test_text_format_contains_all_dims(self):
        q = _load()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            self._make_project(p)
            sc = q.compute_scorecard(p)
            text = q.format_scorecard_text(sc)
            for dim in ("evidence", "writing", "structure", "research", "provenance"):
                assert dim in text.lower()
            assert "OVERALL" in text or "overall" in text.lower()

    def test_grade_mapping(self):
        q = _load()
        assert q._grade(95) == "A"
        assert q._grade(85) == "B+"
        assert q._grade(75) == "B"
        assert q._grade(65) == "C+"
        assert q._grade(55) == "C"
        assert q._grade(45) == "D"
        assert q._grade(30) == "F"
