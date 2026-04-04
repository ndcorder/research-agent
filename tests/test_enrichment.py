"""Tests for bibtex parsing / knowledge graph enrichment in knowledge.py."""

import os
import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import knowledge.py safely (same pattern as test_smart_query.py)
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

_normalize_author = knowledge._normalize_author
_strip_braces = knowledge._strip_braces
parse_bib_entries = knowledge.parse_bib_entries
parse_source_headers = knowledge.parse_source_headers
parse_all_source_headers = knowledge.parse_all_source_headers
parse_source_body = knowledge.parse_source_body
merge_enrichment_into_graph = knowledge.merge_enrichment_into_graph


# ---------------------------------------------------------------------------
# TestNormalizeAuthor
# ---------------------------------------------------------------------------

class TestNormalizeAuthor:
    """Tests for _normalize_author helper."""

    def test_last_comma_first(self):
        result = _normalize_author("Gordon, Lawrence A.")
        assert result["last"] == "Gordon"
        assert result["first"] == "Lawrence A."
        assert result["normalized"] == "gordon, l"

    def test_first_last(self):
        result = _normalize_author("Martin Loeb")
        assert result["last"] == "Loeb"
        assert result["first"] == "Martin"
        assert result["normalized"] == "loeb, m"

    def test_single_name(self):
        result = _normalize_author("Aristotle")
        assert result["last"] == "Aristotle"
        assert result["first"] == ""
        assert result["normalized"] == "aristotle,"


# ---------------------------------------------------------------------------
# TestParseBibEntries
# ---------------------------------------------------------------------------

_SINGLE_ARTICLE = r"""
@article{gordon2002,
  author    = {Gordon, Lawrence A. and Loeb, Martin P.},
  title     = {The Economics of Information Security Investment},
  journal   = {ACM Transactions on Information and System Security},
  volume    = {5},
  number    = {4},
  pages     = {438--457},
  year      = {2002},
  doi       = {10.1145/581271.581274},
}
"""

_TWO_ENTRIES = r"""
@article{gordon2002,
  author    = {Gordon, Lawrence A. and Loeb, Martin P.},
  title     = {The Economics of Information Security Investment},
  journal   = {ACM Transactions on Information and System Security},
  year      = {2002},
  doi       = {10.1145/581271.581274},
}

@inproceedings{smith2020,
  author    = {Smith, John},
  title     = {A Novel Approach to {AI} Safety},
  booktitle = {Proceedings of the AAAI Conference},
  year      = {2020},
}
"""

_SHARED_AUTHOR = r"""
@article{paper1,
  author = {Smith, John and Doe, Jane},
  title  = {First Paper},
  journal = {Nature},
  year   = {2020},
}

@article{paper2,
  author = {John Smith and Alice Wonder},
  title  = {Second Paper},
  journal = {Science},
  year   = {2021},
}
"""


