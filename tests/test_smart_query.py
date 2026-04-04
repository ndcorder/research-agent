"""Tests for smart query classification in knowledge.py."""

import os
import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import knowledge.py safely (same pattern as test_knowledge.py)
# ---------------------------------------------------------------------------

os.environ.setdefault("OPENROUTER_API_KEY", "test-key-not-real")

_spec = importlib.util.spec_from_file_location(
    "knowledge",
    Path(__file__).parent.parent / "template" / "scripts" / "knowledge.py",
)
knowledge = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(knowledge)
except Exception:
    pytest.skip("Could not import knowledge.py (missing deps?)", allow_module_level=True)

QueryPattern = knowledge.QueryPattern
classify_query = knowledge.classify_query
EntityMatch = knowledge.EntityMatch
extract_query_targets = knowledge.extract_query_targets
_search_entities_in_graph = knowledge._search_entities_in_graph
_get_graph_nodes = knowledge._get_graph_nodes
_get_entity_relationships = knowledge._get_entity_relationships
get_retrieval_modes = knowledge.get_retrieval_modes
merge_retrieval_results = knowledge.merge_retrieval_results
compute_confidence = knowledge.compute_confidence
format_smart_output = knowledge.format_smart_output
_extract_source_documents = knowledge._extract_source_documents
_build_preflight_context = knowledge._build_preflight_context


class TestClassifyQuery:
    """Test classify_query returns the correct QueryPattern for various inputs."""

    # -- SPECIFIC_PAPER --

    def test_quoted_title_single(self):
        assert classify_query("'Attention Is All You Need'") == QueryPattern.SPECIFIC_PAPER

    def test_quoted_title_double(self):
        assert classify_query('"Scaling Laws for Neural Language Models"') == QueryPattern.SPECIFIC_PAPER

    def test_paper_by_author(self):
        assert classify_query("paper by Vaswani on transformers") == QueryPattern.SPECIFIC_PAPER

    def test_bibtex_key(self):
        assert classify_query("vaswani2017") == QueryPattern.SPECIFIC_PAPER

    def test_bibtex_key_with_suffix(self):
        assert classify_query("brown2020language") == QueryPattern.SPECIFIC_PAPER

    # -- CONCEPT_EXPLORATION --

    def test_what_is(self):
        assert classify_query("what is attention mechanism") == QueryPattern.CONCEPT_EXPLORATION

    def test_what_are(self):
        assert classify_query("what are transformers") == QueryPattern.CONCEPT_EXPLORATION

    def test_approaches_to(self):
        assert classify_query("approaches to few-shot learning") == QueryPattern.CONCEPT_EXPLORATION

    def test_how_does_work(self):
        assert classify_query("how does RLHF work") == QueryPattern.CONCEPT_EXPLORATION

    def test_definition(self):
        assert classify_query("definition of self-attention") == QueryPattern.CONCEPT_EXPLORATION

    # -- EVIDENCE --

    def test_evidence_for(self):
        assert classify_query("evidence for scaling hypothesis") == QueryPattern.EVIDENCE

    def test_evidence_against(self):
        assert classify_query("evidence against lottery ticket") == QueryPattern.EVIDENCE

    def test_supports_claim(self):
        assert classify_query("what supports the claim that larger models generalize better") == QueryPattern.EVIDENCE

    def test_evidence_supporting(self):
        assert classify_query("evidence supporting emergent abilities") == QueryPattern.EVIDENCE

    # -- CONTRADICTION --

    def test_contradictions(self):
        assert classify_query("contradictions in scaling laws literature") == QueryPattern.CONTRADICTION

    def test_disagree(self):
        assert classify_query("which sources disagree about emergence") == QueryPattern.CONTRADICTION

    def test_tension(self):
        assert classify_query("tension between efficiency and accuracy claims") == QueryPattern.CONTRADICTION

    def test_conflicts_with(self):
        assert classify_query("what conflicts with the grokking hypothesis") == QueryPattern.CONTRADICTION

    # -- BROAD_SURVEY --

    def test_what_do_sources_say(self):
        assert classify_query("what do sources say about chain of thought") == QueryPattern.BROAD_SURVEY

    def test_state_of(self):
        assert classify_query("state of the art in code generation") == QueryPattern.BROAD_SURVEY

    def test_overview(self):
        assert classify_query("overview of RLHF approaches") == QueryPattern.BROAD_SURVEY

    def test_summarize(self):
        assert classify_query("summarize the literature on in-context learning") == QueryPattern.BROAD_SURVEY

    # -- DEFAULT --

    def test_plain_topic(self):
        assert classify_query("transformer architecture") == QueryPattern.DEFAULT

    def test_bare_question(self):
        assert classify_query("multi-head attention layers") == QueryPattern.DEFAULT

    # -- Priority ordering --

    def test_evidence_beats_concept(self):
        """'evidence for what is X' should match EVIDENCE, not CONCEPT_EXPLORATION."""
        assert classify_query("evidence for what is claimed about scaling") == QueryPattern.EVIDENCE

    def test_specific_paper_beats_all(self):
        """Quoted title should match SPECIFIC_PAPER even with other keywords."""
        assert classify_query("evidence from 'Attention Is All You Need'") == QueryPattern.SPECIFIC_PAPER


