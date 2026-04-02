"""Unit tests for the pure parsing functions in template/scripts/reviewer-kb.py."""

import importlib.util
from pathlib import Path

import pytest

# reviewer-kb.py has a hyphen so it cannot be imported normally.
_spec = importlib.util.spec_from_file_location(
    "reviewer_kb",
    Path(__file__).parent.parent / "template" / "scripts" / "reviewer-kb.py",
)
reviewer_kb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reviewer_kb)


# ── _split_table_row ─────────────────────────────────────────────────────


class TestSplitTableRow:
    def test_with_outer_pipes(self):
        assert reviewer_kb._split_table_row("| a | b | c |") == ["a", "b", "c"]

    def test_without_outer_pipes(self):
        assert reviewer_kb._split_table_row("a | b | c") == ["a", "b", "c"]

    def test_whitespace_stripped(self):
        result = reviewer_kb._split_table_row("|  foo  |  bar  |")
        assert result == ["foo", "bar"]

    def test_empty_cells(self):
        result = reviewer_kb._split_table_row("| | mid | |")
        assert result == ["", "mid", ""]

    def test_single_cell(self):
        assert reviewer_kb._split_table_row("| only |") == ["only"]


# ── _is_separator_row ────────────────────────────────────────────────────


class TestIsSeparatorRow:
    def test_standard_separator(self):
        assert reviewer_kb._is_separator_row("|---|---|---|") is True

    def test_separator_with_colons(self):
        assert reviewer_kb._is_separator_row("| :---: | ---: | :--- |") is True

    def test_separator_with_spaces(self):
        assert reviewer_kb._is_separator_row("|  ---  |  ---  |") is True

    def test_rejects_data_row(self):
        assert reviewer_kb._is_separator_row("| foo | bar |") is False

    def test_rejects_empty(self):
        assert reviewer_kb._is_separator_row("") is False

    def test_rejects_no_pipes(self):
        assert reviewer_kb._is_separator_row("--- ---") is False


# ── _expand_access ───────────────────────────────────────────────────────


class TestExpandAccess:
    def test_ft(self):
        assert reviewer_kb._expand_access("FT") == "Full-Text"

    def test_ao(self):
        assert reviewer_kb._expand_access("AO") == "Abstract-Only"

    def test_mo(self):
        assert reviewer_kb._expand_access("MO") == "Metadata-Only"

    def test_unknown_passthrough(self):
        assert reviewer_kb._expand_access("XX") == "XX"

    def test_lowercase_passthrough(self):
        assert reviewer_kb._expand_access("ft") == "ft"


# ── _slugify ─────────────────────────────────────────────────────────────


class TestSlugify:
    def test_basic(self):
        assert reviewer_kb._slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert reviewer_kb._slugify("Cost–Benefit: An Analysis!") == "cost-benefit-an-analysis"

    def test_strips_leading_trailing_hyphens(self):
        assert reviewer_kb._slugify("!!!test!!!") == "test"

    def test_truncates_at_60(self):
        long_title = "a" * 100
        assert len(reviewer_kb._slugify(long_title)) == 60

    def test_empty_string(self):
        assert reviewer_kb._slugify("") == ""


# ── parse_claims_matrix ──────────────────────────────────────────────────

FULL_CLAIMS_TABLE = """\
# Claims Matrix

| # | Tier | Claim | Evidence Sources | Warrant (Quality) | Qualifier | Rebuttal | Score | Strength | Section | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Core | First claim | smith2023(FT,direct)=0.9 jones2024(AO,tangential)=0.5 | Empirical warrant (High) | Domain-specific | Possible confound | 0.85 | Strong | Introduction, Methods | Active |
| C2 | Supporting | Second claim | lee2022(MO,direct)=0.3 | Theoretical justification (Medium) | Limited scope | No rebuttal | 0.6 | Moderate | Results | Pending |
"""


