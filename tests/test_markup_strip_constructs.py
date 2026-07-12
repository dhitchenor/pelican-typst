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

    def test_bibliography_file_path_call_produces_no_output(self, converter):
        # A real Typst file-path call, e.g. #bibliography("refs.bib") --
        # not something we can resolve/parse (that's the later BibTeX
        # import work), so it's silently consumed same as before,
        # rather than leaking broken text.
        out = converter.convert('Before.\n\n#bibliography("refs.bib")\n\nAfter.')
        assert "#bibliography" not in out
        assert "<p>Before.</p>" in out
        assert "<p>After.</p>" in out


class TestInlineBibliography:
    """#bibliography((key: "entry", ...)) -- our own inline-dict
    stepping stone ahead of real BibTeX/Hayagriva file support: authors
    hand-write entries directly in the .typ file, #cite(<key>) links to
    them, and a References section renders at the end listing only
    what was actually cited, in citation order."""

    def test_cite_renders_numbered_link_not_stripped(self, converter):
        out = converter.convert(
            'Claim #cite(<smith2020>) here.\n\n'
            '#bibliography((smith2020: "Smith, J. (2020). A Paper."))'
        )
        assert "[1]" in out
        assert 'href="#cite-1"' in out
        assert "#cite(" not in out

    def test_references_section_lists_only_cited_entries(self, converter):
        out = converter.convert(
            "Only this one is cited #cite(<used>).\n\n"
            '#bibliography((\n'
            '  used: "Used Entry.",\n'
            '  unused: "Never Cited Entry.",\n'
            "))"
        )
        assert "Used Entry." in out
        assert "Never Cited Entry." not in out
        assert '<h2>References</h2>' in out

    def test_citation_order_not_bibliography_order_determines_numbering(self, converter):
        # bib dict lists "b" first, but "a" is cited first in the body
        # -- numbering must follow citation order, not dict order.
        out = converter.convert(
            "First #cite(<a>), then #cite(<b>).\n\n"
            '#bibliography((\n'
            '  b: "Entry B.",\n'
            '  a: "Entry A.",\n'
            "))"
        )
        assert out.index("[1]") < out.index("[2]")
        assert out.index('id="cite-1"') < out.index('id="cite-2"')
        assert "Entry A." in out.split('id="cite-1"')[1].split("</li>")[0]

    def test_same_key_cited_twice_reuses_number_no_duplicate_id(self, converter):
        out = converter.convert(
            "Cited once #cite(<x>), cited again #cite(<x>).\n\n"
            '#bibliography((x: "Entry X."))'
        )
        assert out.count("[1]") == 2
        assert out.count('id="cite-ref-1"') == 1  # only first occurrence
        assert out.count('id="cite-1"') == 1  # exactly one reference entry

    def test_unresolved_citation_key_gets_graceful_fallback(self, converter):
        # No matching #bibliography entry at all -- must not crash or
        # silently vanish; shows the reader something diagnosable.
        out = converter.convert("Dangling claim #cite(<missing>).")
        assert "[1]" in out
        assert "missing" in out

    def test_no_citations_means_no_references_section(self, converter):
        out = converter.convert(
            'Nothing cited here.\n\n#bibliography((x: "Entry X."))'
        )
        assert "References" not in out
        assert "Entry X." not in out


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
