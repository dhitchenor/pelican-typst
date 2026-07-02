# pelican-typst

A Pelican reader plugin that converts `.typ` (Typst) source files into
HTML, the same way Pelican natively handles `.md` and `.rst` files.

No Typst installation is required. This does **not** shell out to the
`typst` compiler and does **not** produce a PDF anywhere in the pipeline
-- it reads the Typst source text directly in Python and converts it,
the same way `python-markdown` reads Markdown text directly.

Because of that, it supports a **markdown-equivalent subset** of Typst
(headings, lists, code, emphasis, links, images/figures, quotes, and
math) rather than the full Typst language (no `#let`, `#for`, custom
functions, imports, etc.). See "Limitations" below.

## Install

On PyPI:

```bash
pip install pelican-typst
```

Then enable it in `pelicanconf.py`:

```python
PLUGINS = ["typst"]
```

(Pelican also auto-discovers installed namespace plugins if `PLUGINS`
is left unset entirely -- but the explicit form above is recommended:
it's obvious from your config what's enabled, and it's the one form
that works no matter how the plugin was installed, including editable
installs during development.)

That's it -- no dependencies beyond Pelican itself. Front matter parsing
and everything else here is pure Python; no `pyyaml`, no `typst`
binary required.

**Developing the plugin itself?** See `CONTRIBUTING.md` -- in
particular, editable installs (`pip install -e .`) need `PLUGINS`
set explicitly, since Pelican's auto-discovery can't see them.

<details>
<summary>Other ways to install (latest unreleased code, standalone wheel, offline)</summary>

**Latest code from GitHub**, if you want something not in a tagged
release yet:

```bash
pip install git+https://github.com/dhitchenor/pelican-typst.git
```

Or clone first if you'd rather have the source on disk:

```bash
git clone https://github.com/dhitchenor/pelican-typst.git
cd pelican-typst
pip install .
```

**A standalone wheel file**, to hand to someone without pointing them
at PyPI or a source tree at all (e.g. an offline/air-gapped install):

```bash
pip install build
python -m build            # produces dist/pelican_typst-1.0.1-py3-none-any.whl
pip install dist/pelican_typst-1.0.1-py3-none-any.whl
```

</details>

## Testing

```bash
pip install .[test]
pytest tests/ -v
```

167 tests across math, numbering, metadata/YAML parsing, and every
markup feature (footnotes, tables/grids/stacks, all 14 layout
functions, cross-references/outline, `#let` bindings, `#lorem()`, and
the constructs that are recognised-and-stripped rather than shown
broken). Several tests exist specifically to pin real bugs found during
development in place as regressions -- e.g. a regex-backtracking issue
that corrupted `` `#metadata()` `` inside an inline code span, and an
unresolved `#name` reference with an underscore getting misread as
italic shorthand by a later pass. If either of those ever starts
failing again, something regressed.

There's also a smoke test (`test_examples_smoke.py`) that runs every
file in `examples/` through the real `TypstReader` -- the same object
Pelican itself instantiates -- checking both that nothing raises and
that no unrestored stash placeholder (a literal null byte) leaks into
the output. That specific failure mode is what actually broke RSS/Atom
feed generation once during development (`UnserializableContentError:
Control characters are not supported in XML 1.0`) -- pytest alone
wouldn't necessarily catch that class of bug, since it only shows up
once Pelican's own feed generator gets involved, which is why CI (see
below) also does a full end-to-end site build on top of the unit tests.

### CI