class TestParseClaimsMatrix:
    def test_full_table(self, tmp_project):
        p = tmp_project / "research" / "claims_matrix.md"
        p.write_text(FULL_CLAIMS_TABLE)

        claims = reviewer_kb.parse_claims_matrix(p)
        assert len(claims) == 2

        c1 = claims[0]
        assert c1.id == "C1"
        assert c1.tier == "Core"
        assert c1.statement == "First claim"
        assert len(c1.evidence) == 2
        assert c1.evidence[0].bibtex_key == "smith2023"
        assert c1.evidence[0].access_level == "FT"
        assert c1.evidence[0].directness == "direct"
        assert c1.evidence[0].score == 0.9
        assert c1.evidence[1].bibtex_key == "jones2024"
        assert c1.evidence[1].access_level == "AO"
        assert c1.evidence[1].directness == "tangential"
        assert c1.evidence[1].score == 0.5
        assert c1.warrant == "Empirical warrant"
        assert c1.warrant_quality == "High"
        assert c1.qualifier == "Domain-specific"
        assert c1.rebuttal == "Possible confound"
        assert c1.score == 0.85
        assert c1.strength == "Strong"
        assert c1.sections == ["Introduction", "Methods"]
        assert c1.status == "Active"

        c2 = claims[1]
        assert c2.id == "C2"
        assert c2.tier == "Supporting"
        assert len(c2.evidence) == 1
        assert c2.evidence[0].bibtex_key == "lee2022"
        assert c2.evidence[0].access_level == "MO"
        assert c2.warrant_quality == "Medium"
        assert c2.score == 0.6
        assert c2.sections == ["Results"]

    def test_empty_file(self, tmp_project):
        p = tmp_project / "research" / "claims_matrix.md"
        p.write_text("")
        assert reviewer_kb.parse_claims_matrix(p) == []

    def test_malformed_row_skipped(self, tmp_project):
        """Rows without a C-prefixed id are silently skipped."""
        table = """\
| # | Tier | Claim | Evidence Sources | Warrant (Quality) | Qualifier | Rebuttal | Score | Strength | Section | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| X1 | Core | Bad id | none | w (Low) | q | r | 0.1 | Weak | Intro | Draft |
| C3 | Core | Good id | ref(FT,direct)=0.7 | w (High) | q | r | 0.7 | Strong | Intro | Active |
"""
        p = tmp_project / "research" / "claims_matrix.md"
        p.write_text(table)
        claims = reviewer_kb.parse_claims_matrix(p)
        assert len(claims) == 1
        assert claims[0].id == "C3"

    def test_no_evidence(self, tmp_project):
        """A claim row with no parseable evidence produces an empty list."""
        table = """\
| # | Tier | Claim | Evidence Sources | Warrant (Quality) | Qualifier | Rebuttal | Score | Strength | Section | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| C4 | Core | Claim no evidence | none | warrant (Low) | q | r | 0.0 | Weak | Intro | Draft |
"""
        p = tmp_project / "research" / "claims_matrix.md"
        p.write_text(table)
        claims = reviewer_kb.parse_claims_matrix(p)
        assert len(claims) == 1
        assert claims[0].evidence == []


# ── parse_assumptions ────────────────────────────────────────────────────

FULL_ASSUMPTIONS = """\
# Assumptions

### MA-1: Independence assumption
**Statement.** Variables are independent.
**Category.** CRITICAL
**Justification.** Standard in prior work.
**Consequence if violated.** Biased estimates.
**Mitigation.** Sensitivity analysis.
**Prior art.** Smith et al. (2020) used same assumption.

### MA-2: Linearity
**Statement.** Relationship is approximately linear
over the observed range.
**Category.** REASONABLE
**Justification.** Scatter plots suggest linearity.
**Consequence if violated.** Poor fit.
**Mitigation.** Use polynomial terms.
**Prior art.** Jones (2019).
"""


