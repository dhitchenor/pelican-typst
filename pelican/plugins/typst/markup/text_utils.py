"""
Generic, stateless text-processing helpers used across the markup
package: argument splitting, paren/bracket call scanning, comment
stripping, linebreak joining, smart quotes, and the #let literal parser.
"""

import re

from .patterns import _BLOCK_START_RES, _BR_SENTINEL, _FENCE_RE


def _split_top_level(s, sep=","):
    """Split on a separator, respecting nested (...)/[...] and "..." """
    parts = []
    depth = 0
    in_str = False
    cur = ""
    for c in s:
        if in_str:
            cur += c
            if c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            cur += c
            continue
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        if c == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += c
    if cur.strip():
        parts.append(cur)
    return parts


def _scan_call(text, start_idx):
    """Given text and the index right after a function name (so
    text[start_idx] is '(' or '['), parse the call: optional paren-depth
    args, then an optional trailing bracket content block (Typst's
    `f(args)[content]` sugar for `f(args, [content])`). Returns
    (args_src_or_None, content_src_or_None, end_index)."""
    n = len(text)
    p = start_idx
    args_src = None
    if p < n and text[p] == "(":
        depth = 1
        j = p + 1
        in_str = False
        while j < n and depth > 0:
            c = text[j]
            if in_str:
                if c == "\\":
                    j += 1
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
            j += 1
        args_src = text[p + 1:j - 1]
        p = j
    content_src = None
    q = p
    while q < n and text[q] in " \t":
        q += 1
    if q < n and text[q] == "[":
        bdepth = 1
        r = q + 1
        while r < n and bdepth > 0:
            if text[r] == "[":
                bdepth += 1
            elif text[r] == "]":
                bdepth -= 1
            r += 1
        content_src = text[q + 1:r - 1]
        p = r
    return args_src, content_src, p


def _strip_line_comment(line, in_fence):
    if in_fence:
        return line
    i = 0
    in_str = False
    while i < len(line) - 1:
        c = line[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "/" and line[i + 1] == "/":
                return line[:i].rstrip()
        i += 1
    return line


def _strip_comments(text):
    lines = text.split("\n")
    out = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            out.append(line)
            continue
        out.append(_strip_line_comment(line, in_fence))
    text = "\n".join(out)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _join_with_linebreaks(lines):
    parts = []
    for ln in lines:
        stripped_right = ln.rstrip()
        if stripped_right.endswith("\\") and not stripped_right.endswith("\\\\"):
            parts.append(stripped_right[:-1].rstrip())
            parts.append(_BR_SENTINEL)
        else:
            parts.append(ln)
    return " ".join(parts)


def _smartquotes(text):
    text = re.sub(r'(^|[\s([{\u2018\u201c])"', "\\1\u201c", text)
    text = text.replace('"', "\u201d")
    text = re.sub(r"(^|[\s([{\u2018\u201c])'", "\\1\u2018", text)
    text = text.replace("'", "\u2019")
    return text


def _parse_let_literal(value_src):
    """Only handles simple literal bindings (#let x = "..."/123/true) --
    anything else (function definitions, expressions, other variable
    references) returns None, meaning we can't resolve it, so later
    #name references stay honestly broken rather than silently wrong."""
    value_src = value_src.strip()
    m = re.match(r'^"((?:[^"\\]|\\.)*)"$', value_src, re.DOTALL)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    if re.match(r"^-?\d+(\.\d+)?$", value_src):
        return value_src
    if value_src in ("true", "false"):
        return value_src
    return None


def _looks_like_block_start(line):
    return any(r.match(line) for r in _BLOCK_START_RES) or line.strip() == ""
