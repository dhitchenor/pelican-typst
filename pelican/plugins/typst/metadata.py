"""
Metadata extraction for .typ Pelican source files.

Two styles are supported, auto-detected, so authors can use whichever they
prefer per file:

1. YAML front matter, exactly like Pelican's Markdown reader:

    ---
    title: My First Post
    date: 2026-06-01
    tags: [typst, pelican]
    ---
    = Body starts here

2. A native Typst dictionary passed to a `#metadata()` call at the top of
   the file (valid Typst, so `typst compile` on the same source elsewhere
   still works if you ever want it to):

    #metadata((
      title: "My First Post",
      date: "2026-06-01",
      tags: ("typst", "pelican"),
    ))

    = Body starts here

Only literal values are supported in the Typst-native form (strings,
numbers, booleans, `none`, arrays, and nested dicts) -- this is a small
literal parser, not a Typst evaluator.
"""

import re

from . import simpleyaml


def extract_metadata(text):
    """Return (metadata_dict, remaining_body_text)."""
    text = text.lstrip("\ufeff")
    lstripped = text.lstrip()
    offset = len(text) - len(lstripped)

    if lstripped.startswith("---"):
        result = _extract_yaml(text, offset)
        if result is not None:
            return result

    found = _find_metadata_call(text)
    if found:
        inner, consumed = found
        try:
            data, _ = _parse_value(inner, 0)
        except (ValueError, IndexError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        return data, text[consumed:]

    return {}, text


def _extract_yaml(text, offset):
    m = re.match(r"---[ \t]*\n(.*?\n)---[ \t]*\n?", text[offset:], re.DOTALL)
    if not m:
        return None
    try:
        data = simpleyaml.safe_load(m.group(1))
    except (ValueError, IndexError):
        data = None
    if not isinstance(data, dict):
        data = {}
    body = text[offset + m.end() :]
    return data, body


def _find_metadata_call(text):
    """Locate a leading `#metadata(...)` call, skipping blank lines and
    `//` line comments that may precede it. Returns (inner_src, end_index)
    or None."""
    idx = 0
    n = len(text)
    while idx < n:
        m = re.match(r"[ \t\r\n]+", text[idx:])
        if m:
            idx += m.end()
            continue
        if text[idx : idx + 2] == "//":
            nl = text.find("\n", idx)
            idx = nl + 1 if nl != -1 else n
            continue
        break

    if not text[idx:].startswith("#metadata("):
        return None

    start = idx + len("#metadata(")
    depth = 1
    i = start
    in_str = False
    while i < n and depth > 0:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
        i += 1

    inner = text[start : i - 1]
    end = i
    if end < n and text[end] == ";":
        end += 1
    return inner, end


# ---------------------------------------------------------------------------
# Minimal Typst literal-value parser: strings, numbers, booleans, none,
# arrays `(a, b, c)`, and dicts `(key: value, ...)`.
# ---------------------------------------------------------------------------


def _skip_ws(s, i):
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i


def _parse_value(s, i):
    i = _skip_ws(s, i)
    if i >= len(s):
        raise ValueError("unexpected end of metadata")
    c = s[i]

    if c == '"':
        return _parse_string(s, i)

    if c == "(":
        return _parse_paren(s, i)

    if s[i : i + 4] == "true" and not _is_ident_char(s, i + 4):
        return True, i + 4
    if s[i : i + 5] == "false" and not _is_ident_char(s, i + 5):
        return False, i + 5
    if s[i : i + 4] == "none" and not _is_ident_char(s, i + 4):
        return None, i + 4

    m = re.match(r"-?\d+(\.\d+)?", s[i:])
    if m:
        text = m.group(0)
        val = float(text) if "." in text else int(text)
        return val, i + m.end()

    # Bare/unquoted token (e.g. an unquoted date) -- read up to a
    # delimiter and use the raw text.
    m = re.match(r"[^,()\s][^,()]*", s[i:])
    if m:
        return m.group(0).strip(), i + m.end()

    raise ValueError(f"cannot parse metadata value near: {s[i : i + 20]!r}")


def _is_ident_char(s, i):
    return i < len(s) and (s[i].isalnum() or s[i] == "_")


def _parse_string(s, i):
    j = i + 1
    out = []
    while j < len(s) and s[j] != '"':
        if s[j] == "\\" and j + 1 < len(s):
            out.append(s[j + 1])
            j += 2
        else:
            out.append(s[j])
            j += 1
    return "".join(out), j + 1


def _parse_paren(s, i):
    j = _skip_ws(s, i + 1)
    if j < len(s) and s[j] == ")":
        return {}, j + 1
    if re.match(r"[A-Za-z_][A-Za-z0-9_-]*\s*:", s[j:]):
        return _parse_dict_body(s, i)
    return _parse_array_body(s, i)


def _parse_dict_body(s, i):
    j = i + 1
    result = {}
    while True:
        j = _skip_ws(s, j)
        if j < len(s) and s[j] == ")":
            return result, j + 1
        m = re.match(r"[A-Za-z_][A-Za-z0-9_-]*", s[j:])
        if not m:
            raise ValueError("malformed metadata dict key")
        key = m.group(0)
        j = _skip_ws(s, j + m.end())
        if j >= len(s) or s[j] != ":":
            raise ValueError("expected ':' in metadata dict")
        j += 1
        value, j = _parse_value(s, j)
        result[key] = value
        j = _skip_ws(s, j)
        if j < len(s) and s[j] == ",":
            j += 1
            continue
        if j < len(s) and s[j] == ")":
            return result, j + 1
        raise ValueError("malformed metadata dict")


def _parse_array_body(s, i):
    j = i + 1
    result = []
    while True:
        j = _skip_ws(s, j)
        if j < len(s) and s[j] == ")":
            return result, j + 1
        value, j = _parse_value(s, j)
        result.append(value)
        j = _skip_ws(s, j)
        if j < len(s) and s[j] == ",":
            j += 1
            continue
        if j < len(s) and s[j] == ")":
            return result, j + 1
        raise ValueError("malformed metadata array")