`.github/workflows/tests.yml` runs on every push/PR: the full pytest
suite across Python 3.8 through 3.12 (via a real `pip install .`, not
editable -- catches packaging/namespace-discovery issues the tests
themselves can't see), plus a separate job that builds an actual
Pelican site from every example file and checks the generated HTML for
leftover placeholders, mirroring the manual verification this plugin
was built against throughout development.

## Metadata: two supported styles, auto-detected

You can use whichever you prefer, per file -- the reader detects which
one you used and there is nothing to configure.

**YAML front matter**, exactly like Pelican's Markdown reader:

```typst
---
title: My First Post
date: 2026-06-01
tags: [typst, pelican, python]
category: Programming
slug: my-first-post
authors: [Your Name]
summary: A short summary of the post.
---
= Body starts here
```

**Native Typst dictionary**, if you'd rather the file stay 100% valid
Typst (e.g. so `typst compile` elsewhere on the same source doesn't choke
on non-Typst syntax):

```typst
#metadata((
  title: "My First Post",
  date: "2026-06-01",
  tags: ("typst", "pelican", "python"),
  category: "Programming",
  slug: "my-first-post",
  authors: ("Your Name",),
  summary: "A short summary of the post.",
))

= Body starts here
```

The `#metadata()` form supports strings, numbers, booleans, `none`,
arrays, and nested dicts -- it's a small literal parser, not a full
Typst evaluator, so values must be literal (no `#let` references,
function calls, computed dates, etc.).

Recognised metadata keys are whatever your Pelican settings already
recognise (`title`, `date`, `modified`, `tags`, `category`, `slug`,
`authors`, `summary`, `status`, and any custom fields you've configured).

## Body markup supported

| Typst                              | Renders as                          |
|-------------------------------------|--------------------------------------|
| `= Heading` / `== Sub` / ...        | `<h1>` .. `<h6>` (depth capped at 6) |
| `- item`                            | `<ul><li>`                           |
| `+ item`                            | `<ol><li>`                           |
| `` ```lang ... ``` ``               | `<pre><code class="language-lang">`  |
| `` `code` ``                        | `<code>`                             |
| `*bold*`                            | `<strong>`                           |
| `_italic_`                          | `<em>`                               |
| `#link("url")[text]`                | `<a href="url">text</a>`             |
| `#quote[text]` or `#quote(attribution:)[text]`  | `<blockquote><p>` with optional `<footer>` |
| `#strong[..]` / `#emph[..]`          | function forms, alongside `*..*`/`_.._` shorthand |
| `#figure(image(...)|table(...)|[content], caption:)` | `<figure>`, caption optional, body can be an image, a table, or arbitrary content |
| `#image("path", width:, height:)`     | `<img>`, sizing args optional             |
| `#raw("code", lang:, block:)` (any arg order) | `<code>` or `<pre><code>`         |
| `#lorem(n)`                            | n words of bundled placeholder text (own data file, not Typst's exact algorithm) |
| `#let name = "value"` / `= 123` / `= true`  | binding line stripped; later bare `#name` references substituted |
| `text#footnote[note]`                | superscript ref + endnote list       |
| `#highlight[text]`                    | `<mark>`                             |
| `#strike[text]`                        | `<s>`                                |
| `#underline[text]`                      | `<u>`                               |
| `#overline[text]`                        | `<span style="text-decoration: overline">` |
| `#smallcaps[text]`                        | `<span style="font-variant: small-caps">` |
| `#sub[text]` / `#super[text]`               | `<sub>` / `<sup>` (text-level, distinct from math sub/sup) |
| `#upper[text]` / `#lower[text]`               | case-transformed, plain text only (no nested markup, see note below) |
| `#text(fill:, size:, weight:, style:, font:)[text]` | `<span style="...">`, best-effort CSS mapping |
| `` `code` ``                                            | `<code>` (shorthand, unchanged)      |
| `\` at end of a line                                      | `<br>`                               |
| `#linebreak()`                                              | `<br>`                               |
| straight `"`/`'` quotes                                       | automatic typographic curly quotes/apostrophes |
| `#table(columns:, table.header([..]), [cell], ...)`             | `<table>` with optional `<thead>`      |
| `/ Term: Description`                                             | `<dl><dt>`/`<dd>`                    |
| `#numbering("1.1.1", n1, n2, ...)`                                  | formatted numbering string           |
| `#set heading(numbering: "1.1.1")`                                    | auto-numbered headings from that point on |
| `= Heading <label>`                                                     | `id="label"` on the `<hN>` tag       |
| `@label` / `#ref(<label>)`                                                | cross-reference link, resolves forward or backward |
| `#outline()`                                                                | nested `<nav><ul>` table of contents |
| `#align(pos)[..]`, `#block[..]`, `#box[..]`, `#pad[..]`, `#move[..]`, `#place[..]`, `#rotate[..]`, `#scale[..]`, `#skew[..]`, `#columns(N)[..]`, `#hide[..]`, `#repeat[..]` | mapped to inline CSS (see "Layout" below) |
| `#grid(columns:, [cell], ...)`                                                | CSS Grid                             |
| `#stack(dir:, spacing:, [item], ...)`                                          | CSS flexbox                          |
| `#h(len)` / `#v(len)`                                                            | inline / block spacers               |
| `#set page(...)`, `#pagebreak()`, `#colbreak()`                                    | silently stripped, no output (see "Layout" below) |
| `// comment`                        | stripped                             |
| `/* comment */`                     | stripped                             |
| `$ ... $` (spaces inside)           | display/block math                   |
| `$...$` (no spaces)                 | inline math                          |

Plain lines with no blank line between them are joined into one `<p>`,
same reflow behaviour as Markdown.

## Math: MathML by default, LaTeX as a real fallback

Every equation is parsed once into a small AST, then rendered twice from
that same AST: to MathML (what's shown by default) and to LaTeX (kept as
a fallback for browsers that can't render MathML). The output looks like:

```html
<span class="typst-math" data-display="inline">
  <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">
    <semantics>
      <mrow> ... </mrow>
      <annotation encoding="application/x-tex">x^{2} + y^{2}</annotation>
    </semantics>
  </math>
  <span class="typst-math-fallback" aria-hidden="true" hidden>\(x^{2} + y^{2}\)</span>
</span>
```

The `<annotation>` is invisible per the MathML spec (browsers only render
the first child of `<semantics>`), so on any MathML-capable browser you
just get clean native MathML -- selectable, accessible, no JS needed.

`static/mathml-fallback.js` handles the rest: on page load it does a real
feature test (not a browser sniff) to check whether MathML is actually
rendered, and if not, hides the `<math>` element and reveals the LaTeX
fallback span. If `KaTeX` or `MathJax` is also loaded on the page, the
fallback is rendered through it for a normal-looking equation; if
neither is present, the raw LaTeX source is shown as plain text (still
correct and readable, just not typeset).

Wire it up via Pelican's static file settings, e.g.:

```python
STATIC_PATHS = ["extra/mathml-fallback.js"]
EXTRA_PATH_METADATA = {"extra/mathml-fallback.js": {"path": "mathml-fallback.js"}}
```

and add `<script src="{{ SITEURL }}/mathml-fallback.js"></script>` to
your theme's base template (optionally alongside a `<script>` tag for
KaTeX/MathJax if you want prettier fallback rendering).

Typst math syntax supported by the converter: identifiers, numbers,
Greek letters and common symbols (`alpha`, `infinity`, `arrow.r`,
`lt.eq`, ...), `^`/`_` sub/superscripts (including `sum_(i=1)^n` style
limits), `frac(a,b)` and the `a/b` shorthand, `sqrt()`, `root()`,
`vec()`, `mat(...; ...)`, `binom()`, `abs()`, `norm()`, `floor()`,
`ceil()`, big operators (`sum`, `product`, `integral`, ...), common
named functions (`sin`, `cos`, `lim`, `det`, ...), accents (`hat()`,
`tilde()`, `dot()`, `ddot()`, `bar()`, `breve()`, `check()`, `acute()`,
`grave()`, `circle()`, `arrow()` for vectors, plus the generic
`accent(x, symbol)` form), primes (`x'''`), math-alphabet styles
(`bb()`, `cal()`, `frak()`, `sans()`, `mono()`, `bold()`, `italic()`,
`upright()` -- using the real Unicode Mathematical Alphanumeric
Symbols, e.g. `bb(R)` renders as an actual ℝ, not a styled "R"),
`cancel()`, `class()`, `lr()`, `stretch()`, sizing overrides (`display()`,
`inline()`, `script()`, `sscript()`), and `overbrace()`/`underbrace()`.

This covers every item in Typst's own ["math" reference category](https://typst.app/docs/reference/math/),
including equation accessibility text via `#math.equation(alt: "...")`
(see below). Equation *numbering* (`#set math.equation(numbering:)`)
is still not implemented -- ask if you want that added too, it's a
distinct feature from `alt`. A few honest simplifications worth
knowing about:

- `class()` and `stretch()`'s sizing options are recognised-and-ignored
  (content renders correctly, but the fine spacing/sizing control itself
  has no effect) -- these are subtle typesetting nuances that don't
  have a clean equivalent in plain HTML/MathML.
- The blackboard-bold/calligraphic/fraktur/italic Unicode remapping only
  applies to plain ASCII letters (the overwhelmingly common case, e.g.
  `bb(R)`, `cal(A)`) -- applying a style to a complex nested expression
  (like `bb(x^2)`) falls back to rendering the expression normally,
  unstyled, since the Unicode math-alphanumeric block only covers
  individual letters, not structural constructs.
- "styles" and "variants" (two separate items in Typst's own docs) are
  treated as the same mechanism here.

Anything genuinely unrecognised (not on the list above) degrades to an
upright word/identifier rather than breaking the build.

### Equation accessibility (`alt:`)

```typst
#math.equation(
  alt: "d S equals delta q divided by T",
  block: true,
  $ dif S = (delta q) / T $,
)
```

`alt` becomes an `aria-label` on the `<math>` element -- MathML's actual
accessible-name mechanism, so screen readers announce your plain-language
description instead of trying to read the raw notation aloud. Matches
Typst's own recently-added `math.equation.alt` property, which exists
specifically because PDF/UA accessibility standards require it. Works
for both block and inline equations; `block:`/`numbering:`/`supplement:`
and other named args are recognised (block affects display mode) or
harmlessly ignored (numbering, supplement) rather than breaking the call.

## YAML subset

`simpleyaml.py` is a small hand-rolled parser, not `pyyaml` -- it covers
what front matter actually uses:

- flat `key: value` pairs
- inline lists (`tags: [a, b, c]`) and block lists (`- item` on
  following lines)
- quoted (`"..."`/`'...'`) and unquoted string scalars
- booleans (`true`/`false`/`yes`/`no`), `null`/`~`
- integers and floats
- ISO dates (`2026-06-01`) and datetimes (`2026-06-01 10:30`)
- `#` comments (correctly ignored inside quoted strings)

It deliberately does **not** support YAML anchors/aliases, multi-line
block scalars (`|`/`>`), flow mappings (`{a: 1}`), nested mappings, or
multiple documents -- none of which come up in normal post front matter.
If you hit one of these, the value will just come back as a plain
string rather than the parser crashing.

## Footnotes

`#footnote[content]` works the same way it does in real Typst -- the
note is written inline at its point of use, not defined separately and
referenced by key. Each one becomes a superscript reference marker in
place, and all footnotes for the article are collected into a numbered
list appended after the body, with back-links from note to reference:

```html
<p>Some claim.<sup id="fnref1" class="footnote-ref"><a href="#fn1">1</a></sup></p>
...
<section class="footnotes" role="doc-endnotes">
<hr>
<ol>
<li id="fn1">The note text. <a href="#fnref1" class="footnote-backref" aria-label="Back to content">↩</a></li>
</ol>
</section>
```

Numbering is sequential in document order, regardless of how many
paragraphs/lists/blocks the footnotes are spread across. Footnote
content gets full inline processing -- bold/italic, inline math, and
`#link(...)[...]` (including nested brackets, e.g. a link *inside* a
footnote) all work correctly inside `#footnote[...]`.

No CSS is bundled for the `.footnotes` section -- it'll render as a
plain `<hr>` + numbered list unless you style it in your theme. A
reasonable starting point:

```css
.footnotes { font-size: 0.9em; color: #555; }
.footnote-ref a, .footnote-backref { text-decoration: none; }
```

## Text styling

Most of Typst's `text` reference category is supported (everything
except `lorem`, which is a placeholder-text generator and doesn't
really apply to converting already-written content):

- **Simple wraps** -- `#highlight[]`, `#strike[]`, `#underline[]`,
  `#overline[]`, `#smallcaps[]`, `#sub[]`, `#super[]` -- each recursively
  processes its content (so `#highlight[a *bold* word]` works correctly)
  and wraps it in the obvious tag/CSS.
- **`#upper[]` / `#lower[]`** -- case-transformed, but deliberately
  **not** recursively processed. If they were, uppercasing a nested
  `<strong>` tag would mangle the tag name itself. So content inside
  `#upper[...]`/`#lower[...]` is treated as plain text -- no nested
  bold/italic/links/math inside a case-transform. In practice this is
  rarely a real constraint (case-transforms are almost always applied to
  short plain phrases).
- **`#text(...)[...]`** -- best-effort mapping to inline CSS. Recognised
  keys: `fill` (named CSS colors, `rgb("#hex")`, or `rgb(r, g, b[, a])`),
  `size` (needs a `pt`/`em`/`cm`/`mm`/`in` unit), `weight` (named like
  `"bold"`/`"light"` or numeric 100-900), `style` (`"italic"`/`"normal"`/
  `"oblique"`), and `font`. Unrecognised keys are silently ignored rather
  than breaking the build.
- **`#raw("code", lang: "...", block: true/false)`** -- the function
  form, alongside the existing `` `code` `` and fenced ` ``` ` shorthand
  syntax. Known gap: if the string literal itself contains a real
  newline, that newline gets flattened to a space (paragraph-line-joining
  doesn't know it's inside a quoted string) -- use a fenced code block
  instead for genuinely multi-line code, which handles this correctly.
- **Linebreaks** -- both the `\` end-of-line shorthand and `#linebreak()`
  produce a `<br>`.
- **Smart quotes** -- straight `"`/`'` are automatically converted to
  typographic quotes/apostrophes, matching Typst's default behaviour.
  This is always on; there's currently no equivalent of
  `#set smartquote(enabled: false)` to disable it per-file.

## Tables

```typst
#table(
  columns: 3,
  table.header([Name], [Role], [Team]),
  [Alice], [Engineer], [Platform],
  [Bob], [Designer], [Product],
)
```

Unlike everything else in this converter, table calls are allowed to
span multiple physical lines (most real tables are written that way for
readability) -- the parser does a paren-depth-aware scan to find the
matching close, not a single-line regex.

- `columns:` accepts a plain integer (`columns: 3`) or an array, where
  the array's *length* determines the column count (`columns: (1fr, 1fr, 1fr)`
  becomes 3 columns; the actual width values are ignored, since column
  sizing doesn't map onto this converter's plain HTML `<table>` output).
- An optional leading `table.header([h1], [h2], ...)` argument becomes a
  real `<thead>`. Without it, all cells go into `<tbody>` as plain `<td>`
  -- there's no automatic header-row detection.
- Cell content gets full recursive inline processing -- math, links,
  bold/italic, etc. all work inside a cell.
- Other named args (`stroke:`, `align:`, `fill:`, `inset:`, and so on)
  are recognised-and-ignored rather than breaking the build -- they're
  visual/layout concerns that don't map onto plain HTML tables anyway.

## Term lists

```typst
/ Typst: A markup-based typesetting system.
/ Pelican: A static site generator written in Python.
```

Becomes `<dl><dt>Term</dt><dd>Description</dd>...</dl>`. Splits on the
*first* colon on the line. Same limitation as bullet/numbered lists:
single physical line per item -- a description can't continue onto a
following (unmarked) line.

## Numbering

`#numbering("pattern", n1, n2, ...)` -- the direct function-call form,
matching real Typst semantics:

```typst
#numbering("1.", 3)        // "3."
#numbering("a)", 27)       // "aa)"
#numbering("I.", 2026)     // "MMXXVI."
#numbering("1.1.1", 2, 3)  // "2.3."  (only as many groups as numbers given)
#numbering("*", 7)         // "**"    (star markers cycle then double)
```

Counting symbols: `1` (arabic), `a`/`A` (lower/uppercase letters, with
`z` rolling over to `aa`, `ab`, ...), `i`/`I` (lower/uppercase roman
numerals), `*` (star/dagger/double-dagger cycle, matching Typst's
default footnote-marker style). Everything else in the pattern is a
literal separator. If more numbers are given than the pattern has
counting positions, the last group (symbol + its trailing literal)
repeats for the remaining numbers, matching Typst's own documented
behaviour.

**Auto-numbered headings** are also supported via
`#set heading(numbering: "pattern")`:

```typst
#set heading(numbering: "1.1.1")

= Introduction        // -> "1. Introduction"
== Background          // -> "1.1. Background"
== Motivation            // -> "1.2. Motivation"
= Methodology               // -> "2. Methodology"
== Data Collection             // -> "2.1. Data Collection"
```

- A per-level counter (levels 1-6) increments on each heading; deeper
  levels reset to 0 whenever a shallower heading appears, so section 2
  starts subsection numbering over at `2.1`, not continuing from `1.3`.
- The directive is a document-wide switch, not scoped to a section --
  once seen, every heading after it is numbered until either the
  document ends or a later `#set heading(numbering: none)` turns it back
  off. Turning it off doesn't retroactively change headings already
  rendered before that point.
- If you skip a level (e.g. `=` straight to `===` with no `==` in
  between), the unused level's counter stays at 0 rather than being
  silently hidden -- you'd see something like `1.0.1`, an honest
  reflection of what happened rather than a guess at what you meant.
- This is a document-wide flag, not scoped like Typst's real `#set`
  rule system (which supports proper block/function scoping) -- there's
  only one heading-numbering pattern active at a time per file.
- Unlike real Typst, this doesn't affect an outline/table-of-contents
  (not implemented) or cross-references (also not implemented) -- it
  only changes what appears directly in the `<h1>`-`<h6>` text.

## Cross-references and outline

```typst
= Introduction <intro>
...
As covered in @intro, ...          // shorthand
As covered in #ref(<intro>), ...   // function form, equivalent
```

Attach a label to a heading with `<label>` at the end of the heading
line. Reference it from anywhere in the document -- **before or after**
the heading itself. This works because `convert()` runs a lightweight
first pass over the whole document (`_collect_headings`) that computes
every heading's id and number before the real line-by-line render pass
starts, so forward references ("as we'll cover in @later-section")
resolve correctly, not just backward ones.

- The link text shown is the heading's **number** if
  `#set heading(numbering:)` is active at that point in the document,
  otherwise the heading's plain text.
- Headings without an explicit `<label>` still get an auto-generated
  anchor (`id="section-N"`) so `#outline()` can always link to them --
  they just can't be targeted by `@something` themselves, since there's
  no author-chosen name for it (matches real Typst, which also requires
  an explicit label to reference something).
- An unresolved reference (typo, or the label genuinely doesn't exist)
  degrades to showing the literal `@label` text rather than crashing or
  guessing.
- **Known caveat:** the `@label` shorthand's character set deliberately
  excludes `.`, because Typst label names combined with normal sentence
  punctuation created a real ambiguity during testing -- `@section.`
  at the end of a sentence would otherwise swallow the period into the
  label name and fail to resolve. Use `:`/`-`/`_` in label names instead
  of `.` if you plan to reference them with the `@` shorthand (the
  `#ref(<label>)` function form doesn't have this restriction, since its
  `<...>` delimiters make the boundary unambiguous either way).
- Only heading labels are supported as reference targets -- not
  figures, equations, or table labels.

`#outline()` builds a nested table of contents from every heading in
the document (regardless of where the `#outline()` call itself sits):

```typst
#outline()                                    // default: "Contents" title, all levels
#outline(title: [Table of Contents])           // custom title
#outline(title: none)                           // no title heading at all
#outline(depth: 2)                               // only include levels 1-2
```

Renders as `<nav role="doc-toc"><h2>...</h2><ul>...</ul></nav>` with
properly nested `<ul>`s matching heading depth. No CSS bundled -- style
`.outline` in your theme same as you would for `.footnotes`. The
`target:` argument (for building an outline of figures/tables instead
of headings) isn't supported -- always heading-based.

## Layout

Typst's ["layout" reference category](https://typst.app/docs/reference/layout/)
has 27 entries, but roughly a third of them are fundamentally about
**paged, printed documents** -- a Pelican article is a continuously-
scrolling web page with no concept of "pages" at all, so those don't
translate. Here's the honest breakdown:

**Implemented (14 functions, mapped to real CSS):**

| Typst | CSS mapping |
|---|---|
| `align(pos)[..]` | `text-align` (horizontal component only -- see note below) |
| `block[..]` | `<div>` with `fill`→background-color, `inset`→padding, `radius`→border-radius, `width`/`height`, `stroke`→plain border |
| `box[..]` | same as `block`, but `<span style="display:inline-block">` |
| `pad[..]` | `padding` (single positional value = all sides, or `left:`/`right:`/`top:`/`bottom:`/`x:`/`y:`) |
| `move(dx:, dy:)[..]` | `position:relative` + offset |
| `place(pos)[..]` | `position:absolute` + edge mapping |
| `rotate(angle)[..]` | `transform: rotate()` |
| `scale(factor)[..]` | `transform: scale()` (`150%` correctly becomes `1.5`, not literal `150%`) |
| `skew(ax:, ay:)[..]` | `transform: skew()` |
| `columns(n)[..]` | `column-count` |
| `hide[..]` | `visibility:hidden` (reserves space -- matches Typst's semantics, deliberately not `display:none`) |
| `grid(columns:, [cell], ...)` | CSS Grid, multi-line source supported same as `#table` |
| `stack(dir:, spacing:, [item], ...)` | CSS flexbox (Typst's default direction, top-to-bottom, is respected) |
| `h(len)` / `v(len)` | inline spacer span / block spacer div |

**Silently stripped -- produce no HTML output at all**, rather than
leaking as broken literal text: `#set page(...)`, `#pagebreak()`,
`#colbreak()`. This matters if you write the same `.typ` source for
both this plugin and real `typst compile` output (PDF) -- page setup
and manual page/column breaks are meaningful there and meaningless
here, so they're recognised and discarded cleanly instead of showing
up as garbled text in the middle of your article. `#set page(...)`
supports the same multi-line, one-option-per-line style as `#table`.

**Not implemented -- genuinely can't be, not just "not built yet":**
`layout()` and `measure()` are compile-time layout-introspection
functions (they need to know computed sizes that only a real layout
engine produces) -- architecturally impossible for a static text-to-
HTML converter to answer, since only the browser computes layout, at
render time, not this plugin at build time.

**Simplifications worth knowing about:**
- `align()` only handles the horizontal component (`left`/`center`/
  `right`/`start`/`end`). Vertical alignment (`top`/`bottom`/`horizon`)
  is silently ignored -- it depends on knowing the container's height,
  which doesn't translate cleanly to flowing HTML anyway.
- `repeat()` is supposed to fill available space by repeating content
  (e.g. dotted leader lines before a page number) -- since that also
  needs real layout computation, the content renders **once** instead,
  rather than showing nothing or broken syntax.
- `align`/`block`/`pad`/`place` render a `<div>`. If one of these
  appears alone on its own line, it currently ends up nested inside a
  `<p>` -- technically invalid HTML5 (browsers auto-recover and render
  it correctly regardless, but a strict validator would flag it).

## Constructs that are recognised and cleanly stripped

A full audit pass went through every category above checking what
happens for constructs we *don't* support: does it leak as broken
literal text, or degrade cleanly? The following are now recognised and
produce **zero output**, rather than showing up as garbled text in the
middle of an article:

- **Any `#set name(...)` rule** other than `#set heading(numbering:)`
  (which is the one case with real semantic effect here) -- `#set
  text(...)`, `#set par(...)`, `#set document(...)`, `#set
  math.equation(numbering:)`, etc. A `#set` rule never produces visible
  output in real Typst either, so stripping is strictly correct, not a
  compromise. Multi-line, same as `#set page(...)`.
- **`#import "file.typ": *`** and **`#import "@preview/pkg:1.0.1": ...`**
  -- common in real templated documents, never visible either way.
- **`#bibliography(...)`** and **`#cite(<key>)`** -- since bibliographies
  aren't implemented (see below), showing the raw call would be
  strictly worse than hiding it.

## Variable bindings (`#let`)

```typst
#let version = "1.2.3"
#let year = 2026
#let draft = false

Current version: #version, released #year. Draft: #draft.
```

Simple literal bindings (`"strings"`, numbers, `true`/`false`) are
tracked and substituted wherever the bare name is referenced later --
this is a real, bounded feature, not just cleanup: the binding line
itself is stripped (it never renders in real Typst either), and every
subsequent `#name` use resolves to the stored value.

What's deliberately **not** supported, and stays honestly broken rather
than silently vanishing:

- **Function definitions** (`#let f(x) = ...`) -- the definition line
  is still stripped cleanly (it never renders either way), but calling
  the function isn't evaluated. This isn't a strip case; genuinely
  calling a function requires real evaluation, which is out of scope.
- **Anything beyond a plain literal on the right-hand side** --
  expressions, computed values, arrays, other variable references.
- **Forward references** -- `#x` used *before* `#let x = ...` appears
  in the document stays unresolved, matching real Typst's own
  sequential, top-to-bottom evaluation (a genuine forward reference to
  a `#let` variable is undefined in real Typst too, so this isn't a
  limitation of the plugin, it's the correct behavior).

The design principle here: a visible gap (`#name` showing as literal
broken text) tells you something needs attention; a silent gap doesn't.
Every construct in this plugin that can't be fully resolved follows
that same rule rather than guessing or hiding the problem.

## Constructs that were too narrowly matched (now widened, not stripped)

A few existing patterns only matched one specific shape and fell
through to broken text the moment real usage varied slightly. These
now accept the realistic range of forms Typst itself allows, rather
than being stripped:

- `#quote[text]` now also accepts `#quote(attribution: [Name])[text]`
  (or a plain string attribution), rendering a `<footer>`.
- `#figure(...)` now works without a caption, and its body can be an
  `image(...)` call, a nested `table(...)` call, or arbitrary bracket
  content -- not just the one exact `image + caption` shape.
- `#image("path")` now also accepts `width:`/`height:` args.
- `#strong[...]` / `#emph[...]` (the function forms) now work
  alongside the existing `*..*`/`_.._` shorthand.
- `#raw(...)` now accepts its arguments (the code string, `lang:`,
  `block:`) in **any order**, not just one fixed sequence.

## Placeholder text (`#lorem()`)

`#lorem(n)` produces `n` words of placeholder text, drawn (with
wraparound) from a bundled classic Lorem Ipsum passage stored in its
own data file (`data/lorem.txt`) rather than hard-coded inline --
straightforward to swap out if you'd rather use different filler text.
This is **not** a faithful reproduction of Typst's own `lorem()`
algorithm (which uses a seeded pseudo-random generator for more varied,
sentence-like output) -- it's a simpler, deterministic "take the next N
words from the pool" approach. Good enough for placeholder purposes,
not trying to be pixel-identical to Typst's own output.

## Bibliographies

Not yet implemented -- calls are stripped cleanly (see above) rather
than shown broken. See "Limitations" below for the fuller picture.

## Limitations (read this before relying on it for complex documents)

- This is **not** a Typst implementation. Typst-the-language features
  (`#let`, `#for`, `#if`, custom functions, package imports, footnotes,
  bibliographies, cross-references, etc.) are not evaluated -- if your
  `.typ` files use them, they'll show up as literal text in the output,
  not be executed.
- The Typst-math-to-LaTeX conversion is best-effort. It covers the
  constructs listed above well; unusual notation (custom operators,
  exotic delimiters, stretchy accents, multi-line aligned equation
  systems) will degrade gracefully rather than crash, but may not look
  exactly like Typst's own renderer would produce.
- `//` comment stripping is a simple scan, not a full tokenizer -- a
  `//` inside a string that itself contains unbalanced quotes could
  theoretically confuse it. This doesn't come up in normal prose.
- If you need pixel-perfect Typst rendering (not just "good enough for a
  blog post"), consider using Typst's own experimental HTML export
  (`typst compile --format html`) instead, at the cost of needing the
  Typst compiler as a build step.

## Files

```
pelican-typst/
├── pyproject.toml
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .gitignore
├── pyrightconfig.json
├── .github/
│   └── workflows/
│       └── tests.yml        # pytest across Python 3.8-3.12 + a real Pelican build smoke test
├── tests/
│   ├── conftest.py           # shared fixtures (converter, latex_of, mathml_of, EXAMPLES_DIR)
│   ├── test_math.py
│   ├── test_numbering.py
│   ├── test_metadata.py
│   ├── test_markup_basics.py
│   ├── test_markup_text_and_footnotes.py
│   ├── test_markup_layout.py
│   ├── test_markup_refs_and_numbering.py
│   ├── test_markup_let_and_lorem.py
│   ├── test_markup_strip_constructs.py     # includes the two real-bug regression tests
│   └── test_examples_smoke.py               # every example, through the real TypstReader
├── examples/
│   ├── README.md              # index -- what each file demonstrates, suggested order
│   ├── 01-getting-started.typ
│   ├── 02-native-metadata.typ
│   ├── 03-text-styling-and-footnotes.typ
│   ├── 04-math-extras.typ
│   ├── 05-tables-and-terms.typ
│   ├── 06-numbering-and-references.typ
│   ├── 07-layout.typ
│   ├── 08-let-bindings-and-graceful-fallbacks.typ
│   └── 09-known-limitations.typ
└── pelican/
    └── plugins/
        └── typst/              # no __init__.py above this level --
            ├── __init__.py     # plugin registration (readers_init signal)
            ├── reader.py        # TypstReader(BaseReader) -- ties it all together
            ├── metadata.py       # YAML front matter + Typst-dict metadata parsing
            ├── simpleyaml.py       # small YAML-subset parser (no pyyaml dependency)
            ├── math.py               # Typst math -> MathML + LaTeX (shared AST)
            ├── markup/                # Typst body markup -> HTML (split for readability --
            │   │                       see the package docstring in markup/__init__.py
            │   │                       for the full breakdown)
            │   ├── __init__.py         # re-exports TypstToHTML; design notes live here
            │   ├── patterns.py          # all regex/lookup constants, single source of truth
            │   ├── numbering.py          # numbering-pattern formatting algorithm
            │   ├── lorem.py                # #lorem() word-pool loader
            │   ├── text_utils.py            # generic string parsing (arg splitting, call
            │   │                             scanning, comments, smart quotes, #let literals)
            │   ├── css_utils.py              # Typst-value -> CSS mapping (colors, sizes,
            │   │                               weights, layout-wrapper CSS builders)
            │   ├── outline_utils.py            # flat heading list -> nested <ul> tree
            │   ├── block_renderers.py           # mixin: tables/grids/stacks/figures/images/
            │   │                                  heading-collection/outline
            │   ├── inline_processors.py           # mixin: the #name(...) substitution
            │   │                                    passes used inside _inline()
            │   └── core.py                          # TypstToHTML: state + convert() +
            │                                          _inline(), combines both mixins
            ├── static/
            │   └── mathml-fallback.js
            └── data/
                └── lorem.txt            # word pool for #lorem()
```

## A note on debugging with this structure

If something in the rendered HTML looks wrong, here's roughly where to
look first, in order of how often you'll actually need each one:

- **A specific Typst construct renders wrong or not at all** ->
  `patterns.py` first (is the regex actually matching what you wrote?),
  then whichever of `block_renderers.py` / `inline_processors.py`
  handles that construct.
- **CSS/styling looks off** (colors, sizes, `#text()`, `#block()`,
  `#align()`, etc.) -> `css_utils.py`.
- **Heading numbers, labels, or `#outline()` are wrong** ->
  `block_renderers.py` (`_collect_headings`, `_render_outline`) plus
  `numbering.py` for the actual number-formatting algorithm.
- **Something that should be silently stripped (e.g. `#set page(...)`)
  is leaking as visible text** -> check `patterns.py` for whether a
  matching regex exists yet, then `core.py`'s `convert()` main loop for
  whether it's actually wired in.
- **The overall pipeline order is suspect** (e.g. one substitution
  seems to interfere with another) -> `core.py`'s `_inline()` is the
  single place that lists every pass in order, with comments explaining
  why each one is positioned where it is.
