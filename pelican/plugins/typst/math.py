"""
Typst math -> (MathML, LaTeX) conversion.

This is a best-effort recursive-descent parser for a useful subset of
Typst's math syntax. It is NOT a full Typst math implementation -- Typst's
math mode is large, and this covers the constructs people actually use
day to day: symbols/greek letters, sub/superscripts, fractions (both
`frac(a,b)` and `a/b`), roots, vectors/matrices, binomials, abs/norm/floor/
ceil, big operators with limits, and common named functions (sin, lim, ...).

Anything unrecognised is passed through as an upright identifier/word
rather than crashing the build, so uncommon notation degrades gracefully
instead of breaking the page.

Public entry point: `convert_math(src, display) -> str` (HTML snippet).
"""

import html
import re

# ---------------------------------------------------------------------------
# Symbol table: typst name -> (unicode char for text fallback / mi content,
# latex command)
# ---------------------------------------------------------------------------

SYMBOLS = {
    # lowercase greek
    "alpha": ("\u03b1", r"\alpha"),
    "beta": ("\u03b2", r"\beta"),
    "gamma": ("\u03b3", r"\gamma"),
    "delta": ("\u03b4", r"\delta"),
    "epsilon": ("\u03b5", r"\epsilon"),
    "epsilon.alt": ("\u03f5", r"\varepsilon"),
    "zeta": ("\u03b6", r"\zeta"),
    "eta": ("\u03b7", r"\eta"),
    "theta": ("\u03b8", r"\theta"),
    "theta.alt": ("\u03d1", r"\vartheta"),
    "iota": ("\u03b9", r"\iota"),
    "kappa": ("\u03ba", r"\kappa"),
    "lambda": ("\u03bb", r"\lambda"),
    "mu": ("\u03bc", r"\mu"),
    "nu": ("\u03bd", r"\nu"),
    "xi": ("\u03be", r"\xi"),
    "pi": ("\u03c0", r"\pi"),
    "rho": ("\u03c1", r"\rho"),
    "sigma": ("\u03c3", r"\sigma"),
    "tau": ("\u03c4", r"\tau"),
    "upsilon": ("\u03c5", r"\upsilon"),
    "phi": ("\u03c6", r"\phi"),
    "phi.alt": ("\u03d5", r"\varphi"),
    "chi": ("\u03c7", r"\chi"),
    "psi": ("\u03c8", r"\psi"),
    "omega": ("\u03c9", r"\omega"),
    # uppercase greek
    "Gamma": ("\u0393", r"\Gamma"),
    "Delta": ("\u0394", r"\Delta"),
    "Theta": ("\u0398", r"\Theta"),
    "Lambda": ("\u039b", r"\Lambda"),
    "Xi": ("\u039e", r"\Xi"),
    "Pi": ("\u03a0", r"\Pi"),
    "Sigma": ("\u03a3", r"\Sigma"),
    "Phi": ("\u03a6", r"\Phi"),
    "Psi": ("\u03a8", r"\Psi"),
    "Omega": ("\u03a9", r"\Omega"),
    # misc symbols
    "infinity": ("\u221e", r"\infty"),
    "partial": ("\u2202", r"\partial"),
    "nabla": ("\u2207", r"\nabla"),
    "emptyset": ("\u2205", r"\emptyset"),
    "dot": ("\u22c5", r"\cdot"),
    "times": ("\u00d7", r"\times"),
    "div": ("\u00f7", r"\div"),
    "star": ("\u22c6", r"\star"),
    "ast": ("\u2217", r"\ast"),
    "plus.minus": ("\u00b1", r"\pm"),
    "minus.plus": ("\u2213", r"\mp"),
    "lt.eq": ("\u2264", r"\leq"),
    "gt.eq": ("\u2265", r"\geq"),
    "eq.not": ("\u2260", r"\neq"),
    "approx": ("\u2248", r"\approx"),
    "equiv": ("\u2261", r"\equiv"),
    "prop": ("\u221d", r"\propto"),
    "arrow.r": ("\u2192", r"\rightarrow"),
    "arrow.l": ("\u2190", r"\leftarrow"),
    "arrow.l.r": ("\u2194", r"\leftrightarrow"),
    "arrow.r.double": ("\u21d2", r"\Rightarrow"),
    "arrow.l.double": ("\u21d0", r"\Leftarrow"),
    "arrow.l.r.double": ("\u21d4", r"\Leftrightarrow"),
    "in": ("\u2208", r"\in"),
    "in.not": ("\u2209", r"\notin"),
    "subset": ("\u2282", r"\subset"),
    "subset.eq": ("\u2286", r"\subseteq"),
    "union": ("\u222a", r"\cup"),
    "sect": ("\u2229", r"\cap"),
    "forall": ("\u2200", r"\forall"),
    "exists": ("\u2203", r"\exists"),
    "sum": ("\u2211", r"\sum"),
    "product": ("\u220f", r"\prod"),
    "integral": ("\u222b", r"\int"),
    "integral.double": ("\u222c", r"\iint"),
    "integral.triple": ("\u222d", r"\iiint"),
    "integral.cont": ("\u222e", r"\oint"),
    "dots.h": ("\u2026", r"\ldots"),
    "dots.v": ("\u22ee", r"\vdots"),
    "dots.c": ("\u22ef", r"\cdots"),
    "dots.d": ("\u22f1", r"\ddots"),
    "checkmark": ("\u2713", r"\checkmark"),
    "degree": ("\u00b0", r"^\circ"),
    "and": ("\u2227", r"\land"),
    "or": ("\u2228", r"\lor"),
    "not": ("\u00ac", r"\lnot"),
    "dif": ("d", r"\mathrm{d}"),
}

