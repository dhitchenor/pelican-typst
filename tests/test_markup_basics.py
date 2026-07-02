"""Tests for the markdown-equivalent subset: headings, lists, code,
bold/italic, links, quotes, figures, images, tables."""


class TestHeadings:
    def test_levels(self, converter):
        out = converter.convert("= H1\n\n== H2\n\n=== H3")
        assert "<h1" in out and "H1</h1>" in out
        assert "<h2" in out and "H2</h2>" in out
        assert "<h3" in out and "H3</h3>" in out

    def test_gets_an_auto_id(self, converter):
        out = converter.convert("= Some Heading")
        assert 'id="section-1"' in out


class TestLists:
    def test_bullet_list(self, converter):
        out = converter.convert("- one\n- two\n- three")
        assert "<ul>" in out and out.count("<li>") == 3

    def test_numbered_list(self, converter):
        out = converter.convert("+ one\n+ two")
        assert "<ol>" in out and out.count("<li>") == 2


class TestCode:
    def test_fenced_block_with_language(self, converter):
        out = converter.convert("```python\nprint(1)\n```")
        assert '<pre><code class="language-python">print(1)</code></pre>' in out

    def test_inline_code(self, converter):
        out = converter.convert("Some `inline code` here.")
        assert "<code>inline code</code>" in out


class TestEmphasis:
    def test_bold_and_italic_shorthand(self, converter):
        out = converter.convert("A *bold* word and an _italic_ word.")
        assert "<strong>bold</strong>" in out
        assert "<em>italic</em>" in out

    def test_strong_and_emph_function_forms(self, converter):
        out = converter.convert("#strong[bold] and #emph[italic]")
        assert "<strong>bold</strong>" in out
        assert "<em>italic</em>" in out


class TestLinks:
    def test_basic_link(self, converter):
        out = converter.convert('#link("https://example.com")[Example]')
        assert '<a href="https://example.com">Example</a>' in out


class TestComments:
    def test_line_comment_is_stripped(self, converter):
        out = converter.convert("// a comment\n= Heading")
        assert "a comment" not in out
        assert "<h1" in out


class TestQuote:
    def test_bare_bracket_form(self, converter):
        out = converter.convert("#quote[Simplicity is the ultimate sophistication.]")
        assert "<blockquote>" in out
        assert "Simplicity is the ultimate sophistication." in out

    def test_with_attribution(self, converter):
        out = converter.convert(
            "#quote(attribution: [Einstein])[Imagination is more important.]"
        )
        assert "<footer>" in out
        assert "Einstein" in out


class TestFigureAndImage:
    def test_figure_with_caption(self, converter):
        out = converter.convert(
            '#figure(image("diagram.png"), caption: [An example diagram.])'
        )
        assert '<img src="diagram.png"' in out
        assert "<figcaption>An example diagram.</figcaption>" in out

    def test_figure_without_caption(self, converter):
        out = converter.convert('#figure(image("diagram.png"))')
        assert "<figure>" in out
        assert "<figcaption>" not in out

    def test_figure_wrapping_a_table(self, converter):
        out = converter.convert(
            '#figure(table(columns: 2, [A], [B]), caption: [A table])'
        )
        assert "<table>" in out
        assert "<figcaption>A table</figcaption>" in out

    def test_image_with_sizing_args(self, converter):
        out = converter.convert('#image("photo.jpg", width: 50%)')
        assert 'width="50%"' in out


class TestTable:
    def test_with_header(self, converter):
        out = converter.convert(
            "#table(columns: 2, table.header([A], [B]), [1], [2])"
        )
        assert "<thead>" in out and "<th>A</th>" in out and "<th>B</th>" in out
        assert "<tbody>" in out and "<td>1</td>" in out and "<td>2</td>" in out

    def test_without_header(self, converter):
        out = converter.convert("#table(columns: 2, [1], [2], [3], [4])")
        assert "<thead>" not in out
        assert out.count("<td>") == 4


class TestTermList:
    def test_basic(self, converter):
        out = converter.convert("/ Typst: A typesetting system.")
        assert "<dl>" in out
        assert "<dt>Typst</dt>" in out
        assert "<dd>A typesetting system.</dd>" in out
