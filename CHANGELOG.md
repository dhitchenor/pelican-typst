# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/).


## [1.0.4] - 2026-07-12

### Added

- **`#bibliography((key: "entry", ...))` and `#cite(<key>)`** -- a
  self-contained, hand-written stepping stone ahead of real external
  BibTeX/Hayagriva file support (planned separately). Authors write
  reference entries directly in the `.typ` file as an inline dict
  literal (reusing the same small literal parser `#metadata()` already
  uses), and cite them from the body with `#cite(<key>)`. Citations
  render as numbered, linked markers (`[1]`, `[2]`, ...) in order of
  first appearance in the document -- not bibliography-listing order --
  and a `References` section is appended after the footnotes section,
  listing only the entries actually cited. Citing the same source more
  than once reuses its number and link target; only the first
  occurrence gets a backlink anchor id, so a repeatedly-cited source
  doesn't produce duplicate HTML ids. An unresolved key (cited but with
  no matching bibliography entry) still renders its `[n]` marker with a
  visible fallback in the reference list, rather than crashing or
  silently vanishing.

  ```typst
  Typst compiles quickly #cite(<haug2022>).

  #bibliography((
    haug2022: "Haug, M. (2022). Fast Typesetting with Incremental Compilation. Thesis.",
  ))
  ```

  A real Typst file-path call, e.g. `#bibliography("refs.bib")`, is
  still recognised and silently discarded (not a dict literal, so
  there's nothing to render yet) rather than shown broken -- this is
  the gap that an actual BibTeX/Hayagriva import will eventually close.

### Testing

- Added a `TestInlineBibliography` class covering: numbered rendering
  instead of stripping, References section listing only cited entries,
  citation order (not dict order) determining numbering, repeated
  citations reusing a number without duplicate ids, graceful fallback
  for an unresolved key, and no References section at all when nothing
  is cited.
- Updated the one existing test that asserted the old "strip `#cite`
  entirely" behaviour, now that citations render.


## [1.0.3] - 2026-07-10

### Added

- **`#line(...)` now renders as an `<hr>` instead of falling through as
  literal, unprocessed text.** Previously there was no handling for this
  function at all, so something like:
  ```typst
  #line(length: 100%, stroke: 0.5pt + gray)
  ```
  would render as a stray paragraph containing the raw Typst source
  (`<p>#line(length: 100%, stroke: 0.5pt + gray)</p>`) instead of a
  horizontal rule. `length` maps to the `<hr>`'s width; `stroke` (a
  Typst `width + color` value, e.g. `0.5pt + gray`) maps to
  `border-top`. Both are optional, falling back to `100%` width and a
  `1pt solid currentColor` border when omitted. Registered as a proper
  block-start marker, so it's also correctly recognised standing on its
  own between paragraphs rather than being absorbed into a preceding or
  following paragraph's continuation lines.

### Testing

- Added a `TestLine` class in `test_markup_layout.py` covering: renders
  as `<hr>` rather than literal text, `length` sets width, `stroke`
  width/color are both applied, sensible defaults when called with no
  arguments, and correct block-boundary behaviour alongside surrounding
  paragraphs.


## [1.0.2] - 2026-07-09

### Fixed

- **Crash (`IndexError`) when an inline styling call (e.g. `#text(...)[...]`)
  was nested inside a layout wrap (`#align`, `#block`, `#box`, `#pad`,
  `#move`, `#place`, `#rotate`, `#scale`, `#skew`, `#columns`, `#hide`,
  `#repeat`).** `_inline()` ran `_process_bracket_functions` and
  `_process_text_style` *before* `_process_layout_wraps`, so any inline
  call textually nested inside a layout wrap's `[...]` content got
  stashed into the *outer* call's placeholder list first. When the
  layout-wrap processor then extracted that (already partially
  processed) content and recursively called `_inline()` on it, the
  recursive call started a fresh, empty placeholder list and could not
  resolve the leftover placeholder markers left behind by the outer
  call, raising `IndexError: list index out of range` in `restore()`.
  Fixed by running `_process_layout_wraps` first in the `_inline()`
  pipeline, so nested content stays as raw Typst source until its own
  independent recursive call fully resolves it.

  Example that previously crashed the build:
  ```typst
  #align(center)[
    #text(size: 22pt, weight: "bold")[Some title]
    #text(size: 10pt, fill: gray)[Some subtitle]
  ]
  ```

- **Multi-line bullet (`-`) and numbered (`+`) list items were split
  into separate single-item lists instead of one grouped `<ul>`/`<ol>`.**
  The list-collection loop in `convert()` only recognised a line as
  part of the current item if that exact physical line itself started
  with the `-`/`+` marker. A list item's wrapped continuation line
  (any real Typst list item long enough to span multiple lines) didn't
  match, silently ending the list early; the continuation text then
  fell through to the generic paragraph handler and rendered as a
  stray `<p>` between list fragments. The next `-`/`+` line started a
  *new* single-item list, which is why rendered numbered lists always
  showed "1." for every entry instead of incrementing, each item was
  its own separate one-item `<ol>`, not a numbering defect. Fixed by
  having each item absorb subsequent non-blank lines that aren't
  themselves a new marker or another block-start (heading, fence,
  etc.), same continuation logic already used by paragraph handling.

  Example that previously rendered as three separate lists with stray
  paragraphs in between:
  ```typst
  + *First item.* This is a longer explanation that
    wraps onto a second physical line.
  + *Second item.* Also wraps onto
    another line here.
  ```

