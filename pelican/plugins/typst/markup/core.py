"""
TypstToHTML: the main entry point, combining the mixins
(BlockRenderersMixin, InlineProcessorsMixin, BibliographyMixin) with
the document-level state and the two central methods:

- convert(text): the line-based main loop that walks the document
  block by block.
- _inline(text): the pipeline of substitution passes applied to any
  already-joined chunk of text (a paragraph, heading, table cell, ...).

See the package docstring in __init__.py for the overall design notes
(two-pass heading/label resolution, PDF-only constructs being silently
stripped, etc.).
"""

import html
import re

from ..math import convert_math
from .block_renderers import BlockRenderersMixin
from .bibliography import BibliographyMixin
from .css_utils import _parse_size, _parse_stroke
from .inline_processors import InlineProcessorsMixin
from .lorem import _generate_lorem
from .numbering import _apply_numbering
from .patterns import (
    _AT_LABEL_RE,
    _BIBLIOGRAPHY_START_RE,
    _BR_SENTINEL,
    _BULLET_RE,
    _CITE_INLINE_RE,
    _COLBREAK_INLINE_RE,
    _COLBREAK_RE,
    _DISPLAY_MATH_LINE_RE,
    _FENCE_RE,
    _FIGURE_START_RE,
    _GRID_START_RE,
    _H_FUNC_RE,
    _HASH_REF_RE,
    _HEADING_RE,
    _IMAGE_START_RE,
    _IMPORT_START_RE,
    _LABEL_SUFFIX_RE,
    _LET_ANY_RE,
    _LET_LITERAL_RE,
    _LINE_FUNC_RE,
    _LOREM_RE,
    _NUMBERED_RE,
    _NUMBERING_RE,
    _OUTLINE_RE,
    _PAGEBREAK_INLINE_RE,
    _PAGEBREAK_RE,
    _PLACEHOLDER,
    _QUOTE_START_RE,
    _REF_FUNC_RE,
    _SET_ANY_START_RE,
    _SET_HEADING_NUMBERING_RE,
    _STACK_START_RE,
    _TABLE_START_RE,
    _TERMS_RE,
    _V_FUNC_RE,
)
from .text_utils import (
    _join_with_linebreaks,
    _looks_like_block_start,
    _parse_let_literal,
    _scan_call,
    _smartquotes,
    _split_top_level,
    _strip_comments,
)


