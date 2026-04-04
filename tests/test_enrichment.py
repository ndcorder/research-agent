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