### Testing

- Added regression tests covering both fixes (nested inline-style-in-
  layout-wrap; multi-line bullet and numbered list items), following
  the existing convention of pinning real bugs found during development
  in place as regressions.
- Re-verified all 9 bundled `examples/*.typ` files convert without
  errors or leftover stash placeholders.


## [1.0.1] - 2026-07-04

Initial release.

### Core

- `TypstReader(BaseReader)` -- registers `.typ` as a Pelican source
  format via `readers_init`, same mechanism Pelican's own Markdown/RST
  readers use.
- Pure Python throughout -- no `typst` binary, no PDF generation step,
  no `pyyaml` (front matter is parsed by a small bundled YAML-subset
  parser, `simpleyaml.py`).
- Namespace-package layout (`pelican.plugins.typst`) per Pelican's
  documented plugin structure -- auto-discovered when installed
  normally, or explicit via `PLUGINS = ["typst"]`.

### Metadata

- Two auto-detected styles: YAML front matter, or a native Typst
  `#metadata((...))` dict literal -- pick per file, both feed the same
  pipeline.

### Body markup

- Headings, bullet/numbered/term lists, fenced and inline code, bold/
  italic (shorthand and function forms), links, images, figures
  (image, table, or arbitrary content; caption optional), block quotes
  (with optional attribution), tables, grids, stacks.
- Footnotes, with full recursive inline processing inside the note
  (math, links, formatting all work).
- Text styling: highlight, strike, underline, overline, smallcaps, sub/
  superscript, upper/lower, `#text()` styling, `#raw()` (any argument
  order), manual linebreaks, automatic smart quotes.
- Cross-references (`@label` / `#ref(<label>)`) resolve correctly
  whether the label is defined before *or after* the reference point,
  via a side-effect-free pre-pass over the document.
- `#outline()` builds a properly nested table of contents from every
  heading in the document.
- `#numbering()` pattern formatter (arabic/alpha/roman/star, including
  alphabet rollover and the "last group repeats" rule) and `#set
  heading(numbering:)` auto-numbering, sharing the same algorithm.
- `#let` literal bindings (string/number/bool) are tracked and
  substituted at later reference points; unresolvable cases (function
  definitions, expressions, forward references) degrade to visibly
  broken text rather than silently disappearing, by design.
- 14 layout functions mapped to real CSS (`align`, `block`, `box`,
  `pad`, `move`, `place`, `rotate`, `scale`, `skew`, `columns`, `hide`,
  `grid`, `stack`, `h`/`v`).
- `#lorem()` placeholder text from a bundled word pool.
- PDF/print-only constructs with no meaning on a scrolling web page
  (`#set page(...)`, `#pagebreak()`, `#colbreak()`), plus constructs
  needing real evaluation we don't attempt (`#set` rules generally,
  `#import`, `#bibliography`, `#cite`), are recognised and silently
  stripped rather than leaking as broken text; important for `.typ`
  files that are also compiled to PDF from the same source.

### Math

- Full custom tokenizer/parser producing a shared AST, rendered to both
  MathML (primary) and LaTeX (embedded as a `<semantics>` annotation
  and a hidden fallback span, restored by `mathml-fallback.js` via a
  real feature test if the browser can't render MathML).
- Covers every item in Typst's own math reference category: symbols,
  fractions, roots, matrices, big operators, accents, primes, alphabet
  styles (`bb`/`cal`/`frak`/... via real Unicode Mathematical
  Alphanumeric Symbols, with the known Letterlike-block exceptions
  handled), `cancel`, sizing overrides, `overbrace`/`underbrace`, and
  `#math.equation(alt:)` accessibility text -> `aria-label`.
- Malformed equations degrade to plain text rather than breaking the
  build.

### Known gaps (see README "Limitations" for the full, current list)

- Bibliographies are not implemented (calls are stripped cleanly rather
  than rendered).
- Nested/multi-line list items, `layout()`/`measure()` (architecturally
  impossible for a static converter), and equation numbering are not
  supported.

### Internal

- `markup.py` split into a package (`patterns`, `numbering`, `lorem`,
  `text_utils`, `css_utils`, `outline_utils`, `block_renderers`,
  `inline_processors`, `core`) instead of one ~1600-line file.
- `tests/` added: unit coverage for math, numbering, metadata, and
  markup, plus a smoke test that runs every example through the real
  reader.
- CI runs the test suite across Python 3.8-3.12.