# ===========================================================================
# Task 2 — Entity pre-flight search
# ===========================================================================


class TestEntityMatch:
    """EntityMatch dataclass field verification."""

    def test_fields_exist(self):
        em = EntityMatch(name="foo", entity_type="concept", score=0.9, source="graph")
        assert em.name == "foo"
        assert em.entity_type == "concept"
        assert em.score == 0.9
        assert em.source == "graph"

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(EntityMatch)


class TestExtractQueryTargets:
    """Test extract_query_targets for quoted strings and bibtex keys."""

    def test_double_quoted(self):
        assert extract_query_targets('"Attention Is All You Need"') == [
            "Attention Is All You Need"
        ]

    def test_single_quoted(self):
        assert extract_query_targets("'Scaling Laws for LLMs'") == [
            "Scaling Laws for LLMs"
        ]

    def test_smart_quotes(self):
        assert extract_query_targets("\u201cSmart Quotes\u201d") == ["Smart Quotes"]

    def test_bibtex_key(self):
        assert extract_query_targets("vaswani2017") == ["vaswani2017"]

    def test_bibtex_key_with_suffix(self):
        assert extract_query_targets("brown2020a") == ["brown2020a"]

    def test_no_targets(self):
        assert extract_query_targets("what is attention") == []

    def test_multiple_targets(self):
        result = extract_query_targets('"Paper One" and vaswani2017')
        assert "Paper One" in result
        assert "vaswani2017" in result

    def test_short_quoted_ignored(self):
        """Quoted strings < 3 chars should be excluded."""
        assert extract_query_targets('"ab"') == []

    def test_dedup_quoted_over_bibtex(self):
        """If a quoted string matches a bibtex pattern, keep quoted version only."""
        result = extract_query_targets('"vaswani2017"')
        assert result == ["vaswani2017"]
        assert len(result) == 1


class TestEntityPreflight:
    """Test _search_entities_in_graph for substring matching."""

    def test_exact_match(self):
        nodes = {"attention mechanism": {"entity_type": "concept"}}
        matches = _search_entities_in_graph(nodes, ["attention mechanism"])
        assert len(matches) == 1
        assert matches[0].name == "attention mechanism"
        assert matches[0].score == 1.0

    def test_substring_match(self):
        nodes = {"multi-head attention mechanism": {"entity_type": "concept"}}
        matches = _search_entities_in_graph(nodes, ["attention mechanism"])
        assert len(matches) == 1
        assert matches[0].name == "multi-head attention mechanism"
        assert matches[0].score < 1.0

    def test_bibtex_key_match(self):
        nodes = {"vaswani2017": {"entity_type": "paper"}}
        matches = _search_entities_in_graph(nodes, ["vaswani2017"])
        assert len(matches) == 1
        assert matches[0].entity_type == "paper"

    def test_no_match(self):
        nodes = {"transformer": {"entity_type": "concept"}}
        matches = _search_entities_in_graph(nodes, ["quantum computing"])
        assert len(matches) == 0

    def test_case_insensitive(self):
        nodes = {"Attention Mechanism": {"entity_type": "concept"}}
        matches = _search_entities_in_graph(nodes, ["attention mechanism"])
        assert len(matches) == 1

    def test_sorted_by_score_descending(self):
        nodes = {
            "attention": {"entity_type": "concept"},
            "multi-head attention mechanism": {"entity_type": "concept"},
        }
        matches = _search_entities_in_graph(nodes, ["attention"])
        assert matches[0].score >= matches[-1].score

    def test_dedup_by_name(self):
        nodes = {"attention": {"entity_type": "concept"}}
        matches = _search_entities_in_graph(nodes, ["attention", "attention"])
        assert len(matches) == 1


