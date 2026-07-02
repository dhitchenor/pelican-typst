"""
Typst body markup -> HTML.

This covers a "markdown-equivalent subset" of Typst: headings (with
optional auto-numbering and labels), bullet/numbered/term lists, fenced
code blocks, inline code, bold/italic, links, images, figures, tables,
grids, stacks, layout wrappers (align/block/box/pad/move/rotate/scale/
skew/place/hide/columns), block quotes, footnotes, text styling,
linebreaks, automatic smart quotes, cross-references, a table-of-
contents outline, and inline/display math (delegated to math.py). It
is a line-based converter, not a full Typst evaluator -- arbitrary
Typst code (`#let`, `#for`, custom functions, imports, etc.) is
intentionally out of scope and will be passed through as literal text
rather than executed.

A handful of Typst constructs are meaningful for PDF/print output but
have no equivalent in a continuously-scrolling web page (there are no
"pages" to break between, no page margins to set, and no way to
pre-compute layout the way `layout()`/`measure()`/`repeat()` need).
Since real-world .typ files are often compiled to BOTH a PDF (via
`typst compile`) and this HTML pipeline from the same source, those
constructs are deliberately recognised and silently stripped (produce
no output) rather than leaking into the page as broken literal text --
see `_SET_ANY_START_RE`, `_PAGEBREAK_RE`, `_COLBREAK_RE` in patterns.py.

Cross-references (`@label`, `#ref(<label>)`) need to work even when the
label is defined *later* in the document than where it's referenced, so
`convert()` runs a lightweight first pass (`_collect_headings`) that
walks the document computing every heading's id/number without any
side effects, before the real line-by-line render pass runs.

Package layout, for whoever's debugging this later:
    patterns.py            all regex/lookup constants, single source of truth
    numbering.py            numbering-pattern formatting algorithm
    lorem.py                  #lorem() word-pool loader
    text_utils.py               generic string parsing (arg splitting, call
                                  scanning, comments, smart quotes, #let literals)
    css_utils.py                  Typst-value -> CSS mapping (colors, sizes,
                                    weights, layout-wrapper CSS builders)
    outline_utils.py                flat heading list -> nested <ul> tree
    block_renderers.py                mixin: tables/grids/stacks/figures/
                                        images/heading-collection/outline
    inline_processors.py                mixin: the #name(...) substitution
                                          passes used inside _inline()
    core.py                               TypstToHTML: state + convert() +
                                            _inline(), combines both mixins
"""

from .core import TypstToHTML

__all__ = ["TypstToHTML"]
