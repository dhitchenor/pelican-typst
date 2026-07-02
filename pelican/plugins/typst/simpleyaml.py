"""
A tiny YAML-subset parser, just enough for Pelican-style front matter --
not a general YAML implementation.

Supported:
    key: value
    key: "quoted value"
    key: 'quoted value'
    key: [inline, list, of, values]
    key:
      - block
      - list
      - of values
    booleans (true/false/yes/no), null/~, ints, floats,
    ISO dates (2026-06-01) and datetimes (2026-06-01 10:30 / with T),
    # comments (outside quotes)

Deliberately NOT supported (front matter essentially never needs these):
    anchors/aliases (&x, *x), multi-line block scalars (| and >),
    flow mappings ({a: 1}), nested mappings, multiple documents,
    tags (!!something).

If a file uses any of the unsupported forms, values will come back as
plain strings rather than raising -- good enough for metadata, where a
slightly-wrong parse of an edge case beats a hard crash on someone's
otherwise-fine post.
"""

import datetime
import re

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$")
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")


def safe_load(text):
    """Parse a flat (optionally list-valued) YAML mapping into a dict."""
    lines = text.split("\n")
    result = {}
    i = 0
    n = len(lines)

    while i < n:
        line = _strip_comment(lines[i])
        if line.strip() == "":
            i += 1
            continue

        m = _KEY_RE.match(line)
        if not m:
            i += 1
            continue

        key, rest = m.group(1), m.group(2).strip()

        if rest != "":
            result[key] = _parse_scalar(rest)
            i += 1
            continue

        # No inline value -- check whether a block list follows.
        items = []
        j = i + 1
        found_list = False
        while j < n:
            nxt = _strip_comment(lines[j])
            if nxt.strip() == "":
                j += 1
                continue
            if len(lines[j]) - len(lines[j].lstrip(" ")) == 0:
                break  # back to column 0, this key's block is over
            stripped = nxt.strip()
            if stripped.startswith("- "):
                items.append(_parse_scalar(stripped[2:].strip()))
                found_list = True
                j += 1
                continue
            break
        result[key] = items if found_list else None
        i = j if found_list else i + 1

    return result


def _strip_comment(line):
    in_single = False
    in_double = False
    for idx, c in enumerate(line):
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif c == "#" and not in_single and not in_double:
            if idx == 0 or line[idx - 1] in " \t":
                return line[:idx]
    return line


def _parse_scalar(s):
    s = s.strip()
    if s == "":
        return None

    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if inner == "" else [_parse_scalar(p) for p in _split_commas(inner)]

    if (s.startswith('"') and s.endswith('"') and len(s) >= 2) or \
       (s.startswith("'") and s.endswith("'") and len(s) >= 2):
        return s[1:-1]

    if s in ("null", "Null", "NULL", "~"):
        return None
    if s in ("true", "True", "TRUE", "yes", "Yes"):
        return True
    if s in ("false", "False", "FALSE", "no", "No"):
        return False

    if _DATETIME_RE.match(s):
        date_part, time_part = re.split(r"[ T]", s, maxsplit=1)
        d = datetime.date.fromisoformat(date_part)
        hh, mm, *ss = time_part.split(":")
        sec = int(ss[0]) if ss else 0
        return datetime.datetime(d.year, d.month, d.day, int(hh), int(mm), sec)

    if _DATE_RE.match(s):
        return datetime.date.fromisoformat(s)

    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)

    return s


def _split_commas(s):
    """Split on top-level commas, respecting nested [...] and quotes."""
    parts = []
    depth = 0
    in_single = False
    in_double = False
    cur = ""
    for c in s:
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        if c == "," and depth == 0 and not in_single and not in_double:
            parts.append(cur)
            cur = ""
            continue
        if c == "[" and not in_single and not in_double:
            depth += 1
        elif c == "]" and not in_single and not in_double:
            depth -= 1
        cur += c
    if cur.strip() != "":
        parts.append(cur)
    return parts
