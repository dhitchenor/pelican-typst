# Examples

Nine `.typ` files, numbered in a suggested reading order (though each
one stands alone -- feel free to jump to whichever topic you need).
Every file here has actually been built through the real Pelican
pipeline, not just written and assumed to work.

| File | Demonstrates |
|---|---|
| `01-getting-started.typ` | The basics: headings, lists, code, bold/italic, links, inline & display math, a quote, a figure. YAML front matter. Start here. |
| `02-native-metadata.typ` | The alternative to YAML front matter -- a native `#metadata()` call. Shares a category/tag with file 1 to show both metadata styles aggregating together correctly. |
| `03-text-styling-and-footnotes.typ` | highlight/strike/underline/overline/smallcaps, sub/superscript, upper/lower, `#text()`, `#raw()`, linebreaks, smart quotes, and footnotes (including one with a nested link and one with math). |
| `04-math-extras.typ` | Accents (`hat`, `tilde`, `dot`, ...), primes, alphabet styles (`bb`, `cal`, `frak`, ...), `cancel()`, forced sizing, `overbrace`/`underbrace`, and accessible equations via `#math.equation(alt:)`. |
| `05-tables-and-terms.typ` | Table headers, cell markup (math and links inside cells), and term/definition lists. |
| `06-numbering-and-references.typ` | The `#numbering()` formatter on its own, auto-numbered headings via `#set heading(numbering:)`, labels, cross-references (including a genuine **forward** reference), and `#outline()` -- all in one connected document. |
| `07-layout.typ` | All 14 supported layout functions (`align`, `block`, `box`, `grid`, `stack`, `pad`, `move`, `rotate`, `scale`, `skew`, `columns`, `hide`, `h`/`v`, `repeat`), plus proof that PDF-only directives (`#set page(...)`, `#pagebreak()`) vanish cleanly instead of leaking as broken text. |
| `08-let-bindings-and-graceful-fallbacks.typ` | `#let` literal substitution and its honest limits, plus everything this plugin recognises-and-strips rather than showing broken (`#set`, `#import`, `#bibliography`, `#cite`), generalized `#quote`/`#figure`/`#image`, flexible `#raw()` argument order, and `#lorem()`. |
| `09-known-limitations.typ` | Deliberately awkward input -- a nested list (doesn't nest, by design, see the README), and several kinds of malformed math -- to show exactly how the converter degrades rather than leaving you to guess. |

## Trying these yourself

Copy whichever file(s) you want into your Pelican project's `content/`
folder and build normally:

```bash
python -m pelican content -s pelicanconf.py -o output
```

Files 3 through 9 all use the same `category: Testing` / `tags: [typst,
testing]` so they'll group together on your test site if you drop in
several at once -- files 1 and 2 use `category: Programming` instead,
specifically to test that both metadata styles aggregate correctly
together (see `02-native-metadata.typ`'s summary).
