"""Tests for text-level styling (highlight/strike/underline/sub/super/
upper/lower/text()/raw()/linebreaks/smart quotes) and footnotes."""


class TestSimpleWraps:
    def test_highlight(self, converter):
        assert "<mark>hi</mark>" in converter.convert("#highlight[hi]")

    def test_strike(self, converter):
        assert "<s>gone</s>" in converter.convert("#strike[gone]")

    def test_underline(self, converter):
        assert "<u>line</u>" in converter.convert("#underline[line]")

    def test_sub_and_super(self, converter):
        out = converter.convert("H#sub[2]O and E=mc#super[2]")
        assert "<sub>2</sub>" in out
        assert "<sup>2</sup>" in out


class TestCaseTransform:
    def test_upper_and_lower(self, converter):
        out = converter.convert("#upper[shout] but not #lower[WHISPER]")
        assert "SHOUT" in out
        assert "whisper" in out

    def test_upper_does_not_corrupt_sibling_markup(self, converter):
        # Regression: upper()/lower() must NOT recursively process
        # their content, or uppercasing e.g. a <strong> tag's letters
        # would mangle the tag itself.
        out = converter.convert("#upper[shout] but *bold* stays intact")
        assert "<strong>bold</strong>" in out


class TestTextStyle:
    def test_color_and_weight(self, converter):
        out = converter.convert('#text(fill: red, weight: "bold")[styled]')
        assert "color: red" in out
        assert "font-weight: bold" in out

    def test_rgb_hex_color(self, converter):
        out = converter.convert('#text(fill: rgb("#0077cc"))[blue]')
        assert "#0077cc" in out


class TestRaw:
    def test_inline(self, converter):
        out = converter.convert('#raw("print(1)", lang: "python")')
        assert '<code class="language-python">print(1)</code>' in out

    def test_block(self, converter):
        out = converter.convert('#raw("fn main() {}", lang: "rust", block: true)')
        assert '<pre><code class="language-rust">fn main() {}</code></pre>' in out

    def test_arguments_in_any_order(self, converter):
        a = converter.convert('#raw(lang: "python", "print(1)")')
        b = converter.convert('#raw("print(1)", lang: "python")')
        assert a == b


class TestLinebreaks:
    def test_function_form(self, converter):
        assert "<br>" in converter.convert("line#linebreak()break")

    def test_backslash_shorthand(self, converter):
        out = converter.convert("first line\\\nsecond line")
        assert "<br>" in out


class TestSmartQuotes:
    def test_opening_and_closing_double_quotes(self, converter):
        out = converter.convert('"Hello," she said.')
        assert "\u201cHello,\u201d" in out

    def test_apostrophe_not_treated_as_opening_quote(self, converter):
        out = converter.convert("don't")
        assert "don\u2019t" in out
        assert "don\u2018t" not in out


class TestFootnotes:
    def test_basic(self, converter):
        out = converter.convert("Sentence.#footnote[A note.]")
        assert '<sup id="fnref1"' in out
        assert '<li id="fn1">A note.' in out
        assert 'class="footnotes"' in out

    def test_sequential_numbering(self, converter):
        out = converter.convert(
            "One.#footnote[First.] Two.#footnote[Second.]"
        )
        assert '<a href="#fn1">1</a>' in out
        assert '<a href="#fn2">2</a>' in out

    def test_content_gets_full_inline_processing(self, converter):
        out = converter.convert(
            'Text.#footnote[See #link("https://x.com")[here] and *bold*.]'
        )
        assert '<a href="https://x.com">here</a>' in out
        assert "<strong>bold</strong>" in out

    def test_math_inside_footnote(self, converter):
        out = converter.convert("Text.#footnote[Math: $x^2$.]")
        assert "typst-math" in out
