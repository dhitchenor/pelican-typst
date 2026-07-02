"""
Typst numbering-pattern formatting: `numbering("1.1.1", 2, 3)` -> "2.3.",
`numbering("a)", 27)` -> "aa)", etc. Pure functions, no shared state --
used both by the `#numbering()` inline function and by heading
auto-numbering (`#set heading(numbering:)`).
"""

_COUNTING_CHARS = set("1aAiI*")
_ROMAN_VALUES = [
    (1000, "m"), (900, "cm"), (500, "d"), (400, "cd"),
    (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
    (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i"),
]
_STAR_SYMBOLS = ["*", "\u2020", "\u2021", "\u00a7", "\u00b6", "\u2016"]  # * † ‡ § ¶ ‖


def _format_arabic(n):
    return str(n)


def _format_alpha_lower(n):
    if n <= 0:
        return str(n)
    letters = []
    while n > 0:
        n -= 1
        letters.append(chr(ord("a") + (n % 26)))
        n //= 26
    return "".join(reversed(letters))


def _format_alpha_upper(n):
    return _format_alpha_lower(n).upper()


def _format_roman_lower(n):
    if n <= 0:
        return str(n)
    result = []
    for value, symbol in _ROMAN_VALUES:
        while n >= value:
            result.append(symbol)
            n -= value
    return "".join(result)


def _format_roman_upper(n):
    return _format_roman_lower(n).upper()


def _format_star(n):
    if n <= 0:
        return str(n)
    cycle = len(_STAR_SYMBOLS)
    idx = (n - 1) % cycle
    repeat = (n - 1) // cycle + 1
    return _STAR_SYMBOLS[idx] * repeat


_COUNTING_FORMATTERS = {
    "1": _format_arabic, "a": _format_alpha_lower, "A": _format_alpha_upper,
    "i": _format_roman_lower, "I": _format_roman_upper, "*": _format_star,
}


def _tokenize_numbering_pattern(pattern):
    idx = 0
    n = len(pattern)
    prefix = ""
    while idx < n and pattern[idx] not in _COUNTING_CHARS:
        prefix += pattern[idx]
        idx += 1
    if idx >= n:
        return pattern, []

    groups = []
    current_symbol = None
    current_literal = ""
    for c in pattern[idx:]:
        if c in _COUNTING_CHARS:
            if current_symbol is not None:
                groups.append((current_symbol, current_literal))
            current_symbol = c
            current_literal = ""
        else:
            current_literal += c
    groups.append((current_symbol, current_literal))
    return prefix, groups


def _apply_numbering(pattern, numbers):
    """`numbering("1.1.1", 2, 3)` -> "2.3." -- uses only as many groups
    as numbers given; if there are MORE numbers than groups, the last
    group repeats (matching Typst's own documented behaviour)."""
    prefix, groups = _tokenize_numbering_pattern(pattern)
    if not groups:
        return pattern
    out = [prefix]
    for i, num in enumerate(numbers):
        symbol, literal = groups[min(i, len(groups) - 1)]
        out.append(_COUNTING_FORMATTERS.get(symbol, _format_arabic)(num))
        out.append(literal)
    return "".join(out)