# ---------------------------------------------------------------------------
# Multi-strategy retrieval tests
# ---------------------------------------------------------------------------


class TestGetRetrievalModes:
    def test_specific_paper_modes(self):
        assert get_retrieval_modes(QueryPattern.SPECIFIC_PAPER) == ["naive", "local"]

    def test_concept_exploration_modes(self):
        assert get_retrieval_modes(QueryPattern.CONCEPT_EXPLORATION) == ["hybrid", "naive"]

    def test_evidence_modes(self):
        assert get_retrieval_modes(QueryPattern.EVIDENCE) == ["hybrid", "naive"]

    def test_contradiction_modes(self):
        assert get_retrieval_modes(QueryPattern.CONTRADICTION) == ["global", "hybrid"]

    def test_broad_survey_modes(self):
        assert get_retrieval_modes(QueryPattern.BROAD_SURVEY) == ["hybrid", "naive"]

    def test_default_modes(self):
        assert get_retrieval_modes(QueryPattern.DEFAULT) == ["hybrid", "naive"]

    def test_returns_list_of_strings(self):
        for pattern in QueryPattern:
            modes = get_retrieval_modes(pattern)
            assert isinstance(modes, list)
            assert all(isinstance(m, str) for m in modes)


class TestMergeRetrievalResults:
    def test_empty_input(self):
        assert merge_retrieval_results([]) == {"entities": [], "relationships": [], "chunks": []}

    def test_single_result_passthrough(self):
        data = {
            "entities": [{"entity_name": "A", "description": "desc"}],
            "relationships": [{"src_id": "A", "tgt_id": "B", "description": "rel"}],
            "chunks": [{"content": "text", "source_id": "s1"}],
        }
        result = merge_retrieval_results([data])
        assert len(result["entities"]) == 1
        assert len(result["relationships"]) == 1
        assert len(result["chunks"]) == 1

    def test_deduplicates_entities(self):
        r1 = {"entities": [{"entity_name": "A", "description": "a"}], "relationships": [], "chunks": []}
        r2 = {"entities": [{"entity_name": "A", "description": "a"}], "relationships": [], "chunks": []}
        assert len(merge_retrieval_results([r1, r2])["entities"]) == 1

    def test_merges_different_entities(self):
        r1 = {"entities": [{"entity_name": "A", "description": "a"}], "relationships": [], "chunks": []}
        r2 = {"entities": [{"entity_name": "B", "description": "b"}], "relationships": [], "chunks": []}
        assert len(merge_retrieval_results([r1, r2])["entities"]) == 2

    def test_deduplicates_relationships(self):
        rel = {"src_id": "A", "tgt_id": "B", "description": "rel"}
        r1 = {"entities": [], "relationships": [rel], "chunks": []}
        r2 = {"entities": [], "relationships": [rel], "chunks": []}
        assert len(merge_retrieval_results([r1, r2])["relationships"]) == 1

    def test_deduplicates_chunks_by_content(self):
        c = {"content": "same text", "source_id": "s1"}
        r1 = {"entities": [], "relationships": [], "chunks": [c]}
        r2 = {"entities": [], "relationships": [], "chunks": [c]}
        assert len(merge_retrieval_results([r1, r2])["chunks"]) == 1

    def test_preserves_order(self):
        r1 = {"entities": [{"entity_name": "A"}, {"entity_name": "B"}], "relationships": [], "chunks": []}
        r2 = {"entities": [{"entity_name": "C"}], "relationships": [], "chunks": []}
        names = [e["entity_name"] for e in merge_retrieval_results([r1, r2])["entities"]]
        assert names == ["A", "B", "C"]

    def test_missing_keys_tolerated(self):
        result = merge_retrieval_results([{"entities": [{"entity_name": "X"}]}])
        assert len(result["entities"]) == 1
        assert result["relationships"] == []
        assert result["chunks"] == []


# ---------------------------------------------------------------------------
# Task 4: Synthesis and structured output
# ---------------------------------------------------------------------------


