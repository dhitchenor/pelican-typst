"""Tests for pelican.plugins.typst.markup.numbering -- the formatter
that backs both #numbering() and #set heading(numbering:)."""

from pelican.plugins.typst.markup.numbering import _apply_numbering


class TestArabic:
    def test_basic(self):
        assert _apply_numbering("1.", [1]) == "1."
        assert _apply_numbering("1.", [2]) == "2."


class TestAlpha:
    def test_basic(self):
        assert _apply_numbering("a", [1]) == "a"
        assert _apply_numbering("a", [3]) == "c"

    def test_rollover_past_z(self):
        assert _apply_numbering("a", [26]) == "z"
        assert _apply_numbering("a", [27]) == "aa"
        assert _apply_numbering("a", [28]) == "ab"

    def test_uppercase(self):
        assert _apply_numbering("A", [1]) == "A"
        assert _apply_numbering("A", [26]) == "Z"


class TestRoman:
    def test_small_values(self):
        assert _apply_numbering("I", [1]) == "I"
        assert _apply_numbering("I", [4]) == "IV"
        assert _apply_numbering("I", [9]) == "IX"

    def test_large_value(self):
        # 2000 + 20 + 6
        assert _apply_numbering("I", [2026]) == "MMXXVI"

    def test_lowercase(self):
        assert _apply_numbering("i", [4]) == "iv"


class TestStar:
    def test_cycles_then_doubles(self):
        assert _apply_numbering("*", [1]) == "*"
        assert _apply_numbering("*", [2]) == "\u2020"
        # 7th item: cycle of 6 symbols wraps back to the first, doubled
        assert _apply_numbering("*", [7]) == "**"


class TestMultiLevelPatterns:
    def test_uses_only_as_many_groups_as_numbers_given(self):
        # One number given -> format that number (2) with the first
        # group's symbol -> "2.", not "1." (a single number never means
        # "always show 1").
        assert _apply_numbering("1.1.1", [2]) == "2."
        assert _apply_numbering("1.1.1", [2, 3]) == "2.3."

    def test_last_group_repeats_when_more_numbers_than_groups(self):
        # Pattern has 2 groups ("1." and "1"); with 4 numbers the last
        # group (empty trailing literal) repeats for numbers 3 and 4.
        assert _apply_numbering("1.1", [1, 2, 3, 4]) == "1.234"

    def test_mixed_symbol_types(self):
        assert _apply_numbering("A.I.", [1]) == "A."
        assert _apply_numbering("A.I.", [1, 2]) == "A.II."
