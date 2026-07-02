"""Tests for #let literal bindings, #lorem(), and a regression test for
a real bug found during development: an unresolved #name reference
containing '_' getting corrupted by the later italic-shorthand pass."""


class TestLetBindings:
    def test_string_binding_substituted(self, converter):
        out = converter.convert('#let version = "1.2.3"\n\nCurrent: #version.')
        assert "Current: 1.2.3." in out

    def test_number_and_bool_bindings(self, converter):
        out = converter.convert(
            "#let year = 2026\n#let draft = false\n\n#year and #draft."
        )
        assert "2026 and false." in out

    def test_multiple_references_all_resolve(self, converter):
        out = converter.convert('#let name = "X"\n\nHi #name, bye #name.')
        assert out.count("X") == 2

    def test_binding_line_itself_never_renders(self, converter):
        out = converter.convert('#let x = "value"\n\nUse: #x.')
        assert "#let" not in out

    def test_function_definition_line_stripped_but_not_evaluated(self, converter):
        out = converter.convert(
            '#let f(x) = "Item: " + x\n\nAfter the definition.'
        )
        assert "#let" not in out
        assert "After the definition." in out

    def test_forward_reference_stays_unresolved(self, converter):
        # Real Typst evaluates #let strictly top-to-bottom -- a genuine
        # forward reference is undefined there too, so staying broken
        # here is correct behaviour, not a limitation.
        out = converter.convert('Value: #x.\n\n#let x = "too late"')
        assert "#x" in out

    def test_unrelated_stray_hash_word_is_left_alone(self, converter):
        out = converter.convert("Just a stray #hashtag mention.")
        assert "#hashtag" in out

    def test_unresolved_reference_with_underscore_not_corrupted_by_italics(self, converter):
        # Regression: an unresolved #name reference was being returned
        # as raw editable text, so the LATER *и*/_.._ italic-shorthand
        # pass could still match the underscores inside it, turning
        # "#totally_undefined_name" into "#totally<em>undefined</em>name".
        # Real Typst variable names commonly use snake_case, so this was
        # a real bug, not just a contrived edge case.
        out = converter.convert("See #totally_undefined_name here.")
        assert "#totally_undefined_name" in out
        assert "<em>" not in out


class TestLorem:
    def test_word_count_and_capitalization(self, converter):
        out = converter.convert("#lorem(5)")
        # "<p>Word1 word2 word3 word4 word5.</p>"
        words = out.replace("<p>", "").replace("</p>", "").rstrip(".").split()
        assert len(words) == 5
        assert words[0][0].isupper()

    def test_zero_words_produces_empty_output(self, converter):
        out = converter.convert("#lorem(0)")
        assert "<p></p>" == out
