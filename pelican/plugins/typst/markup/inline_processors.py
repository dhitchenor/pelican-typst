"""
Inline text-substitution passes: the various `#name[...]`/`#name(...)`
scanners that run inside _inline(), turning Typst function calls
embedded in prose into stashed HTML fragments. Split out as a mixin so
TypstToHTML (in core.py) doesn't have to be one giant class -- this is
everything that scans raw text for a specific call shape, as opposed to
the block-level renderers (see block_renderers.py) that already have
their args_src handed to them by the main loop.
"""

import html
import re
from typing import Dict, List, Tuple

from ..math import convert_math
from .css_utils import (
    _align_css,
    _box_css,
    _pad_css,
    _parse_size,
    _parse_text_style_args,
    _place_css,
    _scale_factor,
)
from .patterns import _KNOWN_BRACKET_FUNCS, _LAYOUT_WRAP_NAMES, _SIMPLE_WRAP_TAGS
from .text_utils import _scan_call, _split_top_level


class InlineProcessorsMixin:
    # Type-only declarations: this mixin is never instantiated on its
    # own (see core.py's `TypstToHTML(BlockRenderersMixin,
    # InlineProcessorsMixin)`), which is where these are actually set
    # up (footnotes/footnote_counter/label_map in __init__, _inline as
    # a real method). Declaring them here just tells the type checker
    # what the host class is expected to provide, since it can't see
    # across the mixin boundary otherwise. The `_inline` stub is never
    # actually called -- Python's attribute resolution always checks
    # TypstToHTML's own namespace (where the real _inline lives) before
    # falling back to a mixin's, so `raise NotImplementedError` here is
    # dead code by construction, not a real fallback path.
    footnotes: List[Tuple[int, str]]
    footnote_counter: int
    label_map: Dict[str, Tuple[str, str]]

    def _inline(self, text: str) -> str:
        raise NotImplementedError

    def _process_bracket_functions(self, text, stash):
        out = []
        i = 0
        n = len(text)
        while i < n:
            idx = text.find("#", i)
            if idx == -1:
                out.append(text[i:])
                break
            m = re.match(r"#([a-zA-Z]+)\[", text[idx:])
            name = m.group(1) if m else None
            if not m or name not in _KNOWN_BRACKET_FUNCS:
                out.append(text[i : idx + 1])
                i = idx + 1
                continue

            out.append(text[i:idx])
            open_idx = idx + m.end()
            depth = 1
            j = open_idx
            while j < n and depth > 0:
                if text[j] == "[":
                    depth += 1
                elif text[j] == "]":
                    depth -= 1
                j += 1
            inner = text[open_idx : j - 1] if depth == 0 else text[open_idx:]

            if name == "footnote":
                self.footnote_counter += 1
                num = self.footnote_counter
                rendered_inner = self._inline(inner)
                self.footnotes.append(
                    (
                        num,
                        (
                            f'<li id="fn{num}">{rendered_inner} '
                            f'<a href="#fnref{num}" class="footnote-backref" '
                            f'aria-label="Back to content">\u21a9</a></li>'
                        ),
                    )
                )
                replacement = (
                    f'<sup id="fnref{num}" class="footnote-ref">'
                    f'<a href="#fn{num}">{num}</a></sup>'
                )
            elif name in ("upper", "lower"):
                transformed = inner.upper() if name == "upper" else inner.lower()
                replacement = html.escape(transformed, quote=False)
            else:
                tag, style = _SIMPLE_WRAP_TAGS[name]
                rendered_inner = self._inline(inner)
                attr = f' style="{style}"' if style else ""
                replacement = f"<{tag}{attr}>{rendered_inner}</{tag}>"

            out.append(stash(replacement))
            i = j
        return "".join(out)

    def _process_text_style(self, text, stash):
        out = []
        i = 0
        n = len(text)
        marker = "#text("
        while i < n:
            idx = text.find(marker, i)
            if idx == -1:
                out.append(text[i:])
                break
            out.append(text[i:idx])

            p = idx + len(marker)
            depth = 1
            in_str = False
            while p < n and depth > 0:
                c = text[p]
                if in_str:
                    if c == "\\":
                        p += 1
                    elif c == '"':
                        in_str = False
                else:
                    if c == '"':
                        in_str = True
                    elif c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                p += 1
            args_src = text[idx + len(marker) : p - 1]

            q = p
            while q < n and text[q] in " \t":
                q += 1
            if q >= n or text[q] != "[":
                out.append(text[idx:p])
                i = p
                continue

            bdepth = 1
            r = q + 1
            while r < n and bdepth > 0:
                if text[r] == "[":
                    bdepth += 1
                elif text[r] == "]":
                    bdepth -= 1
                r += 1
            inner = text[q + 1 : r - 1] if bdepth == 0 else text[q + 1 :]

            style = _parse_text_style_args(args_src)
            rendered_inner = self._inline(inner)
            attr = f' style="{style}"' if style else ""
            out.append(stash(f"<span{attr}>{rendered_inner}</span>"))
            i = r
        return "".join(out)

    def _process_raw_func(self, text, stash):
        """#raw("code", lang:, block:) -- args in ANY order (unlike the
        old fixed-order regex this replaces), via _split_top_level."""
        out = []
        i = 0
        n = len(text)
        marker = "#raw("
        while i < n:
            idx = text.find(marker, i)
            if idx == -1:
                out.append(text[i:])
                break
            out.append(text[i:idx])

            p = idx + len(marker)
            depth = 1
            in_str = False
            while p < n and depth > 0:
                c = text[p]
                if in_str:
                    if c == "\\":
                        p += 1
                    elif c == '"':
                        in_str = False
                else:
                    if c == '"':
                        in_str = True
                    elif c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                p += 1
            args_src = text[idx + len(marker) : p - 1]

            code = None
            lang = None
            is_block = False
            for part in _split_top_level(args_src, ","):
                part = part.strip()
                if not part:
                    continue
                m = re.match(r'^"((?:[^"\\]|\\.)*)"$', part, re.DOTALL)
                if m and code is None:
                    code = m.group(1).replace('\\"', '"').replace("\\\\", "\\")
                    continue
                m = re.match(r'^lang\s*:\s*"([^"]*)"$', part)
                if m:
                    lang = m.group(1)
                    continue
                m = re.match(r"^block\s*:\s*(true|false)$", part)
                if m:
                    is_block = m.group(1) == "true"
                    continue

            if code is None:
                out.append(text[idx:p])  # couldn't find a code string -- leave as-is
                i = p
                continue

            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            if is_block:
                out.append(stash(f"<pre><code{cls}>{html.escape(code)}</code></pre>"))
            else:
                out.append(stash(f"<code{cls}>{html.escape(code)}</code>"))
            i = p
        return "".join(out)

    def _process_layout_wraps(self, text, stash):
        """#align/#block/#box/#hide/#move/#pad/#place/#rotate/#scale/
        #skew/#columns/#repeat -- all take the shape `#name(args)[content]`
        or `#name[content]` and map onto inline CSS on a wrapping div/span."""
        out = []
        i = 0
        n = len(text)
        while i < n:
            idx = text.find("#", i)
            if idx == -1:
                out.append(text[i:])
                break
            m = re.match(r"#([a-zA-Z]+)", text[idx:])
            name = m.group(1) if m else None
            if not m or name not in _LAYOUT_WRAP_NAMES:
                out.append(text[i : idx + 1])
                i = idx + 1
                continue

            start_idx = idx + m.end()
            if start_idx >= n or text[start_idx] not in "([":
                out.append(text[i : idx + 1])
                i = idx + 1
                continue

            args_src, content_src, end = _scan_call(text, start_idx)
            if content_src is None:
                # No content block found -- can't safely wrap anything.
                out.append(text[i:end])
                i = end
                continue

            out.append(text[i:idx])
            rendered_inner = self._inline(content_src)
            replacement = self._render_layout_wrap(name, args_src or "", rendered_inner)
            out.append(stash(replacement))
            i = end
        return "".join(out)

    def _render_layout_wrap(self, name, args_src, inner_html):
        parts = _split_top_level(args_src, ",") if args_src else []
        named = {}
        positional = []
        for part in parts:
            p = part.strip()
            if not p:
                continue
            m = re.match(r"^([a-zA-Z-]+)\s*:\s*(.+)$", p, re.DOTALL)
            if m:
                named[m.group(1)] = m.group(2).strip()
            else:
                positional.append(p)

        if name == "align":
            target = positional[0] if positional else named.get("alignment", "")
            css = _align_css(target)
            return (
                f'<div style="{css}">{inner_html}</div>'
                if css
                else f"<div>{inner_html}</div>"
            )

        if name in ("block", "box"):
            css = _box_css(named)
            tag = "div" if name == "block" else "span"
            extra = "" if name == "block" else "display:inline-block; "
            return f'<{tag} style="{extra}{css}">{inner_html}</{tag}>'

        if name == "columns":
            count = positional[0] if positional else named.get("count", "2")
            count = re.sub(r"[^\d]", "", count) or "2"
            style = f"column-count: {count};"
            if "gutter" in named:
                g = _parse_size(named["gutter"])
                if g:
                    style += f" column-gap: {g};"
            return f'<div style="{style}">{inner_html}</div>'

        if name == "hide":
            return f'<span style="visibility:hidden;">{inner_html}</span>'

        if name == "move":
            dx = _parse_size(named.get("dx", "0pt")) or "0"
            dy = _parse_size(named.get("dy", "0pt")) or "0"
            return (
                f'<span style="position:relative; display:inline-block; '
                f'left:{dx}; top:{dy};">{inner_html}</span>'
            )

        if name == "pad":
            css = _pad_css(named, positional)
            return f'<div style="{css}">{inner_html}</div>'

        if name == "place":
            target = positional[0] if positional else ""
            css = _place_css(target, named)
            return f'<div style="{css}">{inner_html}</div>'

        if name == "rotate":
            angle = positional[0] if positional else named.get("angle", "0deg")
            return (
                f'<span style="display:inline-block; '
                f'transform: rotate({angle});">{inner_html}</span>'
            )

        if name == "scale":
            factor = positional[0] if positional else named.get("x", "100%")
            factor_css = _scale_factor(factor)
            return (
                f'<span style="display:inline-block; '
                f'transform: scale({factor_css});">{inner_html}</span>'
            )

        if name == "skew":
            ax = named.get("ax", "0deg")
            ay = named.get("ay", "0deg")
            return (
                f'<span style="display:inline-block; '
                f'transform: skew({ax}, {ay});">{inner_html}</span>'
            )

        if name == "repeat":
            # Typst repeats `content` to fill available space (e.g. dotted
            # leader lines) -- that needs real layout computation we don't
            # have, so render the content once rather than showing nothing
            # or broken syntax.
            return inner_html

        return inner_html

    def _resolve_ref(self, label):
        target = self.label_map.get(label)
        if not target:
            return None
        hid, display = target
        return (
            f'<a href="#{html.escape(hid, quote=True)}">'
            f"{html.escape(display, quote=False)}</a>"
        )

    def _process_math_equation(self, text, stash):
        """#math.equation(alt: "...", block: true/false, $ ... $) --
        Typst's accessibility-aware equation wrapper. Extracts alt/block
        and threads them into convert_math() as an aria-label / display
        mode. Must run BEFORE the generic $...$ math-span step, or that
        step would already have consumed the $ ... $ inside these parens."""
        out = []
        i = 0
        n = len(text)
        marker = "#math.equation("
        while i < n:
            idx = text.find(marker, i)
            if idx == -1:
                out.append(text[i:])
                break
            out.append(text[i:idx])

            p = idx + len(marker)
            depth = 1
            in_str = False
            while p < n and depth > 0:
                c = text[p]
                if in_str:
                    if c == "\\":
                        p += 1
                    elif c == '"':
                        in_str = False
                else:
                    if c == '"':
                        in_str = True
                    elif c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                p += 1
            args_src = text[idx + len(marker) : p - 1]

            alt_text = None
            block = None
            math_src = None
            for part in _split_top_level(args_src, ","):
                part = part.strip()
                if not part:
                    continue
                m = re.match(r'^alt\s*:\s*"((?:[^"\\]|\\.)*)"$', part, re.DOTALL)
                if m:
                    alt_text = m.group(1).replace('\\"', '"')
                    continue
                m = re.match(r"^block\s*:\s*(true|false)$", part)
                if m:
                    block = m.group(1) == "true"
                    continue
                m = re.match(r"^\$(.*)\$$", part, re.DOTALL)
                if m:
                    math_src = m.group(1)
                    continue
                # unrecognised named arg (numbering:, supplement:, ...) -- ignored.

            if math_src is None:
                out.append(text[idx:p])  # couldn't find the equation -- leave as-is
                i = p
                continue

            inner = math_src.strip()
            if block is None:
                block = math_src.startswith((" ", "\t")) and math_src.endswith(
                    (" ", "\t")
                )
            out.append(stash(convert_math(inner, display=block, alt=alt_text)))
            i = p
        return "".join(out)