class TestParseBibEntries:
    """Tests for parse_bib_entries."""

    def test_single_article(self):
        result = parse_bib_entries(_SINGLE_ARTICLE)
        assert len(result["papers"]) == 1
        paper = result["papers"][0]
        assert paper["key"] == "gordon2002"
        assert paper["entry_type"] == "article"
        assert paper["year"] == "2002"
        assert paper["doi"] == "10.1145/581271.581274"
        assert "Economics" in paper["title"]

    def test_multiple_entries(self):
        result = parse_bib_entries(_TWO_ENTRIES)
        assert len(result["papers"]) == 2
        keys = {p["key"] for p in result["papers"]}
        assert keys == {"gordon2002", "smith2020"}

    def test_author_dedup(self):
        result = parse_bib_entries(_SHARED_AUTHOR)
        normalized = [a["normalized"] for a in result["authors"]]
        # "Smith, John" appears in both entries; should be deduplicated
        assert normalized.count("smith, j") == 1

    def test_venue_from_journal(self):
        result = parse_bib_entries(_SINGLE_ARTICLE)
        venue_names = [v["name"] for v in result["venues"]]
        assert "ACM Transactions on Information and System Security" in venue_names

    def test_venue_from_booktitle(self):
        result = parse_bib_entries(_TWO_ENTRIES)
        venue_names = [v["name"] for v in result["venues"]]
        assert "Proceedings of the AAAI Conference" in venue_names

    def test_empty_bib(self):
        result = parse_bib_entries("")
        assert result["papers"] == []
        assert result["authors"] == []
        assert result["venues"] == []
        assert result["relationships"] == []

    def test_relationships_created(self):
        result = parse_bib_entries(_SINGLE_ARTICLE)
        rels = result["relationships"]
        authored = [r for r in rels if r["type"] == "AUTHORED_BY"]
        published = [r for r in rels if r["type"] == "PUBLISHED_IN"]
        assert len(authored) == 2  # two authors
        assert len(published) == 1
        assert authored[0]["src"] == "gordon2002"
        assert published[0]["tgt"] == "acm transactions on information and system security"

    def test_braces_in_title_stripped(self):
        result = parse_bib_entries(_TWO_ENTRIES)
        smith_paper = [p for p in result["papers"] if p["key"] == "smith2020"][0]
        assert "{" not in smith_paper["title"]
        assert "}" not in smith_paper["title"]
        assert "AI" in smith_paper["title"]

    def test_venue_dedup(self):
        bib = r"""
@article{a1,
  author = {Doe, Jane},
  title  = {Paper A},
  journal = {Nature},
  year   = {2020},
}

@article{a2,
  author = {Doe, Jane},
  title  = {Paper B},
  journal = {Nature},
  year   = {2021},
}
"""
        result = parse_bib_entries(bib)
        venue_names = [v["name"] for v in result["venues"]]
        assert venue_names.count("Nature") == 1

    def test_authors_list_on_paper(self):
        result = parse_bib_entries(_SINGLE_ARTICLE)
        paper = result["papers"][0]
        assert len(paper["authors"]) == 2
        assert paper["authors"][0]["normalized"] == "gordon, l"
        assert paper["authors"][1]["normalized"] == "loeb, m"


# ---------------------------------------------------------------------------
# Source extract header parsing
# ---------------------------------------------------------------------------

_FULL_SOURCE = """\
# The Economics of Information Security Investment

**Citation**: Lawrence A. Gordon and Martin P. Loeb, "The Economics of Information Security Investment," *ACM TISS*, 2002.
**DOI/URL**: https://doi.org/10.1145/581271.581274
**BibTeX Key**: gordon2002
**Access Level**: FULL-TEXT
**Source Type**: journal_article
**Deep-Read**: true
**Deep-Read Date**: 2026-03-28

## Content Snapshot
This paper proposes a model...
"""


class TestParseSourceHeaders:
    def test_full_header(self):
        result = parse_source_headers("gordon2002.md", _FULL_SOURCE)
        assert result["key"] == "gordon2002"
        assert result["title"] == "The Economics of Information Security Investment"
        assert result["access_level"] == "FULL-TEXT"
        assert result["source_type"] == "journal_article"
        assert result["deep_read"] is True
        assert result["doi"] == "https://doi.org/10.1145/581271.581274"
        assert "Gordon" in result["citation"]
        assert result["filename"] == "gordon2002.md"

    def test_missing_bibtex_key_falls_back_to_filename(self):
        content = "# Some Title\n\n**Access Level**: ABSTRACT-ONLY\n"
        result = parse_source_headers("smith2020.md", content)
        assert result["key"] == "smith2020"
        assert result["title"] == "Some Title"
        assert result["access_level"] == "ABSTRACT-ONLY"

    def test_no_header_fields(self):
        content = "# Just a Title\n\nSome body text.\n"
        result = parse_source_headers("orphan.md", content)
        assert result["title"] == "Just a Title"
        assert result["key"] == "orphan"
        assert result["access_level"] is None
        assert result["source_type"] is None
        assert result["deep_read"] is False
        assert result["doi"] is None
        assert result["citation"] is None

    def test_deep_read_false_string(self):
        content = "# Title\n\n**Deep-Read**: false\n"
        result = parse_source_headers("x.md", content)
        assert result["deep_read"] is False

    def test_deep_read_yes_string(self):
        content = "# Title\n\n**Deep-Read**: yes\n"
        result = parse_source_headers("x.md", content)
        assert result["deep_read"] is True

    def test_no_title_line(self):
        content = "No heading here.\n**BibTeX Key**: abc\n"
        result = parse_source_headers("abc.md", content)
        assert result["title"] is None
        assert result["key"] == "abc"

    def test_parse_all_source_headers(self, tmp_path):
        (tmp_path / "a.md").write_text(
            "# Paper A\n\n**BibTeX Key**: a1\n**Access Level**: FULL-TEXT\n"
        )
        (tmp_path / "b.md").write_text(
            "# Paper B\n\n**BibTeX Key**: b1\n**Access Level**: ABSTRACT-ONLY\n"
        )
        (tmp_path / "not_md.txt").write_text("ignored")
        results = parse_all_source_headers(str(tmp_path))
        assert len(results) == 2
        keys = {r["key"] for r in results}
        assert keys == {"a1", "b1"}


