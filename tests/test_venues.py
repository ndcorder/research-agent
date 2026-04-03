"""Validate venue configuration files: required fields, content quality, consistency."""

import json
from pathlib import Path

VENUES_DIR = Path(__file__).parent.parent / "template" / "venues"

REQUIRED_FIELDS = {"name", "documentclass", "packages", "citation_style", "writing_guide"}

KNOWN_CITATION_STYLES = {
    "natbib", "biblatex", "numeric", "numeric-superscript", "apa",
    "author-year", "ieee", "chicago",
}


def _venue_files():
    """Return all .json files in the venues directory."""
    return sorted(VENUES_DIR.glob("*.json"))


def _load_venue(path):
    """Load and return a venue JSON dict."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------


class TestRequiredFields:
    """Every venue must have the required fields."""

    def test_all_venues_have_required_fields(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            for field in REQUIRED_FIELDS:
                assert field in data, (
                    f"{vf.name} missing required field: {field}"
                )

    def test_packages_is_list_of_strings(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            pkgs = data["packages"]
            assert isinstance(pkgs, list), (
                f"{vf.name}: 'packages' should be a list, got {type(pkgs).__name__}"
            )
            for i, p in enumerate(pkgs):
                assert isinstance(p, str), (
                    f"{vf.name}: packages[{i}] should be str, got {type(p).__name__}"
                )

    def test_documentclass_is_string(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            assert isinstance(data["documentclass"], str), (
                f"{vf.name}: 'documentclass' should be a string"
            )

    def test_citation_style_is_string(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            assert isinstance(data["citation_style"], str), (
                f"{vf.name}: 'citation_style' should be a string"
            )


# ---------------------------------------------------------------------------
# Writing guide quality
# ---------------------------------------------------------------------------


class TestWritingGuide:
    """writing_guide should be substantial (>100 words)."""

    def test_writing_guide_is_substantial(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            guide = data["writing_guide"]
            assert isinstance(guide, str), (
                f"{vf.name}: 'writing_guide' should be a string"
            )
            word_count = len(guide.split())
            assert word_count > 100, (
                f"{vf.name}: writing_guide has only {word_count} words (need >100)"
            )


# ---------------------------------------------------------------------------
# Citation style
# ---------------------------------------------------------------------------


class TestCitationStyle:
    """citation_style should be one of the known values."""

    def test_citation_style_is_known(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            style = data["citation_style"]
            assert style in KNOWN_CITATION_STYLES, (
                f"{vf.name}: citation_style '{style}' not in known styles: "
                f"{sorted(KNOWN_CITATION_STYLES)}"
            )


# ---------------------------------------------------------------------------
# Forbidden packages vs packages
# ---------------------------------------------------------------------------


class TestForbiddenPackages:
    """forbidden_packages (if present) must not overlap with packages."""

    def _extract_package_name(self, usepackage_line):
        """Extract the package name from a \\usepackage line."""
        import re
        # Match \usepackage[...]{name} or \usepackage{name} or \usepackage{a,b,c}
        m = re.search(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}", usepackage_line)
        if m:
            # May be comma-separated: "amsmath,amssymb,amsthm"
            return {n.strip() for n in m.group(1).split(",")}
        return set()

    def test_no_overlap(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            forbidden = data.get("forbidden_packages", [])
            if not forbidden:
                continue
            assert isinstance(forbidden, list), (
                f"{vf.name}: 'forbidden_packages' should be a list"
            )
            # Collect all package names from the packages list
            pkg_names = set()
            for pkg_line in data.get("packages", []):
                pkg_names.update(self._extract_package_name(pkg_line))
            # Collect forbidden package names (these are plain strings)
            forbidden_names = set(forbidden)
            overlap = pkg_names & forbidden_names
            assert not overlap, (
                f"{vf.name}: packages overlap with forbidden_packages: {overlap}"
            )

    def test_forbidden_packages_is_list(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            if "forbidden_packages" in data:
                assert isinstance(data["forbidden_packages"], list), (
                    f"{vf.name}: 'forbidden_packages' should be a list"
                )

    def test_preamble_extra_is_list(self):
        for vf in _venue_files():
            data = _load_venue(vf)
            if "preamble_extra" in data:
                assert isinstance(data["preamble_extra"], list), (
                    f"{vf.name}: 'preamble_extra' should be a list"
                )


# ---------------------------------------------------------------------------
# Valid JSON (redundant with test_structure.sh, but good for pytest coverage)
# ---------------------------------------------------------------------------


class TestValidJSON:
    """All venue files should be valid JSON."""

    def test_all_valid_json(self):
        for vf in _venue_files():
            try:
                _load_venue(vf)
            except json.JSONDecodeError as e:
                raise AssertionError(f"{vf.name}: invalid JSON: {e}")
