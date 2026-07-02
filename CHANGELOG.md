# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

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
  stripped rather than leaking as broken text -- important for `.typ`
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
