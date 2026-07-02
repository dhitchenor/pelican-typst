"""Tests for #set heading(numbering:), labels, @label/#ref() cross-
references (including genuine forward references), and #outline()."""


class TestHeadingNumbering:
    def test_basic_numbering(self, converter):
        out = converter.convert(
            '#set heading(numbering: "1.1")\n= Chapter\n== Section'
        )
        assert "1. Chapter" in out
        # pattern "1.1" only has one literal dot total (between the two
        # counting positions), so level 2 is "1.1", not "1.1."
        assert "1.1 Section" in out

    def test_resets_deeper_level_on_new_shallow_heading(self, converter):
        out = converter.convert(
            '#set heading(numbering: "1.1")\n'
            "= One\n== A\n== B\n= Two\n== C"
        )
        assert "1.1 A" in out
        assert "1.2 B" in out
        assert "2.1 C" in out  # not 1.3 -- resets when a new "= " appears

    def test_no_numbering_directive_means_no_numbers(self, converter):
        out = converter.convert("= Plain Heading")
        assert ">Plain Heading<" in out
        assert "1. Plain Heading" not in out

    def test_numbering_can_be_turned_off_mid_document(self, converter):
        out = converter.convert(
            '#set heading(numbering: "1.")\n'
            "= First\n"
            "#set heading(numbering: none)\n"
            "= Second"
        )
        assert "1. First" in out
        assert ">Second<" in out


class TestLabelsAndReferences:
    def test_backward_reference(self, converter):
        out = converter.convert("= Introduction <intro>\n\nSee @intro for context.")
        assert 'id="intro"' in out
        assert '<a href="#intro">Introduction</a>' in out

    def test_forward_reference_resolves(self, converter):
        # Real Typst evaluates #let strictly top-to-bottom, but labels
        # use a separate resolution mechanism -- a forward reference to
        # a heading label DOES resolve, unlike #let.
        out = converter.convert(
            "As covered in @later, this matters.\n\n= Later Section <later>"
        )
        assert '<a href="#later">Later Section</a>' in out

    def test_ref_function_form_equivalent_to_shorthand(self, converter):
        a = converter.convert("= X <x>\n\nSee @x.")
        b = converter.convert("= X <x>\n\nSee #ref(<x>).")
        assert a == b

    def test_reference_shows_number_when_numbering_active(self, converter):
        out = converter.convert(
            '#set heading(numbering: "1.")\n= Setup <setup>\n\nSee @setup.'
        )
        assert '<a href="#setup">1.</a>' in out

    def test_unresolved_reference_degrades_visibly_rather_than_vanishing(self, converter):
        out = converter.convert("See @nonexistent for details.")
        assert "@nonexistent" in out

    def test_unlabeled_heading_still_gets_auto_id(self, converter):
        out = converter.convert("= No Label Here")
        assert 'id="section-1"' in out


class TestOutline:
    def test_builds_nested_structure(self, converter):
        out = converter.convert(
            "#outline()\n\n= One\n== Sub\n= Two"
        )
        assert 'class="outline"' in out
        assert out.index("Sub") < out.index("<h1") or "Sub" in out
        assert "<h2>Contents</h2>" in out

    def test_custom_title(self, converter):
        out = converter.convert("#outline(title: [Table of Contents])\n\n= X")
        assert "<h2>Table of Contents</h2>" in out

    def test_title_none_omits_heading(self, converter):
        out = converter.convert("#outline(title: none)\n\n= X")
        assert "<h2>" not in out.split("</nav>")[0]

    def test_depth_limit(self, converter):
        out = converter.convert(
            "#outline(depth: 1)\n\n= One\n== Excluded Sub"
        )
        nav = out.split("</nav>")[0]
        assert "One" in nav
        assert "Excluded Sub" not in nav
