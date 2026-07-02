"""Tests for #grid/#stack and the 14 layout functions (align/block/box/
pad/move/place/rotate/scale/skew/columns/hide/repeat/h/v)."""


class TestGridAndStack:
    def test_grid_basic(self, converter):
        out = converter.convert("#grid(columns: 2, [A], [B], [C], [D])")
        assert "display:grid" in out
        assert "grid-template-columns: repeat(2, 1fr)" in out
        assert out.count("<div>") >= 4

    def test_grid_gutter(self, converter):
        out = converter.convert("#grid(columns: 2, gutter: 1em, [A], [B])")
        assert "gap: 1em" in out

    def test_stack_default_direction_is_column(self, converter):
        out = converter.convert("#stack([A], [B])")
        assert "flex-direction:column" in out

    def test_stack_horizontal(self, converter):
        out = converter.convert("#stack(dir: ltr, [A], [B])")
        assert "flex-direction:row" in out


class TestAlign:
    def test_center(self, converter):
        out = converter.convert("#align(center)[Centered]")
        assert "text-align: center" in out


class TestBlockAndBox:
    def test_block_styling(self, converter):
        out = converter.convert("#block(fill: red, inset: 1cm, radius: 5pt)[X]")
        assert "background-color: red" in out
        assert "padding: 1cm" in out
        assert "border-radius: 5pt" in out

    def test_box_is_inline(self, converter):
        out = converter.convert("#box(fill: blue)[X]")
        assert "display:inline-block" in out
        assert "background-color: blue" in out


class TestPad:
    def test_single_value_pads_all_sides(self, converter):
        out = converter.convert("#pad(1cm)[X]")
        assert "padding: 1cm;" in out

    def test_directional(self, converter):
        out = converter.convert("#pad(left: 1cm, top: 2cm)[X]")
        assert "padding-left: 1cm" in out
        assert "padding-top: 2cm" in out


class TestTransforms:
    def test_rotate(self, converter):
        assert "transform: rotate(45deg)" in converter.convert("#rotate(45deg)[X]")

    def test_scale_percent_converts_to_unitless_factor(self, converter):
        # CSS transform:scale() takes a bare multiplier, not a percentage.
        out = converter.convert("#scale(150%)[X]")
        assert "transform: scale(1.5)" in out

    def test_skew(self, converter):
        out = converter.convert("#skew(ax: 10deg)[X]")
        assert "transform: skew(10deg, 0deg)" in out

    def test_move(self, converter):
        out = converter.convert("#move(dx: 1cm, dy: 2cm)[X]")
        assert "left:1cm" in out and "top:2cm" in out


class TestColumnsHideRepeat:
    def test_columns(self, converter):
        assert "column-count: 2" in converter.convert("#columns(2)[X]")

    def test_hide_uses_visibility_not_display_none(self, converter):
        # Typst's hide() reserves layout space -- visibility:hidden
        # matches that; display:none would not.
        out = converter.convert("#hide[invisible]")
        assert "visibility:hidden" in out
        assert "display:none" not in out

    def test_repeat_renders_content_once(self, converter):
        # No real layout engine to know "available space" to fill, so
        # content renders once rather than vanishing or erroring.
        assert converter.convert("#repeat[.]") == "<p>.</p>"


class TestSpacers:
    def test_h_fixed_length(self, converter):
        out = converter.convert("Before#h(1cm)After")
        assert 'width:1cm' in out

    def test_h_fraction_unit_drops_silently(self, converter):
        # 1fr means "fill remaining space" -- no equivalent in normal
        # text flow, so it's dropped rather than shown as broken syntax.
        out = converter.convert("Before#h(1fr)After")
        assert "#h(" not in out
        assert "BeforeAfter" in out

    def test_v_is_block_level(self, converter):
        out = converter.convert("Above\n\n#v(2cm)\n\nBelow")
        assert '<div style="height:2cm;"></div>' in out