# ASCII shorthands typst accepts inline that map onto the symbol table above
SHORTHANDS = {
    "->": "arrow.r",
    "<-": "arrow.l",
    "<->": "arrow.l.r",
    "=>": "arrow.r.double",
    "<=": "lt.eq",
    ">=": "gt.eq",
    "!=": "eq.not",
    "<=>": "arrow.l.r.double",
}

# Accent functions: typst name -> (combining unicode char, latex command)
ACCENT_MAP = {
    "hat": ("\u0302", r"\hat"),
    "tilde": ("\u0303", r"\tilde"),
    "dot": ("\u0307", r"\dot"),
    "diaer": ("\u0308", r"\ddot"),
    "dot.double": ("\u0308", r"\ddot"),
    "ddot": ("\u0308", r"\ddot"),
    "breve": ("\u0306", r"\breve"),
    "check": ("\u030c", r"\check"),
    "acute": ("\u0301", r"\acute"),
    "grave": ("\u0300", r"\grave"),
    "circle": ("\u030a", r"\mathring"),
    "bar": ("\u0304", r"\bar"),
    "arrow": ("\u20d7", r"\vec"),
}

# Math-alphabet style functions: typst name -> Unicode Mathematical
# Alphanumeric Symbols block base (uppercase_base, lowercase_base), plus a
# LaTeX macro. The block has irregular gaps for a handful of letters in
# double-struck/script/fraktur/italic (they live in the legacy Letterlike
# Symbols block instead) -- handled via _MATH_ALPHA_EXCEPTIONS below.
_MATH_ALPHA_BASES = {
    "bold": (0x1D400, 0x1D41A),
    "italic": (0x1D434, 0x1D44E),
    "cal": (0x1D49C, 0x1D4B6),
    "frak": (0x1D504, 0x1D51E),
    "bb": (0x1D538, 0x1D552),
    "sans": (0x1D5A0, 0x1D5BA),
    "mono": (0x1D670, 0x1D68A),
}
_MATH_ALPHA_EXCEPTIONS = {
    "italic": {"h": "\u210e"},
    "cal": {
        "B": "\u212c",
        "E": "\u2130",
        "F": "\u2131",
        "H": "\u210b",
        "I": "\u2110",
        "L": "\u2112",
        "M": "\u2133",
        "R": "\u211b",
        "e": "\u212f",
        "g": "\u210a",
        "o": "\u2134",
    },
    "frak": {"C": "\u212d", "H": "\u210c", "I": "\u2111", "R": "\u211c", "Z": "\u2128"},
    "bb": {
        "C": "\u2102",
        "H": "\u210d",
        "N": "\u2115",
        "P": "\u2119",
        "Q": "\u211a",
        "R": "\u211d",
        "Z": "\u2124",
    },
}
_STYLE_LATEX_CMD = {
    "bold": r"\mathbf",
    "italic": r"\mathit",
    "upright": r"\mathrm",
    "serif": r"\mathrm",
    "cal": r"\mathcal",
    "frak": r"\mathfrak",
    "bb": r"\mathbb",
    "sans": r"\mathsf",
    "mono": r"\mathtt",
}
# "variants" in Typst's docs (alternate typefaces) and "styles" (alternate
# letterforms) are treated as the same mechanism here -- both are just
# math-alphabet switches as far as this converter is concerned.
STYLE_FUNCS = set(_STYLE_LATEX_CMD) | {"variant"}

