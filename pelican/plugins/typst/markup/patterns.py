"""
All regex patterns and simple lookup tables (dicts/sets) used across the
markup package, collected in one place so "what pattern matches X" is a
single, quick lookup rather than a hunt through a 1600-line file.
"""

import re

# --- Block-level start markers (each line is checked against these to
# decide whether paragraph accumulation should stop) -------------------
_HEADING_RE = re.compile(r"^(=+)\s+(.*)$")
_BULLET_RE = re.compile(r"^-\s+(.*)$")
_NUMBERED_RE = re.compile(r"^\+\s+(.*)$")
_FENCE_RE = re.compile(r"^```(\S*)\s*$")
_QUOTE_START_RE = re.compile(r"^#quote[\(\[]")
_FIGURE_START_RE = re.compile(r"^#figure\(")
_IMAGE_START_RE = re.compile(r"^#image\(")
_TABLE_START_RE = re.compile(r"^#table\(")
_GRID_START_RE = re.compile(r"^#grid\(")
_STACK_START_RE = re.compile(r"^#stack\(")
_SET_ANY_START_RE = re.compile(r"^#set\s+[\w.]+\(")
_IMPORT_START_RE = re.compile(r"^#import\s+")
_BIBLIOGRAPHY_START_RE = re.compile(r"^#bibliography\(")
_PAGEBREAK_RE = re.compile(r"^#pagebreak\([^)]*\)\s*$")
_COLBREAK_RE = re.compile(r"^#colbreak\([^)]*\)\s*$")
_V_FUNC_RE = re.compile(r"^#v\(\s*([^)]+?)\s*\)\s*$")
_TERMS_RE = re.compile(r"^/\s+(.*)$")
_SET_HEADING_NUMBERING_RE = re.compile(
    r'^#set\s+heading\(\s*numbering:\s*("(?:[^"\\]|\\.)*"|none)\s*\)\s*$'
)
_OUTLINE_RE = re.compile(r"^#outline\((.*)\)\s*$")
_LABEL_SUFFIX_RE = re.compile(r"\s*<([A-Za-z][\w.:-]*)>\s*$")
_LET_ANY_RE = re.compile(r"^#let\s+")
_LET_LITERAL_RE = re.compile(r"^#let\s+([A-Za-z_]\w*)\s*=\s*(.+?)\s*$")

_BLOCK_START_RES = [_HEADING_RE, _BULLET_RE, _NUMBERED_RE, _FENCE_RE,
                     _QUOTE_START_RE, _FIGURE_START_RE, _IMAGE_START_RE,
                     _TABLE_START_RE, _GRID_START_RE, _STACK_START_RE,
                     _SET_ANY_START_RE, _IMPORT_START_RE, _BIBLIOGRAPHY_START_RE,
                     _PAGEBREAK_RE, _COLBREAK_RE, _V_FUNC_RE, _TERMS_RE,
                     _SET_HEADING_NUMBERING_RE, _OUTLINE_RE, _LET_ANY_RE]

_TABLE_HEADER_RE = re.compile(r"^table\.header\((.*)\)$", re.DOTALL)
_DISPLAY_MATH_LINE_RE = re.compile(r"^\$\s+.*\s+\$$")

# --- Inline substitution patterns (matched within already-joined
# paragraph/heading/cell text, inside _inline()) ------------------------
_NUMBERING_RE = re.compile(
    r'#numbering\(\s*"((?:[^"\\]|\\.)*)"\s*((?:,\s*-?\d+\s*)+)\)'
)
_REF_FUNC_RE = re.compile(r"#ref\(\s*<([A-Za-z][\w.:-]*)>\s*\)")
_AT_LABEL_RE = re.compile(r"@([A-Za-z][\w:-]*)")
_H_FUNC_RE = re.compile(r"#h\(\s*([^)]+?)\s*\)")
_PAGEBREAK_INLINE_RE = re.compile(r"#pagebreak\([^)]*\)")
_COLBREAK_INLINE_RE = re.compile(r"#colbreak\([^)]*\)")
_LOREM_RE = re.compile(r"#lorem\(\s*(\d+)\s*\)")
_CITE_INLINE_RE = re.compile(r"#cite\([^)]*\)")
_HASH_REF_RE = re.compile(r"#([A-Za-z_]\w*)\b(?![(\[])")

# --- Placeholders used by the stash/restore mechanism in _inline() -----
_PLACEHOLDER = "\x00P{}\x00"
_BR_SENTINEL = "\x00BR\x00"

# --- Lookup tables -------------------------------------------------------
_SIMPLE_WRAP_TAGS = {
    "highlight": ("mark", None),
    "overline": ("span", "text-decoration: overline"),
    "smallcaps": ("span", "font-variant: small-caps"),
    "strike": ("s", None),
    "sub": ("sub", None),
    "super": ("sup", None),
    "underline": ("u", None),
    "strong": ("strong", None),
    "emph": ("em", None),
}
_KNOWN_BRACKET_FUNCS = set(_SIMPLE_WRAP_TAGS) | {"footnote", "upper", "lower"}

# Layout wrapper functions: #name(args)[content] or #name[content],
# mapped onto inline CSS. See inline_processors._render_layout_wrap.
_LAYOUT_WRAP_NAMES = {
    "align", "block", "box", "hide", "move", "pad", "place",
    "rotate", "scale", "skew", "columns", "repeat",
}

_NAMED_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple", "black", "white",
    "gray", "grey", "silver", "navy", "teal", "aqua", "maroon", "olive",
    "lime", "fuchsia", "pink", "brown", "cyan", "magenta",
}

_WEIGHT_MAP = {
    "thin": "100", "extralight": "200", "light": "300",
    "regular": "normal", "normal": "normal", "medium": "500",
    "semibold": "600", "bold": "bold", "extrabold": "800", "black": "900",
}

_ALIGN_H_MAP = {"left": "left", "right": "right", "center": "center",
                 "start": "left", "end": "right"}