class TypstToHTML(BlockRenderersMixin, InlineProcessorsMixin, BibliographyMixin):
    def __init__(self):
        self.footnotes = []
        self.footnote_counter = 0
        self.heading_numbering_pattern = None
        self.heading_entries = []
        self.label_map = {}
        self._heading_entry_idx = 0
        self.let_bindings = {}
        self.bibliography = {}
        self.citation_order = []
        self.citation_index = {}
        self.citation_first_seen = set()

    def convert(self, text):
        self.footnotes = []
        self.footnote_counter = 0
        self.heading_numbering_pattern = None
        self._heading_entry_idx = 0
        self.let_bindings = {}
        self.bibliography = {}
        self.citation_order = []
        self.citation_index = {}
        self.citation_first_seen = set()

        text = _strip_comments(text)
        self.heading_entries, self.label_map = self._collect_headings(text)

        lines = text.split("\n")
        i = 0
        n = len(lines)
        out = []

        while i < n:
            line = lines[i]

            if line.strip() == "":
                i += 1
                continue

            fence = _FENCE_RE.match(line.strip())
            if fence:
                lang = fence.group(1)
                i += 1
                code_lines = []
                while i < n and lines[i].strip() != "```":
                    code_lines.append(lines[i])
                    i += 1
                i += 1
                out.append(self._render_code_block("\n".join(code_lines), lang))
                continue

            m = _SET_HEADING_NUMBERING_RE.match(line.strip())
            if m:
                val = m.group(1)
                self.heading_numbering_pattern = None if val == "none" else val[1:-1]
                i += 1
                continue

            # PDF/print-only constructs, and scripting/reference-file
            # constructs we can't evaluate (imports, bibliographies) --
            # all silently consumed (no output) rather than leaking into
            # the page as broken text. Common in .typ files that are also
            # compiled to PDF, or that import shared templates, from the
            # same source. Checked *after* the heading-numbering case
            # above, since that #set call is semantically meaningful here
            # and every other #set(...) call isn't.
            if set_match := _SET_ANY_START_RE.match(line.strip()):
                marker = set_match.group(0)
                _args, consumed = self._scan_multiline_paren_call(lines, i, marker)
                i += consumed
                continue

            if _IMPORT_START_RE.match(line.strip()):
                i += 1
                continue

            if _BIBLIOGRAPHY_START_RE.match(line.strip()):
                args, consumed = self._scan_multiline_paren_call(
                    lines, i, "#bibliography("
                )
                self._parse_bibliography_args(args)
                i += consumed
                continue

            if _LET_ANY_RE.match(line.strip()):
                # The binding line itself never renders in real Typst
                # either way. If it's a simple literal assignment
                # (string/number/bool), also store it so later bare
                # #name references can be substituted -- function
                # definitions and complex expressions still can't be
                # resolved, so references to THOSE stay honestly broken
                # rather than silently vanishing.
                m = _LET_LITERAL_RE.match(line.strip())
                if m:
                    literal = _parse_let_literal(m.group(2))
                    if literal is not None:
                        self.let_bindings[m.group(1)] = literal
                i += 1
                continue

            if _PAGEBREAK_RE.match(line.strip()) or _COLBREAK_RE.match(line.strip()):
                i += 1
                continue

            m = _V_FUNC_RE.match(line.strip())
            if m:
                size = _parse_size(m.group(1).strip())
                if size:
                    out.append(f'<div style="height:{size};"></div>')
                i += 1
                continue

            m = _LINE_FUNC_RE.match(line.strip())
            if m:
                named = {}
                for part in _split_top_level(m.group(1), ",") if m.group(1) else []:
                    p = part.strip()
                    if not p:
                        continue
                    km = re.match(r"^([a-zA-Z-]+)\s*:\s*(.+)$", p, re.DOTALL)
                    if km:
                        named[km.group(1)] = km.group(2).strip()
                length = _parse_size(named.get("length", "100%")) or "100%"
                border = _parse_stroke(named["stroke"]) if "stroke" in named else "1pt solid currentColor"
                out.append(
                    f'<hr style="width:{length}; border:none; '
                    f'border-top:{border}; margin:1em 0;">'
                )
                i += 1
                continue

            m = _HEADING_RE.match(line)
            if m:
                level = min(len(m.group(1)), 6)
                raw_text = m.group(2)
                lm = _LABEL_SUFFIX_RE.search(raw_text)
                if lm:
                    raw_text = raw_text[: lm.start()].rstrip()
                heading_html = self._inline(raw_text)
                _lvl, entry_id, entry_number, _raw = self.heading_entries[
                    self._heading_entry_idx
                ]
                self._heading_entry_idx += 1
                if entry_number:
                    heading_html = (
                        f"{html.escape(entry_number, quote=False)} {heading_html}"
                    )
                out.append(
                    f'<h{level} id="{html.escape(entry_id, quote=True)}">'
                    f"{heading_html}</h{level}>"
                )
                i += 1
                continue

            if _BULLET_RE.match(line):
                items = []
                while i < n and (bullet_match := _BULLET_RE.match(lines[i])):
                    item_lines = [bullet_match.group(1)]
                    i += 1
                    while (
                        i < n
                        and lines[i].strip() != ""
                        and not _BULLET_RE.match(lines[i])
                        and not _looks_like_block_start(lines[i])
                    ):
                        item_lines.append(lines[i])
                        i += 1
                    items.append(_join_with_linebreaks(item_lines))
                out.append(
                    "<ul>"
                    + "".join(f"<li>{self._inline(it)}</li>" for it in items)
                    + "</ul>"
                )
                continue

            if _NUMBERED_RE.match(line):
                items = []
                while i < n and (numbered_match := _NUMBERED_RE.match(lines[i])):
                    item_lines = [numbered_match.group(1)]
                    i += 1
                    while (
                        i < n
                        and lines[i].strip() != ""
                        and not _NUMBERED_RE.match(lines[i])
                        and not _looks_like_block_start(lines[i])
                    ):
                        item_lines.append(lines[i])
                        i += 1
                    items.append(_join_with_linebreaks(item_lines))
                out.append(
                    "<ol>"
                    + "".join(f"<li>{self._inline(it)}</li>" for it in items)
                    + "</ol>"
                )
                continue

            if _QUOTE_START_RE.match(line.strip()):
                remaining = "\n".join(lines[i:])
                marker_pos = remaining.find("#quote") + len("#quote")
                args_src, content_src, end = _scan_call(remaining, marker_pos)
                if content_src is not None:
                    attribution_html = None
                    for part in _split_top_level(args_src or "", ","):
                        p = part.strip()
                        m = re.match(r"^attribution\s*:\s*\[(.*)\]$", p, re.DOTALL)
                        if m:
                            attribution_html = self._inline(m.group(1))
                            continue
                        m = re.match(
                            r'^attribution\s*:\s*"((?:[^"\\]|\\.)*)"$', p, re.DOTALL
                        )
                        if m:
                            attribution_html = html.escape(m.group(1), quote=False)
                    quote_html = f"<blockquote><p>{self._inline(content_src)}</p>"
                    if attribution_html:
                        quote_html += f"<footer>\u2014 {attribution_html}</footer>"
                    quote_html += "</blockquote>"
                    out.append(quote_html)
                    i += remaining[:end].count("\n") + 1
                    continue
                # else: couldn't parse -- fall through to paragraph handling

            if _FIGURE_START_RE.match(line.strip()):
                args_src, consumed = self._scan_multiline_paren_call(
                    lines, i, "#figure("
                )
                out.append(self._render_figure(args_src))
                i += consumed
                continue

            if _IMAGE_START_RE.match(line.strip()):
                args_src, consumed = self._scan_multiline_paren_call(
                    lines, i, "#image("
                )
                out.append(self._render_image(args_src))
                i += consumed
                continue

            if _TABLE_START_RE.match(line.strip()):
                args_src, consumed = self._scan_multiline_paren_call(
                    lines, i, "#table("
                )
                out.append(self._render_table(args_src))
                i += consumed
                continue

            if _GRID_START_RE.match(line.strip()):
                args_src, consumed = self._scan_multiline_paren_call(lines, i, "#grid(")
                out.append(self._render_grid(args_src))
                i += consumed
                continue

            if _STACK_START_RE.match(line.strip()):
                args_src, consumed = self._scan_multiline_paren_call(
                    lines, i, "#stack("
                )
                out.append(self._render_stack(args_src))
                i += consumed
                continue

            if _TERMS_RE.match(line):
                items = []
                while i < n and (terms_match := _TERMS_RE.match(lines[i])):
                    content = terms_match.group(1)
                    term, _sep, desc = content.partition(":")
                    items.append((term.strip(), desc.strip()))
                    i += 1
                parts = [
                    f"<dt>{self._inline(term)}</dt><dd>{self._inline(desc)}</dd>"
                    for term, desc in items
                ]
                out.append("<dl>" + "".join(parts) + "</dl>")
                continue

            m = _OUTLINE_RE.match(line.strip())
            if m:
                out.append(self._render_outline(m.group(1)))
                i += 1
                continue

            if _DISPLAY_MATH_LINE_RE.match(line.strip()):
                out.append(convert_math(line.strip()[1:-1], display=True))
                i += 1
                continue

            para_lines = [line]
            i += 1
            while (
                i < n
                and lines[i].strip() != ""
                and not _looks_like_block_start(lines[i])
            ):
                para_lines.append(lines[i])
                i += 1
            out.append(f"<p>{self._inline(_join_with_linebreaks(para_lines))}</p>")

        body = "\n".join(out)

        if self.footnotes:
            items = "\n".join(html_str for _, html_str in sorted(self.footnotes))
            body += (
                '\n<section class="footnotes" role="doc-endnotes">\n<hr>\n'
                f"<ol>\n{items}\n</ol>\n</section>"
            )

        body += self._render_references_section()

        return body

    def _inline(self, text):
        placeholders = []

        def stash(rendered):
            placeholders.append(rendered)
            return _PLACEHOLDER.format(len(placeholders) - 1)

        # Verbatim/code content must be protected before ANY other pass
        # scans the text -- otherwise something like `#align(x)[y]`
        # sitting inertly inside a code span or #raw() gets misread as a
        # real layout wrap (or bracket function, etc.) by a later pass,
        # corrupting the span instead of leaving it as literal text.
        text = self._process_raw_func(text, stash)

        def code_sub(m):
            return stash(f"<code>{html.escape(m.group(1))}</code>")

        text = re.sub(r"`([^`]+)`", code_sub, text)

        text = self._process_layout_wraps(text, stash)
        text = self._process_bracket_functions(text, stash)
        text = self._process_text_style(text, stash)
        text = self._process_math_equation(text, stash)

        # #link("url")[text]'s URL argument is opaque data, same as a
        # code span -- it must never be re-scanned for Typst syntax (a
        # URL fragment like "...#download" would otherwise get misread
        # as a bare #hash-reference by _HASH_REF_RE below, corrupting
        # the URL). This has to run *after* the layout-wrap/bracket-
        # function/text-style passes above, though, not before them --
        # those recursively call _inline() on their own nested content
        # (e.g. #footnote[...See #link(...)[...]...]), and each such
        # recursive call needs to see its own #link(...) call intact so
        # it can resolve it within its own self-contained placeholder
        # list, rather than having the outer call consume it first and
        # leave an unresolvable stash marker behind for the inner call
        # to choke on.
        def link_sub(m):
            url = html.escape(m.group(1))
            link_text = self._inline(m.group(2))
            return stash(f'<a href="{url}">{link_text}</a>')

        text = re.sub(r'#link\("([^"]+)"\)\[([^\]]*)\]', link_sub, text)

        def numbering_sub(m):
            pattern = m.group(1)
            numbers = [int(x.strip()) for x in m.group(2).split(",") if x.strip()]
            formatted = _apply_numbering(pattern, numbers)
            return stash(html.escape(formatted, quote=False))

        text = _NUMBERING_RE.sub(numbering_sub, text)

        def lorem_sub(m):
            n = int(m.group(1))
            return stash(html.escape(_generate_lorem(n), quote=False))

        text = _LOREM_RE.sub(lorem_sub, text)

        text = _CITE_INLINE_RE.sub(lambda m: self._cite_sub(m, stash), text)

        def hash_ref_sub(m):
            name = m.group(1)
            if name in self.let_bindings:
                return stash(html.escape(self.let_bindings[name], quote=False))
            # Unresolved -- still stash (don't just return the raw text),
            # so a name containing '_' (very common in real Typst
            # snake_case variable names) can't get misread as italic
            # shorthand by the *..*/_.._  passes later in this pipeline.
            return stash(html.escape(m.group(0), quote=False))

        text = _HASH_REF_RE.sub(hash_ref_sub, text)

        def ref_func_sub(m):
            resolved = self._resolve_ref(m.group(1))
            return stash(resolved) if resolved else m.group(0)

        text = _REF_FUNC_RE.sub(ref_func_sub, text)

        if _BR_SENTINEL in text:
            br = stash("<br>")
            text = text.replace(_BR_SENTINEL, br)
        text = re.sub(r"#linebreak\([^)]*\)", lambda m: stash("<br>"), text)

        # Inline fallbacks for pagebreak/colbreak (block-level handling in
        # the main loop catches the common own-line case; this catches
        # the rarer mid-paragraph usage) -- silently stripped either way.
        text = _PAGEBREAK_INLINE_RE.sub(lambda m: stash(""), text)
        text = _COLBREAK_INLINE_RE.sub(lambda m: stash(""), text)

        def h_sub(m):
            size = _parse_size(m.group(1).strip())
            if size:
                return stash(
                    f'<span style="display:inline-block; width:{size};"></span>'
                )
            return stash(
                ""
            )  # e.g. fr-unit spacing -- no clean equivalent, drop silently

        text = _H_FUNC_RE.sub(h_sub, text)

        def math_sub(m):
            inner = m.group(1)
            display = inner.startswith((" ", "\t")) and inner.endswith((" ", "\t"))
            return stash(convert_math(inner, display=display))

        text = re.sub(r"\$([^$]+)\$", math_sub, text)

        text = html.escape(text, quote=False)

        def at_label_sub(m):
            resolved = self._resolve_ref(m.group(1))
            return stash(resolved) if resolved else m.group(0)

        text = _AT_LABEL_RE.sub(at_label_sub, text)

        text = _smartquotes(text)

        text = re.sub(r"\*([^*\n]+)\*", r"<strong>\1</strong>", text)
        text = re.sub(r"_([^_\n]+)_", r"<em>\1</em>", text)

        def restore(m):
            return placeholders[int(m.group(1))]

        text = re.sub(r"\x00P(\d+)\x00", restore, text)

        return text