_PRIME_GLYPHS = {1: "\u2032", 2: "\u2033", 3: "\u2034", 4: "\u2057"}


def _math_alpha_char(c, style):
    exceptions = _MATH_ALPHA_EXCEPTIONS.get(style, {})
    if c in exceptions:
        return exceptions[c]
    if style not in _MATH_ALPHA_BASES:
        return c
    upper_base, lower_base = _MATH_ALPHA_BASES[style]
    if "A" <= c <= "Z":
        return chr(upper_base + (ord(c) - ord("A")))
    if "a" <= c <= "z":
        return chr(lower_base + (ord(c) - ord("a")))
    return c


def _math_alpha_string(s, style):
    return "".join(_math_alpha_char(c, style) for c in s)


def _plain_text_of(node):
    """Best-effort extraction of literal characters from a simple node
    (ident/word/num/row-of-those) -- used by style functions like bb()/
    cal() which only really make sense applied to plain letters."""
    t = node.get("type")
    if t == "ident" or t == "word":
        return node["name"]
    if t == "num":
        return str(node["value"])
    if t == "row" or t == "seq":
        return "".join(
            _plain_text_of(it) for it in node["items"] if it.get("type") not in ("op",)
        )
    return ""


def _prime_string(count):
    if count in _PRIME_GLYPHS:
        return _PRIME_GLYPHS[count]
    return "\u2032" * count


# Big operators that should use under/over (rather than sub/sup) for limits
BIG_OPS = {
    "sum",
    "product",
    "integral",
    "integral.double",
    "integral.triple",
    "integral.cont",
    "union",
    "sect",
}

# Multi-letter function-like words with dedicated LaTeX macros
TEXT_OPERATORS = {
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "sinh",
    "cosh",
    "tanh",
    "ln",
    "log",
    "exp",
    "det",
    "dim",
    "gcd",
    "lcm",
    "mod",
    "min",
    "max",
    "lim",
    "sup",
    "inf",
    "arg",
    "ker",
    "hom",
    "arccos",
    "arcsin",
    "arctan",
}

TOKEN_RE = re.compile(
    r"""
    \s+
  | "(?:[^"\\]|\\.)*"
  | \d+\.\d+|\d+
  | [A-Za-z][A-Za-z0-9.]*
  | ->|<->|<=>|=>|<=|>=|!=
  | [()\[\]{}|,;^_/+\-*=<>!']
""",
    re.VERBOSE,
)


def tokenize(src):
    tokens = []
    pos = 0
    n = len(src)
    while pos < n:
        m = TOKEN_RE.match(src, pos)
        if not m:
            pos += 1  # skip unrecognised char rather than crash
            continue
        text = m.group(0)
        pos = m.end()
        if text.strip() == "":
            continue
        if text in SHORTHANDS:
            tokens.append(("SYM", SHORTHANDS[text]))
        elif text[0] == '"':
            tokens.append(("STRING", text[1:-1].replace('\\"', '"')))
        elif re.match(r"^\d", text):
            tokens.append(("NUM", text))
        elif re.match(r"^[A-Za-z]", text):
            tokens.append(("IDENT", text))
        else:
            tokens.append(("PUNCT", text))
    tokens.append(("EOF", ""))
    return tokens


# ---------------------------------------------------------------------------
# AST nodes are plain dicts: {"type": ..., ...fields}
# ---------------------------------------------------------------------------