class TestComputeConfidence:
    def test_high_multiple_entities_and_modes(self):
        assert compute_confidence(entity_matches=2, modes_contributed=2, total_chunks=0) == "HIGH"

    def test_high_many_entities_and_modes(self):
        assert compute_confidence(entity_matches=5, modes_contributed=3, total_chunks=10) == "HIGH"

    def test_medium_one_entity(self):
        assert compute_confidence(entity_matches=1, modes_contributed=1, total_chunks=0) == "MEDIUM"

    def test_medium_two_modes_many_chunks(self):
        assert compute_confidence(entity_matches=0, modes_contributed=2, total_chunks=5) == "MEDIUM"

    def test_low_no_entities_one_mode(self):
        assert compute_confidence(entity_matches=0, modes_contributed=1, total_chunks=3) == "LOW"

    def test_low_empty(self):
        assert compute_confidence(entity_matches=0, modes_contributed=0, total_chunks=0) == "LOW"


class TestFormatSmartOutput:
    def test_contains_confidence(self):
        out = format_smart_output(
            confidence="HIGH",
            entity_matches=[EntityMatch("A", "CONCEPT", 1.0, "graph")],
            source_documents=["doc1.md"],
            synthesis="Answer text.",
            entity_context=[],
        )
        assert "**Confidence:** HIGH" in out
        assert "1 entities matched" in out or "1 entity" in out

    def test_contains_synthesis(self):
        out = format_smart_output(
            confidence="MEDIUM",
            entity_matches=[],
            source_documents=[],
            synthesis="Some synthesis.",
            entity_context=[],
        )
        assert "Some synthesis." in out
        assert "### Answer" in out

    def test_contains_entity_context(self):
        out = format_smart_output(
            confidence="HIGH",
            entity_matches=[EntityMatch("A", "CONCEPT", 1.0, "graph"), EntityMatch("B", "PAPER", 0.9, "graph")],
            source_documents=["doc1.md", "doc2.md"],
            synthesis="Answer.",
            entity_context=["A \u2192 RELATES \u2192 B"],
        )
        assert "### Entity Context" in out
        assert "A \u2192 RELATES \u2192 B" in out

    def test_no_entity_context_when_empty(self):
        out = format_smart_output(
            confidence="LOW",
            entity_matches=[],
            source_documents=[],
            synthesis="Answer.",
            entity_context=[],
        )
        assert "### Entity Context" not in out


class TestExtractSourceDocuments:
    def test_extracts_from_chunks(self):
        merged = {
            "entities": [],
            "relationships": [],
            "chunks": [
                {"content": "text", "source_id": "doc1.md"},
                {"content": "other", "source_id": "doc2.md"},
            ],
        }
        result = _extract_source_documents(merged)
        assert result == ["doc1.md", "doc2.md"]

    def test_extracts_from_entity_source_ids(self):
        merged = {
            "entities": [{"entity_name": "A", "source_id": "src1.md\tsrc2.md"}],
            "relationships": [],
            "chunks": [],
        }
        result = _extract_source_documents(merged)
        assert "src1.md" in result
        assert "src2.md" in result

    def test_deduplicates(self):
        merged = {
            "entities": [{"entity_name": "A", "source_id": "doc1.md"}],
            "relationships": [],
            "chunks": [{"content": "text", "source_id": "doc1.md"}],
        }
        result = _extract_source_documents(merged)
        assert result == ["doc1.md"]

    def test_handles_empty(self):
        merged = {"entities": [], "relationships": [], "chunks": []}
        result = _extract_source_documents(merged)
        assert result == []


# ---------------------------------------------------------------------------
# Task 6: Build preflight context
# ---------------------------------------------------------------------------


class TestBuildPreflightContext:
    def test_builds_context_string(self):
        matches = [EntityMatch("Agency Theory", "Concept", 1.0, "exact")]
        rels = ["Agency Theory → CONTRASTS_WITH → Stewardship Theory"]
        ctx = _build_preflight_context(matches, rels)
        assert "Agency Theory" in ctx
        assert "CONTRASTS_WITH" in ctx

    def test_empty_when_no_matches(self):
        ctx = _build_preflight_context([], [])
        assert ctx == ""

    def test_multiple_entities(self):
        matches = [
            EntityMatch("A", "Concept", 1.0, "exact"),
            EntityMatch("B", "Method", 0.8, "graph"),
        ]
        ctx = _build_preflight_context(matches, ["A → uses → B"])
        assert "A" in ctx and "B" in ctx
        assert "uses" in ctx