# ---------------------------------------------------------------------------
# Source body parser
# ---------------------------------------------------------------------------


class TestParseSourceBody:
    def test_cite_extraction(self):
        body = r"As shown by \cite{gordon2002} and \citet{dimaggio1983}."
        result = parse_source_body("smith2020", body, {"gordon2002", "dimaggio1983"})
        cites = [r for r in result["relationships"] if r["type"] == "CITES"]
        assert len(cites) == 2

    def test_multi_cite(self):
        body = r"Prior work \cite{a,b,c} established this."
        result = parse_source_body("x", body, {"a", "b", "c"})
        cites = [r for r in result["relationships"] if r["type"] == "CITES"]
        assert len(cites) == 3

    def test_unknown_keys_filtered(self):
        body = r"\cite{unknown_key}"
        result = parse_source_body("x", body, {"known_key"})
        assert len(result["relationships"]) == 0

    def test_theory_from_headings(self):
        body = "## Agency Theory\n\nText.\n\n## Institutional Isomorphism\n\nMore."
        result = parse_source_body("x", body, set())
        theories = [e for e in result["entities"] if e["type"] == "theory"]
        names = {t["name"] for t in theories}
        assert "Agency Theory" in names
        assert "Institutional Isomorphism" in names

    def test_generic_headings_skipped(self):
        body = "## Introduction\n\n## Methodology\n\n## Conclusion\n"
        result = parse_source_body("x", body, set())
        assert len(result["entities"]) == 0

    def test_method_extraction(self):
        body = "We used systematic review and meta-analysis."
        result = parse_source_body("x", body, set())
        methods = [e for e in result["entities"] if e["type"] == "method"]
        names = {m["name"].lower() for m in methods}
        assert "systematic review" in names
        assert "meta-analysis" in names

    def test_empty_body(self):
        result = parse_source_body("x", "", set())
        assert result == {"entities": [], "relationships": []}


# ---------------------------------------------------------------------------
# Graph merge and deduplication
# ---------------------------------------------------------------------------


class TestMergeEnrichmentIntoGraph:
    def test_adds_new_entity(self):
        import networkx as nx
        G = nx.Graph()
        entities = [{"name": "New Paper", "type": "paper", "description": "desc"}]
        stats = merge_enrichment_into_graph(G, entities, [])
        assert stats["entities_created"] == 1
        assert "NEW PAPER" in G.nodes

    def test_merges_existing(self):
        import networkx as nx
        G = nx.Graph()
        G.add_node("AGENCY THEORY", entity_type="concept", description="original")
        entities = [{"name": "Agency Theory", "type": "theory", "description": "enriched"}]
        stats = merge_enrichment_into_graph(G, entities, [])
        assert stats["entities_merged"] == 1
        assert "enriched" in G.nodes["AGENCY THEORY"]["description"]
        assert "original" in G.nodes["AGENCY THEORY"]["description"]

    def test_adds_relationship(self):
        import networkx as nx
        G = nx.Graph()
        G.add_node("A", entity_type="paper")
        G.add_node("B", entity_type="author")
        rels = [{"src": "a", "tgt": "b", "type": "AUTHORED_BY", "description": "by"}]
        stats = merge_enrichment_into_graph(G, [], rels)
        assert stats["relationships_created"] == 1
        assert G.has_edge("A", "B")

    def test_creates_missing_endpoints(self):
        import networkx as nx
        G = nx.Graph()
        rels = [{"src": "x", "tgt": "y", "type": "CITES", "description": "cites"}]
        stats = merge_enrichment_into_graph(G, [], rels)
        assert "X" in G.nodes
        assert "Y" in G.nodes

    def test_idempotent(self):
        import networkx as nx
        G = nx.Graph()
        entities = [{"name": "X", "type": "paper", "description": "desc"}]
        merge_enrichment_into_graph(G, entities, [])
        n1 = G.number_of_nodes()
        stats = merge_enrichment_into_graph(G, entities, [])
        assert G.number_of_nodes() == n1
        assert stats["entities_created"] == 0
