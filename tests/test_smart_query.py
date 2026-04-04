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
