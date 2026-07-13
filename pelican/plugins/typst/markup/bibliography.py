"""
Bibliography/citation handling: #bibliography((key: "entry", ...))
inline-dict parsing, #cite(<key>) numbered-citation rendering, and the
References section built from whatever was actually cited.

This is a self-contained stepping stone ahead of real external
BibTeX/Hayagriva file support (not yet implemented) -- see the
"Bibliography and citations" section of the README for the full
picture, including why numbering follows citation order rather than
dict order, and how a repeated citation avoids duplicate HTML ids.

State owned here (initialised/reset by TypstToHTML in core.py, same as
every other mixin's state):
- bibliography: dict of key -> already-inline-processed entry HTML
- citation_order: list of keys in first-citation order
- citation_index: key -> citation number (1-based)
- citation_first_seen: set of keys that have already claimed their
  backlink anchor id (see _cite_sub)
"""

import html

from ..metadata import _parse_value


class BibliographyMixin:
    def _parse_bibliography_args(self, args):
        """Parse a #bibliography((...)) call's raw argument source.

        If it's our own inline dict literal (reusing the exact same
        small literal parser #metadata() already uses), merge its
        entries into self.bibliography -- each value is run through
        _inline() so markup inside an entry (bold/italic/links/etc.)
        renders correctly, rather than showing as literal text.

        If it's anything else -- most notably a real Typst file-path
        call like #bibliography("refs.bib") -- silently do nothing.
        External bibliography-file import isn't implemented yet, so
        this is consumed cleanly rather than shown broken, same as
        before this mixin supported inline entries at all.
        """
        try:
            data, _ = _parse_value(args, 0)
            if isinstance(data, dict):
                self.bibliography.update(
                    {str(k): self._inline(str(v)) for k, v in data.items()}
                )
        except (ValueError, IndexError):
            pass

    def _cite_sub(self, m, stash):
        """Render a single #cite(<key>) match as a numbered, linked
        citation marker, called from _CITE_INLINE_RE.sub(...) inside
        _inline(). Numbering follows order of first appearance in the
        document, not bibliography-listing order; citing the same key
        again reuses its number and link target."""
        key = m.group(1)
        if key not in self.citation_index:
            self.citation_index[key] = len(self.citation_order) + 1
            self.citation_order.append(key)
        num = self.citation_index[key]
        if key not in self.citation_first_seen:
            self.citation_first_seen.add(key)
            id_attr = f' id="cite-ref-{num}"'
        else:
            # Same source cited again elsewhere -- still gets the same
            # [num] link, but only the first occurrence owns the
            # backlink anchor id, so a source cited more than once
            # doesn't produce duplicate HTML ids.
            id_attr = ""
        return stash(f'<sup{id_attr}><a href="#cite-{num}">[{num}]</a></sup>')

    def _render_references_section(self):
        """Build the trailing References section HTML from whatever
        was actually cited, in citation order. Returns "" (nothing
        appended to the body) if nothing was ever cited, same as an
        unused #bibliography((...)) dict producing no output at all."""
        if not self.citation_order:
            return ""
        ref_items = []
        for key in self.citation_order:
            num = self.citation_index[key]
            entry = self.bibliography.get(
                key, f"[unresolved citation key: {html.escape(key)}]"
            )
            ref_items.append(f'<li id="cite-{num}">{entry}</li>')
        return (
            '\n<section class="references" role="doc-bibliography">\n'
            "<h2>References</h2>\n"
            f"<ol>\n{chr(10).join(ref_items)}\n</ol>\n</section>"
        )