class TestParseAssumptions:
    def test_full_document(self, tmp_project):
        p = tmp_project / "research" / "assumptions.md"
        p.write_text(FULL_ASSUMPTIONS)

        assumptions = reviewer_kb.parse_assumptions(p)
        assert len(assumptions) == 2

        a1 = assumptions[0]
        assert a1.id == "MA-1"
        assert a1.title == "Independence assumption"
        assert a1.category == "CRITICAL"
        assert a1.statement == "Variables are independent."
        assert a1.justification == "Standard in prior work."
        assert a1.consequence == "Biased estimates."
        assert a1.mitigation == "Sensitivity analysis."
        assert a1.prior_art == "Smith et al. (2020) used same assumption."

        a2 = assumptions[1]
        assert a2.id == "MA-2"
        assert a2.title == "Linearity"
        assert a2.category == "REASONABLE"

    def test_continuation_lines(self, tmp_project):
        """Continuation line after Statement appends to statement."""
        p = tmp_project / "research" / "assumptions.md"
        p.write_text(FULL_ASSUMPTIONS)

        assumptions = reviewer_kb.parse_assumptions(p)
        a2 = assumptions[1]
        assert "approximately linear" in a2.statement
        assert "over the observed range." in a2.statement

    def test_empty_file(self, tmp_project):
        p = tmp_project / "research" / "assumptions.md"
        p.write_text("")
        assert reviewer_kb.parse_assumptions(p) == []

    def test_missing_category_defaults_empty(self, tmp_project):
        """If no **Category.** field is present, category defaults to ''."""
        text = """\
### TA-1: No category given
**Statement.** Some statement.
**Justification.** Some justification.
"""
        p = tmp_project / "research" / "assumptions.md"
        p.write_text(text)
        assumptions = reviewer_kb.parse_assumptions(p)
        assert len(assumptions) == 1
        assert assumptions[0].category == ""
        assert assumptions[0].statement == "Some statement."


# ── decompose_methodology_notes ──────────────────────────────────────────

METHODOLOGY_NOTES = """\
# Methodology Notes

## Data Collection
We collected data from three sources.
Details follow.

## Analysis Pipeline
The pipeline has four stages.

### Stage 1
First stage detail.

## Validation
Cross-validation was performed.
"""


class TestDecomposeMethodologyNotes:
    def test_multi_section(self, tmp_project):
        p = tmp_project / "research" / "methodology-notes.md"
        p.write_text(METHODOLOGY_NOTES)

        sections = reviewer_kb.decompose_methodology_notes(p)
        assert len(sections) == 3

        slug0, content0 = sections[0]
        assert slug0 == "data-collection"
        assert "We collected data" in content0
        assert "Details follow." in content0

        slug1, content1 = sections[1]
        assert slug1 == "analysis-pipeline"
        assert "four stages" in content1
        # ### subsections are included in the parent ## section
        assert "Stage 1" in content1

        slug2, content2 = sections[2]
        assert slug2 == "validation"
        assert "Cross-validation" in content2

    def test_empty_file(self, tmp_project):
        p = tmp_project / "research" / "methodology-notes.md"
        p.write_text("")
        assert reviewer_kb.decompose_methodology_notes(p) == []

    def test_single_section(self, tmp_project):
        text = """\
## Only Section
Content here.
More content.
"""
        p = tmp_project / "research" / "methodology-notes.md"
        p.write_text(text)
        sections = reviewer_kb.decompose_methodology_notes(p)
        assert len(sections) == 1
        assert sections[0][0] == "only-section"
        assert "Content here." in sections[0][1]

    def test_no_h2_sections(self, tmp_project):
        """A file with only # or ### headings produces no sections."""
        text = """\
# Top-level only
Some text.

### Sub only
More text.
"""
        p = tmp_project / "research" / "methodology-notes.md"
        p.write_text(text)
        assert reviewer_kb.decompose_methodology_notes(p) == []
