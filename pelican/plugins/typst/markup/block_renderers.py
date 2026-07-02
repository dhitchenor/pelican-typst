"""
Block-level renderers: tables, grids, stacks, figures, images, the
heading pre-pass (_collect_headings), and the outline. Split out as a
mixin so TypstToHTML (in core.py) doesn't have to be one giant class --
this is everything that turns a parsed block's args into a chunk of
HTML, as opposed to the inline text-substitution passes (see
inline_processors.py).
"""

import html
import re
from typing import List, Optional, Tuple

from .css_utils import _parse_size
from .numbering import _apply_numbering
from .outline_utils import _entries_to_tree, _render_outline_tree
from .patterns import (
    _HEADING_RE,
    _LABEL_SUFFIX_RE,
    _SET_HEADING_NUMBERING_RE,
    _TABLE_HEADER_RE,
)
from .text_utils import _split_top_level


class BlockRenderersMixin:
    # Type-only declarations -- see the matching comment in
    # inline_processors.py for why these exist and why the _inline
    # stub is safe dead code, never actually reached at runtime.
    heading_entries: List[Tuple[int, str, Optional[str], str]]

    def _inline(self, text: str) -> str:
        raise NotImplementedError

    def _scan_multiline_paren_call(self, lines, i, marker):
        """Scan a `marker(...)` call that may span multiple physical
        lines (paren-depth aware) -- used by #table/#grid/#stack/
        #set page, all of which are commonly written one cell/option
        per line. Returns (args_src, lines_consumed)."""
        remaining = "\n".join(lines[i:])
        start_idx = remaining.find(marker)
        args_start = start_idx + len(marker)
        depth = 1
        j = args_start
        in_str = False
        n = len(remaining)
        while j < n and depth > 0:
            c = remaining[j]
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
        args_src = (
            remaining[args_start : j - 1] if depth == 0 else remaining[args_start:]
        )
        consumed = remaining[:j] if depth == 0 else remaining
        lines_consumed = consumed.count("\n") + 1
        return args_src, lines_consumed

    def _collect_headings(self, text):
        """First pass: walk the (comment-stripped) document computing
        every heading's level/id/number/raw-text with NO side effects
        (no footnote registration, no recursive _inline calls) -- purely
        so forward references and the outline can be resolved before the
        real render pass gets to them. Returns (entries, label_map)
        where entries is [(level, id, number_or_None, raw_text), ...] in
        document order and label_map is {label: (id, ref_display_text)}."""
        entries = []
        label_map = {}
        pattern = None
        counters = [0] * 6
        auto_id_counter = 0

        for line in text.split("\n"):
            m = _SET_HEADING_NUMBERING_RE.match(line.strip())
            if m:
                val = m.group(1)
                pattern = None if val == "none" else val[1:-1]
                continue

            m = _HEADING_RE.match(line)
            if not m:
                continue

            level = min(len(m.group(1)), 6)
            raw_text = m.group(2)
            label = None
            lm = _LABEL_SUFFIX_RE.search(raw_text)
            if lm:
                label = lm.group(1)
                raw_text = raw_text[: lm.start()].rstrip()

            number = None
            if pattern:
                counters[level - 1] += 1
                for idx in range(level, 6):
                    counters[idx] = 0
                number = _apply_numbering(pattern, counters[:level])

            if label:
                hid = label
            else:
                auto_id_counter += 1
                hid = f"section-{auto_id_counter}"

            entries.append((level, hid, number, raw_text))
            if label:
                ref_display = number if number else raw_text.strip()
                label_map[label] = (hid, ref_display)

        return entries, label_map

    def _render_outline(self, args_src):
        title_html = "Contents"
        depth = None
        for part in _split_top_level(args_src, ","):
            p = part.strip()
            if not p:
                continue
            if re.match(r"^title\s*:\s*none$", p):
                title_html = None
                continue
            m = re.match(r"^title\s*:\s*\[(.*)\]$", p, re.DOTALL)
            if m:
                title_html = self._inline(m.group(1))
                continue
            m = re.match(r"^depth\s*:\s*(\d+)$", p)
            if m:
                depth = int(m.group(1))
                continue
            # other args (indent:, target:) -- not supported, ignored.

        display_entries = []
        for level, hid, number, raw_text in self.heading_entries:
            if depth and level > depth:
                continue
            label_text = html.escape(raw_text.strip(), quote=False)
            if number:
                label_text = f"{html.escape(number, quote=False)} {label_text}"
            display_entries.append((level, hid, label_text))

        tree = _entries_to_tree(display_entries)
        body = _render_outline_tree(tree)
        title_part = f"<h2>{title_html}</h2>" if title_html is not None else ""
        return f'<nav class="outline" role="doc-toc">{title_part}{body}</nav>'

    def _render_figure(self, args_src):
        """#figure(body, caption: [...]) -> <figure>. body can be
        image("path", ...), a bracket [...] content block, or a nested
        table(...) call. Works with or without a caption."""
        body_html = ""
        caption_html = None
        for part in _split_top_level(args_src, ","):
            p = part.strip()
            if not p:
                continue

            m = re.match(r"^caption\s*:\s*\[(.*)\]$", p, re.DOTALL)
            if m:
                caption_html = self._inline(m.group(1))
                continue

            m = re.match(r'^image\(\s*"([^"]+)"(?:\s*,.*)?\)$', p, re.DOTALL)
            if m:
                body_html = f'<img src="{html.escape(m.group(1))}" alt="">'
                continue

            m = re.match(r"^table\((.*)\)$", p, re.DOTALL)
            if m:
                body_html = self._render_table(m.group(1))
                continue

            if p.startswith("[") and p.endswith("]"):
                body_html = self._inline(p[1:-1])
                continue

            # Other named args (kind:, supplement:, numbering:, gap:,
            # placement:) -- recognised-and-ignored, not an error.

        result = f"<figure>{body_html}"
        if caption_html is not None:
            result += f"<figcaption>{caption_html}</figcaption>"
        result += "</figure>"
        return result

    def _render_image(self, args_src):
        """#image("path", width:, height:) -> <img>, with or without
        the extra sizing args."""
        src = None
        width = None
        height = None
        for part in _split_top_level(args_src, ","):
            p = part.strip()
            if not p:
                continue
            m = re.match(r'^"([^"]*)"$', p)
            if m and src is None:
                src = m.group(1)
                continue
            m = re.match(r"^width\s*:\s*(.+)$", p)
            if m:
                width = _parse_size(m.group(1).strip())
                continue
            m = re.match(r"^height\s*:\s*(.+)$", p)
            if m:
                height = _parse_size(m.group(1).strip())
                continue

        if src is None:
            return ""

        attrs = ""
        if width:
            attrs += f' width="{width}"'
        if height:
            attrs += f' height="{height}"'
        return f'<img src="{html.escape(src)}" alt=""{attrs}>'

    def _render_table(self, args_src):
        parts = _split_top_level(args_src, ",")
        columns = 1
        header_cells = []
        body_cells = []

        for part in parts:
            p = part.strip()
            if not p:
                continue

            m = re.match(r"^columns\s*:\s*(.+)$", p, re.DOTALL)
            if m:
                columns = self._parse_columns(m.group(1).strip())
                continue

            m = _TABLE_HEADER_RE.match(p)
            if m:
                for cell_part in _split_top_level(m.group(1), ","):
                    cp = cell_part.strip()
                    if cp.startswith("[") and cp.endswith("]"):
                        header_cells.append(self._inline(cp[1:-1]))
                continue

            if p.startswith("[") and p.endswith("]"):
                body_cells.append(self._inline(p[1:-1]))

        sections = []
        if header_cells:
            ths = "".join(f"<th>{c}</th>" for c in header_cells)
            sections.append(f"<thead><tr>{ths}</tr></thead>")

        body_rows = []
        for k in range(0, len(body_cells), columns):
            row = body_cells[k : k + columns]
            tds = "".join(f"<td>{c}</td>" for c in row)
            body_rows.append(f"<tr>{tds}</tr>")
        if body_rows:
            sections.append("<tbody>" + "".join(body_rows) + "</tbody>")

        return "<table>" + "".join(sections) + "</table>"

    def _render_grid(self, args_src):
        """#grid(columns:, gutter:/column-gutter:, [cell], [cell], ...)
        -> CSS Grid. Same shape as #table but without header semantics."""
        parts = _split_top_level(args_src, ",")
        columns = 1
        gap = None
        cells = []
        for part in parts:
            p = part.strip()
            if not p:
                continue
            m = re.match(r"^columns\s*:\s*(.+)$", p, re.DOTALL)
            if m:
                columns = self._parse_columns(m.group(1).strip())
                continue
            m = re.match(
                r"^(?:gutter|column-gutter|row-gutter)\s*:\s*(.+)$", p, re.DOTALL
            )
            if m:
                gap = _parse_size(m.group(1).strip())
                continue
            if p.startswith("[") and p.endswith("]"):
                cells.append(self._inline(p[1:-1]))
        style = f"display:grid; grid-template-columns: repeat({columns}, 1fr);"
        if gap:
            style += f" gap: {gap};"
        cells_html = "".join(f"<div>{c}</div>" for c in cells)
        return f'<div style="{style}">{cells_html}</div>'

    def _render_stack(self, args_src):
        """#stack(dir:, spacing:, [item], [item], ...) -> CSS flexbox.
        Typst's default stack direction is top-to-bottom."""
        parts = _split_top_level(args_src, ",")
        direction = "column"
        gap = None
        items = []
        for part in parts:
            p = part.strip()
            if not p:
                continue
            m = re.match(r"^dir\s*:\s*(.+)$", p)
            if m:
                d = m.group(1).strip()
                direction = "row" if d in ("ltr", "rtl") else "column"
                continue
            m = re.match(r"^spacing\s*:\s*(.+)$", p, re.DOTALL)
            if m:
                gap = _parse_size(m.group(1).strip())
                continue
            if p.startswith("[") and p.endswith("]"):
                items.append(self._inline(p[1:-1]))
        style = f"display:flex; flex-direction:{direction};"
        if gap:
            style += f" gap: {gap};"
        items_html = "".join(f"<div>{it}</div>" for it in items)
        return f'<div style="{style}">{items_html}</div>'

    def _parse_columns(self, value):
        if re.match(r"^\d+$", value):
            return max(1, int(value))
        if value.startswith("(") and value.endswith(")"):
            count = len(_split_top_level(value[1:-1], ","))
            return max(1, count)
        return 1

    def _render_code_block(self, code, lang):
        escaped = html.escape(code)
        cls = f' class="language-{html.escape(lang)}"' if lang else ""
        return f"<pre><code{cls}>{escaped}</code></pre>"
