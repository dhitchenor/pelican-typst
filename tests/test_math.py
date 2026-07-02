"""Tests for pelican.plugins.typst.math -- the Typst math tokenizer/
parser and MathML/LaTeX renderers. Assertions check the embedded LaTeX
annotation (see conftest.latex_of) since that's easier to assert on
precisely than raw MathML strings, while still exercising the same
shared AST both renderers consume."""

from conftest import latex_of, mathml_of


class TestBasics:
    def test_superscript_subscript(self):
        assert latex_of("x^2 + y^2 = z^2") == "x^{2} + y^{2} = z^{2}"

    def test_fraction_function(self):
        assert latex_of("frac(a+b, c)") == r"\frac{a + b}{c}"

    def test_fraction_shorthand(self):
        assert latex_of("a/b + c/d") == r"\frac{a}{b} + \frac{c}{d}"

    def test_sqrt(self):
        assert latex_of("sqrt(x^2+y^2)") == r"\sqrt{x^{2} + y^{2}}"

    def test_root(self):
        assert latex_of("root(3, x)") == r"\sqrt[3]{x}"

    def test_binom(self):
        assert latex_of("binom(n,k)") == r"\binom{n}{k}"

    def test_matrix(self):
        # & is correctly HTML-escaped to &amp; since this is checking the
        # LaTeX as embedded in the <annotation> tag, not raw LaTeX source.
        assert latex_of("mat(1, 2; 3, 4)") == \
            r"\begin{pmatrix}1 &amp; 2 \\ 3 &amp; 4\end{pmatrix}"

    def test_named_function(self):
        assert latex_of("sin(x) + cos(y)") == r"\sin(x) + \cos(y)"

    def test_arrow_shorthand(self):
        assert latex_of("x -> y") == r"x \rightarrow y"

    def test_sum_with_limits_uses_invisible_grouping(self):
        # `_(...)` right after ^/_ is invisible grouping like LaTeX's
        # {...}, not a literal rendered parenthesis.
        assert latex_of("sum_(i=1)^n i^2") == r"\sum_{i = 1}^{n} i^{2}"

    def test_lim_with_arrow(self):
        assert latex_of("lim_(x -> infinity) 1/x") == \
            r"\lim_{x \rightarrow \infty} \frac{1}{x}"


class TestPrimes:
    def test_triple_prime(self):
        assert latex_of("x'''") == "x'''"

    def test_prime_with_subscript(self):
        assert latex_of("x'_1") == "x'_{1}"

    def test_primes_not_silently_dropped(self):
        # Regression: the tokenizer originally didn't recognise ' at
        # all and silently discarded it.
        assert "'" in latex_of("f'(x)")


class TestAccents:
    def test_hat(self):
        assert latex_of("hat(x)") == r"\hat{x}"

    def test_tilde(self):
        assert latex_of("tilde(n)") == r"\tilde{n}"

    def test_vector_arrow(self):
        assert latex_of("arrow(v)") == r"\vec{v}"

    def test_double_dot(self):
        assert latex_of("ddot(x)") == r"\ddot{x}"

    def test_generic_accent_with_word_symbol(self):
        # Regression: "tilde" isn't in the greek/operator SYMBOLS table,
        # so the parser produces a "word" node, not a "sym" node -- the
        # accent() lookup must accept both.
        assert latex_of("accent(x, tilde)") == r"\tilde{x}"

    def test_generic_accent_defaults_to_hat_for_unknown(self):
        assert latex_of("accent(x, nonsense)") == r"\hat{x}"


class TestAlphabetStyles:
    def test_blackboard_bold_known_exceptions(self):
        # These specific letters live in the legacy Letterlike Symbols
        # Unicode block rather than the main Mathematical Alphanumeric
        # block -- verified against known real-world usage (naturals,
        # integers, rationals, reals, complex numbers). Checked at the
        # MathML level since that's where the actual character mapping
        # lives (the LaTeX side just emits \mathbb{R} regardless).
        cases = {"N": "\u2115", "Z": "\u2124", "Q": "\u211A",
                 "R": "\u211D", "C": "\u2102"}
        for letter, expected_char in cases.items():
            assert expected_char in mathml_of(f"bb({letter})")
            assert latex_of(f"bb({letter})") == r"\mathbb{" + letter + "}"

    def test_calligraphic(self):
        assert latex_of("cal(A)") == r"\mathcal{A}"

    def test_fraktur(self):
        assert latex_of("frak(g)") == r"\mathfrak{g}"

    def test_bold(self):
        assert latex_of("bold(x)") == r"\mathbf{x}"

    def test_italic(self):
        assert latex_of("italic(y)") == r"\mathit{y}"


class TestMiscFunctions:
    def test_cancel(self):
        assert latex_of("cancel(x + y)") == r"\cancel{x + y}"

    def test_class_ignores_class_name(self):
        assert latex_of('class("bin", x)') == "x"

    def test_lr_unwraps(self):
        assert "frac" in latex_of("lr((a)/(b))")

    def test_display_size_override(self):
        tex = latex_of("display(sum_(i=1)^n i)")
        assert tex.startswith(r"{\displaystyle")

    def test_stretch_passes_through(self):
        assert latex_of("stretch(->)") == r"\rightarrow"

    def test_overbrace_with_annotation(self):
        assert latex_of("overbrace(x+y+z, n)") == r"\overbrace{x + y + z}^{n}"

    def test_underbrace_with_annotation(self):
        assert latex_of("underbrace(a+b, 2)") == r"\underbrace{a + b}_{2}"


class TestRobustness:
    """Malformed input must never crash the build -- it should degrade
    to something reasonable instead."""

    def test_unbalanced_parens_does_not_raise(self):
        latex_of("frac(a, (b + c")  # no exception

    def test_unknown_function_does_not_raise(self):
        latex_of("frobnicate(x, y) + zorp^2")  # no exception

    def test_garbage_tokens_do_not_raise(self):
        latex_of("@@@ ### $$$")  # no exception