FUNC_ARGS_AS_ROWS = {"mat", "cases"}  # ';' separates rows for these


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i]

    def advance(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def at_end_of_group(self):
        return (
            self.peek()[0] == "EOF"
            or self.peek() == ("PUNCT", ")")
            or self.peek() == ("PUNCT", "]")
            or self.peek() == ("PUNCT", "}")
            or self.peek() == ("PUNCT", "|")
            or self.peek() == ("PUNCT", ",")
            or self.peek() == ("PUNCT", ";")
        )

    def parse_row(self):
        """A sequence of terms joined by +, -, =, <, >, or symbol operators
        (->. equiv, etc.) -> {"type": "row", "items": [...]}"""
        items = [self.parse_term()]
        while True:
            kind, val = self.peek()
            if kind == "PUNCT" and val in ("+", "-", "=", "<", ">", "!"):
                self.advance()
                items.append({"type": "op", "value": val})
                items.append(self.parse_term())
                continue
            if kind == "SYM":
                self.advance()
                items.append({"type": "sym", "name": val})
                items.append(self.parse_term())
                continue
            break
        if len(items) == 1:
            return items[0]
        return {"type": "row", "items": items}

    def parse_term(self):
        """Implicit multiplication of factors; a factor may contain a single '/'"""
        factors = [self.parse_factor()]
        while (
            not self.at_end_of_group()
            and not (
                self.peek()[0] == "PUNCT"
                and self.peek()[1] in ("+", "-", "=", "<", ">", "!")
            )
            and self.peek()[0] != "SYM"
        ):
            factors.append(self.parse_factor())
        if len(factors) == 1:
            return factors[0]
        return {"type": "seq", "items": factors}

    def parse_factor(self):
        left = self.parse_postfix()
        if self.peek() == ("PUNCT", "/"):
            self.advance()
            right = self.parse_postfix()
            return {"type": "frac", "num": left, "den": right}
        return left

    def parse_postfix(self):
        base = self.parse_primary()
        prime_count = 0
        while self.peek() == ("PUNCT", "'"):
            self.advance()
            prime_count += 1
        if prime_count:
            base = {"type": "primes", "base": base, "count": prime_count}
        sup = None
        sub = None
        while self.peek()[0] == "PUNCT" and self.peek()[1] in ("^", "_"):
            marker = self.advance()[1]
            operand = self.parse_primary()
            if operand.get("type") == "paren" and operand.get("open") == "(":
                # `^(...)`/`_(...)` is invisible grouping, like LaTeX's {...}
                operand = operand["body"]
            if marker == "^":
                sup = operand
            else:
                sub = operand
        if sup is not None and sub is not None:
            return {"type": "subsup", "base": base, "sub": sub, "sup": sup}
        if sup is not None:
            return {"type": "sup", "base": base, "sup": sup}
        if sub is not None:
            return {"type": "sub", "base": base, "sub": sub}
        return base

    def parse_primary(self):
        kind, val = self.peek()

        if kind == "NUM":
            self.advance()
            return {"type": "num", "value": val}

        if kind == "STRING":
            self.advance()
            return {"type": "text", "value": val}

        if kind == "PUNCT" and val == "(":
            self.advance()
            row = self.parse_row()
            if self.peek() == ("PUNCT", ")"):
                self.advance()
            return {"type": "paren", "open": "(", "close": ")", "body": row}

        if kind == "PUNCT" and val == "[":
            self.advance()
            row = self.parse_row()
            if self.peek() == ("PUNCT", "]"):
                self.advance()
            return {"type": "paren", "open": "[", "close": "]", "body": row}

        if kind == "PUNCT" and val == "{":
            self.advance()
            row = self.parse_row()
            if self.peek() == ("PUNCT", "}"):
                self.advance()
            return {"type": "paren", "open": "{", "close": "}", "body": row}

        if kind == "PUNCT" and val == "|":
            self.advance()
            row = self.parse_row()
            if self.peek() == ("PUNCT", "|"):
                self.advance()
            return {"type": "abs", "body": row}

        if kind == "SYM":
            self.advance()
            return {"type": "sym", "name": val}

        if kind == "IDENT":
            self.advance()
            if self.peek() == ("PUNCT", "("):
                return self.parse_call(val)
            if val in SYMBOLS:
                return {"type": "sym", "name": val}
            if len(val) == 1:
                return {"type": "ident", "name": val}
            return {"type": "word", "name": val}

        if kind == "PUNCT" and val in ("+", "-", "*", "=", "<", ">", "!"):
            self.advance()
            return {"type": "op", "value": val}

        # Fallback: consume the token so we always make progress
        self.advance()
        return {"type": "word", "name": str(val)}

    def parse_call(self, name):
        self.advance()  # consume '('
        args = []
        rows = [[]]
        depth = 0
        while True:
            k, v = self.peek()
            if k == "EOF":
                break
            if k == "PUNCT" and v == "(":
                depth += 1
            if k == "PUNCT" and v == ")" and depth == 0:
                self.advance()
                break
            if k == "PUNCT" and v == ")" and depth > 0:
                depth -= 1
            if k == "PUNCT" and v == ";" and name in FUNC_ARGS_AS_ROWS and depth == 0:
                self.advance()
                rows.append([])
                continue
            if k == "PUNCT" and v == "," and depth == 0:
                self.advance()
                continue
            if k == "IDENT" and self.tokens[self.i + 1] == ("PUNCT", ":"):
                # named argument -- parse and keep only for delim: "x" (else skip)
                key = v
                self.advance()
                self.advance()  # ':'
                value_node = self.parse_row()
                if key == "delim":
                    args.append({"type": "__delim__", "node": value_node})
                continue
            node = self.parse_row()
            rows[-1].append(node)
        if name in FUNC_ARGS_AS_ROWS:
            return {"type": "call", "name": name, "rows": rows, "args": []}
        flat_args = [a for row in rows for a in row] + args
        return {"type": "call", "name": name, "args": flat_args}


def parse_math(src):
    tokens = tokenize(src)
    parser = Parser(tokens)
    node = parser.parse_row()
    return node


# ---------------------------------------------------------------------------
# Rendering: MathML
# ---------------------------------------------------------------------------

VALUE_SYMBOLS = {
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "epsilon.alt",
    "zeta",
    "eta",
    "theta",
    "theta.alt",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "phi.alt",
    "chi",
    "psi",
    "omega",
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Phi",
    "Psi",
    "Omega",
    "infinity",
    "partial",
    "nabla",
    "emptyset",
    "dots.h",
    "dots.v",
    "dots.c",
    "dots.d",
    "checkmark",
    "degree",
    "dif",
}


def esc(s):
    return html.escape(str(s), quote=False)


def _group(node):
    """Wrap in <mrow> so multi-token content is exactly one child element,
    which mfrac/msup/msub/mroot/etc. all require."""
    return f"<mrow>{render_mathml(node)}</mrow>"


def render_mathml(node):
    t = node["type"]

    if t == "row" or t == "seq":
        return "".join(render_mathml(it) for it in node["items"])

    if t == "num":
        return f"<mn>{esc(node['value'])}</mn>"

    if t == "text":
        return f"<mtext>{esc(node['value'])}</mtext>"

    if t == "ident":
        return f"<mi>{esc(node['name'])}</mi>"

    if t == "word":
        return f'<mi mathvariant="normal">{esc(node["name"])}</mi>'

    if t == "sym":
        char, _ = SYMBOLS[node["name"]]
        return (
            f"<mi>{esc(char)}</mi>"
            if node["name"] in VALUE_SYMBOLS
            else f"<mo>{esc(char)}</mo>"
        )

    if t == "op":
        return f"<mo>{esc(node['value'])}</mo>"

    if t == "frac":
        return f"<mfrac>{_group(node['num'])}{_group(node['den'])}</mfrac>"

    if t == "paren":
        o, c = node["open"], node["close"]
        return f"<mrow><mo>{esc(o)}</mo>{render_mathml(node['body'])}<mo>{esc(c)}</mo></mrow>"

    if t == "abs":
        return f"<mrow><mo>|</mo>{render_mathml(node['body'])}<mo>|</mo></mrow>"

    if t == "primes":
        return f"<msup>{_group(node['base'])}<mo>{esc(_prime_string(node['count']))}</mo></msup>"

    if t in ("sup", "sub", "subsup"):
        base = node["base"]
        is_big = base.get("type") == "sym" and base.get("name") in BIG_OPS
        base_mml = _group(base)
        if t == "sup":
            tag = "mover" if is_big else "msup"
            return f"<{tag}>{base_mml}{_group(node['sup'])}</{tag}>"
        if t == "sub":
            tag = "munder" if is_big else "msub"
            return f"<{tag}>{base_mml}{_group(node['sub'])}</{tag}>"
        tag = "munderover" if is_big else "msubsup"
        return f"<{tag}>{base_mml}{_group(node['sub'])}{_group(node['sup'])}</{tag}>"

    if t == "call":
        return _render_call_mathml(node)

    return f"<mtext>{esc(str(node))}</mtext>"


def _cells_mathml(rows):
    trs = []
    for row in rows:
        tds = "".join(f"<mtd>{_group(cell)}</mtd>" for cell in row)
        trs.append(f"<mtr>{tds}</mtr>")
    return f"<mtable>{''.join(trs)}</mtable>"


def _render_call_mathml(node):
    name = node["name"]
    args = node.get("args", [])

    if name == "sqrt" and args:
        return f"<msqrt>{render_mathml(args[0])}</msqrt>"

    if name == "root" and len(args) >= 2:
        return f"<mroot>{_group(args[1])}{_group(args[0])}</mroot>"

    if name == "frac" and len(args) >= 2:
        return f"<mfrac>{_group(args[0])}{_group(args[1])}</mfrac>"

    if name == "binom" and len(args) >= 2:
        return (
            f'<mrow><mo>(</mo><mfrac linethickness="0">'
            f"{_group(args[0])}{_group(args[1])}"
            f"</mfrac><mo>)</mo></mrow>"
        )

    if name in ("abs",) and args:
        return f"<mrow><mo>|</mo>{render_mathml(args[0])}<mo>|</mo></mrow>"

    if name in ("norm",) and args:
        return f"<mrow><mo>\u2016</mo>{render_mathml(args[0])}<mo>\u2016</mo></mrow>"

    if name == "floor" and args:
        return f"<mrow><mo>\u230a</mo>{render_mathml(args[0])}<mo>\u230b</mo></mrow>"

    if name == "ceil" and args:
        return f"<mrow><mo>\u2308</mo>{render_mathml(args[0])}<mo>\u2309</mo></mrow>"

    if name == "vec":
        rows = [[a] for a in args]
        return f"<mrow><mo>(</mo>{_cells_mathml(rows)}<mo>)</mo></mrow>"

    if name == "mat":
        rows = node.get("rows", [[]])
        return f"<mrow><mo>(</mo>{_cells_mathml(rows)}<mo>)</mo></mrow>"

    if name == "cases":
        rows = node.get("rows", [[]])
        return f"<mrow><mo>{{</mo>{_cells_mathml(rows)}</mrow>"

    if name == "op" and args and args[0].get("type") == "text":
        return f'<mi mathvariant="normal">{esc(args[0]["value"])}</mi>'

    if name == "text" and args and args[0].get("type") == "text":
        return f"<mtext>{esc(args[0]['value'])}</mtext>"

    if name in ACCENT_MAP and args:
        char, _ = ACCENT_MAP[name]
        return f"<mover>{_group(args[0])}<mo>{esc(char)}</mo></mover>"

    if name == "accent" and len(args) >= 2:
        second = args[1]
        sym_name = (
            second.get("name")
            if second.get("type") in ("sym", "word", "ident")
            else None
        )
        if not isinstance(sym_name, str) or sym_name not in ACCENT_MAP:
            sym_name = "hat"
        char, _ = ACCENT_MAP[sym_name]
        return f"<mover>{_group(args[0])}<mo>{esc(char)}</mo></mover>"

    if name in STYLE_FUNCS and args:
        style = "bold" if name == "variant" else name
        text = _plain_text_of(args[0])
        if text:
            styled = _math_alpha_string(text, style)
            variant_attr = (
                "" if style in ("upright", "serif") else ' mathvariant="normal"'
            )
            return f"<mi{variant_attr}>{esc(styled)}</mi>"
        return render_mathml(args[0])

    if name == "cancel" and args:
        return (
            f'<menclose notation="updiagonalstrike">{render_mathml(args[0])}</menclose>'
        )

    if name == "class" and args:
        content = args[1] if len(args) >= 2 else args[0]
        return render_mathml(content)

    if name in ("lr", "stretch") and args:
        return render_mathml(args[0])

    if name in ("display", "inline", "script", "sscript") and args:
        style_attrs = {
            "display": 'displaystyle="true"',
            "inline": 'displaystyle="false"',
            "script": 'scriptlevel="1"',
            "sscript": 'scriptlevel="2"',
        }
        return f"<mstyle {style_attrs[name]}>{_group(args[0])}</mstyle>"

    if name in ("overbrace", "underbrace") and args:
        brace = "\u23de" if name == "overbrace" else "\u23df"
        tag = "mover" if name == "overbrace" else "munder"
        base = f"<{tag}>{_group(args[0])}<mo>{brace}</mo></{tag}>"
        if len(args) >= 2:
            return f"<{tag}>{base}{_group(args[1])}</{tag}>"
        return base

    # Unknown/generic function call: render as name(arg1, arg2, ...)
    inner = "<mo>,</mo>".join(render_mathml(a) for a in args)
    label = (
        f'<mi mathvariant="normal">{esc(name)}</mi>'
        if name in TEXT_OPERATORS
        else f"<mi>{esc(name)}</mi>"
    )
    return f"{label}<mo>(</mo>{inner}<mo>)</mo>"


# ---------------------------------------------------------------------------
# Rendering: LaTeX
# ---------------------------------------------------------------------------


def render_latex(node):
    t = node["type"]

    if t == "row" or t == "seq":
        return " ".join(render_latex(it) for it in node["items"])

    if t == "num":
        return str(node["value"])

    if t == "text":
        return r"\text{" + node["value"] + "}"

    if t == "ident":
        return node["name"]

    if t == "word":
        if node["name"] in TEXT_OPERATORS:
            return "\\" + node["name"]
        return r"\mathrm{" + node["name"] + "}"

    if t == "sym":
        _, cmd = SYMBOLS[node["name"]]
        return cmd

    if t == "op":
        return node["value"]

    if t == "frac":
        return (
            r"\frac{"
            + render_latex(node["num"])
            + "}{"
            + render_latex(node["den"])
            + "}"
        )

    if t == "paren":
        o, c = node["open"], node["close"]
        return rf"\left{o} " + render_latex(node["body"]) + rf" \right{c}"

    if t == "abs":
        return r"\left|" + render_latex(node["body"]) + r"\right|"

    if t == "primes":
        return render_latex(node["base"]) + "'" * node["count"]

    if t in ("sup", "sub", "subsup"):
        base = render_latex(node["base"])
        if t == "sup":
            return base + "^{" + render_latex(node["sup"]) + "}"
        if t == "sub":
            return base + "_{" + render_latex(node["sub"]) + "}"
        return (
            base
            + "_{"
            + render_latex(node["sub"])
            + "}^{"
            + render_latex(node["sup"])
            + "}"
        )

    if t == "call":
        return _render_call_latex(node)

    return str(node)


def _rows_latex(rows, sep=r" \\ "):
    return sep.join(" & ".join(render_latex(cell) for cell in row) for row in rows)


def _render_call_latex(node):
    name = node["name"]
    args = node.get("args", [])

    if name == "sqrt" and args:
        return r"\sqrt{" + render_latex(args[0]) + "}"

    if name == "root" and len(args) >= 2:
        return r"\sqrt[" + render_latex(args[0]) + "]{" + render_latex(args[1]) + "}"

    if name == "frac" and len(args) >= 2:
        return r"\frac{" + render_latex(args[0]) + "}{" + render_latex(args[1]) + "}"

    if name == "binom" and len(args) >= 2:
        return r"\binom{" + render_latex(args[0]) + "}{" + render_latex(args[1]) + "}"

    if name == "abs" and args:
        return r"\left|" + render_latex(args[0]) + r"\right|"

    if name == "norm" and args:
        return r"\left\|" + render_latex(args[0]) + r"\right\|"

    if name == "floor" and args:
        return r"\left\lfloor " + render_latex(args[0]) + r"\right\rfloor"

    if name == "ceil" and args:
        return r"\left\lceil " + render_latex(args[0]) + r"\right\rceil"

    if name == "vec":
        rows = [[a] for a in args]
        return r"\begin{pmatrix}" + _rows_latex(rows) + r"\end{pmatrix}"

    if name == "mat":
        rows = node.get("rows", [[]])
        return r"\begin{pmatrix}" + _rows_latex(rows) + r"\end{pmatrix}"

    if name == "cases":
        rows = node.get("rows", [[]])
        return r"\begin{cases}" + _rows_latex(rows, sep=r" \\ ") + r"\end{cases}"

    if name == "op" and args and args[0].get("type") == "text":
        return r"\operatorname{" + args[0]["value"] + "}"

    if name == "text" and args and args[0].get("type") == "text":
        return r"\text{" + args[0]["value"] + "}"

    if name in ACCENT_MAP and args:
        _, cmd = ACCENT_MAP[name]
        return cmd + "{" + render_latex(args[0]) + "}"

    if name == "accent" and len(args) >= 2:
        second = args[1]
        sym_name = (
            second.get("name")
            if second.get("type") in ("sym", "word", "ident")
            else None
        )
        if not isinstance(sym_name, str) or sym_name not in ACCENT_MAP:
            sym_name = "hat"
        _, cmd = ACCENT_MAP[sym_name]
        return cmd + "{" + render_latex(args[0]) + "}"

    if name in STYLE_FUNCS and args:
        style = "bold" if name == "variant" else name
        cmd = _STYLE_LATEX_CMD.get(style, r"\mathrm")
        return cmd + "{" + render_latex(args[0]) + "}"

    if name == "cancel" and args:
        return r"\cancel{" + render_latex(args[0]) + "}"

    if name == "class" and args:
        content = args[1] if len(args) >= 2 else args[0]
        return render_latex(content)

    if name in ("lr", "stretch") and args:
        return render_latex(args[0])

    if name in ("display", "inline", "script", "sscript") and args:
        cmd = {
            "display": r"\displaystyle",
            "inline": r"\textstyle",
            "script": r"\scriptstyle",
            "sscript": r"\scriptscriptstyle",
        }[name]
        return "{" + cmd + " " + render_latex(args[0]) + "}"

    if name in ("overbrace", "underbrace") and args:
        cmd = r"\overbrace" if name == "overbrace" else r"\underbrace"
        marker = "^" if name == "overbrace" else "_"
        base = cmd + "{" + render_latex(args[0]) + "}"
        if len(args) >= 2:
            return base + marker + "{" + render_latex(args[1]) + "}"
        return base

    inner = ", ".join(render_latex(a) for a in args)
    label = ("\\" + name) if name in TEXT_OPERATORS else (r"\mathrm{" + name + "}")
    return label + "(" + inner + ")"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

MATH_JS_CLASS = "typst-math"


def convert_math(src, display=False, alt=None):
    """Convert Typst math source (without the surrounding $ signs) into an
    HTML snippet containing MathML (primary) with an embedded LaTeX
    annotation, plus a hidden LaTeX fallback span for browsers without
    MathML support. `alt`, if given, becomes an aria-label on the <math>
    element -- MathML's actual accessible-name mechanism, matching
    Typst's own `#math.equation(alt: "...")` accessibility parameter."""
    src = src.strip()
    try:
        ast = parse_math(src)
        mathml_body = render_mathml(ast)
        latex_body = render_latex(ast)
    except Exception:
        # Never let a single malformed equation break the whole build.
        escaped = esc(src)
        mathml_body = f"<mtext>{escaped}</mtext>"
        latex_body = src

    display_attr = "block" if display else "inline"
    tex_delims = (r"\[", r"\]") if display else (r"\(", r"\)")
    fallback_tex = f"{tex_delims[0]}{latex_body}{tex_delims[1]}"
    alt_attr = f' aria-label="{esc(alt)}"' if alt else ""

    return (
        f'<span class="{MATH_JS_CLASS}" data-display="{display_attr}">'
        f'<math xmlns="http://www.w3.org/1998/Math/MathML" display="{display_attr}"{alt_attr}>'
        f"<semantics><mrow>{mathml_body}</mrow>"
        f'<annotation encoding="application/x-tex">{esc(latex_body)}</annotation>'
        f"</semantics></math>"
        f'<span class="typst-math-fallback" aria-hidden="true" hidden>{esc(fallback_tex)}</span>'
        f"</span>"
    )
