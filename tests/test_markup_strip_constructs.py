"""Tests for constructs that are recognised and cleanly stripped rather
than leaking as broken text (#set/#import/#bibliography/#cite/
#pagebreak/#colbreak), plus a regression test for a real regex-
backtracking bug found during development."""


class TestGenericSetStripping:
    def test_non_heading_set_rules_produce_no_output(self, converter):
        out = converter.convert(
            '#set text(size: 11pt)\n#set par(justify: true)\n\nReal content.'
        )
        assert "#set" not in out
        assert "<p>Real content.</p>" == out

    def test_multiline_set_page_stripped_cleanly(self, converter):
        out = converter.convert(
            "#set page(\n  width: 21cm,\n  margin: (x: 2cm),\n)\n\n= Heading"
        )
        assert "#set" not in out
        assert "21cm" not in out
        assert "<h1" in out

    def test_heading_numbering_set_rule_still_works(self, converter):
        # The one #set rule with real semantic effect here -- must not
        # be swept up by the generic "#set -> strip" handling.
        out = converter.convert('#set heading(numbering: "1.")\n= X')
        assert "1. X" in out


class TestImportAndBibliography:
    def test_import_produces_no_output(self, converter):
        out = converter.convert('#import "template.typ": *\n\nReal content.')
        assert "#import" not in out
        assert "<p>Real content.</p>" == out

    def test_bibliography_call_produces_no_output(self, converter):
        out = converter.convert('Before.\n\n#bibliography("refs.bib")\n\nAfter.')
        assert "#bibliography" not in out
        assert "<p>Before.</p>" in out
        assert "<p>After.</p>" in out

    def test_cite_stripped_inline(self, converter):
        out = converter.convert("Claim #cite(<smith2020>) here.")
        assert "#cite" not in out
        assert "smith2020" not in out


class TestPagebreakAndColbreak:
    def test_pagebreak_vanishes_with_no_empty_paragraph(self, converter):
        out = converter.convert("Before.\n\n#pagebreak()\n\nAfter.")
        assert "<p></p>" not in out
        assert "<p>Before.</p>" in out
        assert "<p>After.</p>" in out

    def test_colbreak_vanishes(self, converter):
        out = converter.convert("Before.\n\n#colbreak()\n\nAfter.")
        assert "<p></p>" not in out


class TestMetadataCallInsideCodeSpanRegression:
    def test_hash_ref_regex_does_not_truncate_function_calls_in_code(self, converter):
        # Regression: the bare-#name-reference regex used a greedy
        # \w* with a negative lookahead for '(' -- Python's regex engine
        # would backtrack the greedy match to a SHORTER substring that
        # happened to satisfy the lookahead, matching "#metadat" out of
        # "#metadata()" instead of correctly not matching at all. That
        # left an unrestored stash placeholder (a literal null byte) in
        # the output, which broke RSS/Atom feed generation downstream
        # (real error hit during manual testing: "Control characters
        # are not supported in XML 1.0"). Fixed with a word-boundary
        # anchor before the lookahead; this pins that fix in place.
        out = converter.convert("but uses `#metadata()` instead of YAML.")
        assert "\x00" not in out
        assert "<code>#metadata()</code>" in out
