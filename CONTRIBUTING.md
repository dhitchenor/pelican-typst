# Contributing

Thanks for considering it. This is a small, mostly-personal plugin, so
this doc is short on purpose -- just enough to save you from repeating
mistakes that already happened once during development.

## Setting up

```bash
git clone https://github.com/dhitchenor/pelican-typst.git
cd pelican-typst
pip install .[test]
```

**Important gotcha if you're iterating on the code:** `pip install -e .`
(editable install) breaks Pelican's auto-discovery. Pelican's plugin
discovery walks `pelican.plugins.__path__` looking for real
subdirectories on disk; Python's PEP 660 editable-install mechanism
uses an import hook instead of exposing one, so there's nothing for
that directory scan to see. Verified by testing both:

- `pip install -e .` → auto-discovery finds nothing; you must set
  `PLUGINS = ["typst"]` explicitly in `pelicanconf.py` for it to load.
- `pip install .` (normal install) → auto-discovery finds it, no
  `PLUGINS` entry needed.

Either set `PLUGINS = ["typst"]` explicitly while using `-e .`, or just
re-run `pip install .` after each change instead (no build step
involved, it's pure Python, so it's fast either way).

A second, related gotcha: if you've previously done a normal
`pip install .`, there's now a real copy sitting in your environment's
`site-packages`. Editing the source in your working copy **won't be
picked up** until you reinstall (`pip install .` again) -- this bit
during development once (edited `markup.py`, ran tests, they silently
ran against the *old* installed copy because it happened to resolve
first in the namespace-package search path). If a test result looks
suspiciously unchanged after an edit, reinstall before trusting it.

## Running tests

```bash
pytest tests/ -v
```

167 tests as of writing. See the README's "Testing" section for what's
covered. If you're fixing a bug, **add a regression test for it** --
two of the tests in `test_markup_strip_constructs.py` and
`test_markup_let_and_lorem.py` exist specifically because real bugs
were found by hand during development and needed to be pinned in place
so they can't silently come back. That's the standard to match.

Before opening a PR, also sanity-check with a real build, not just
pytest -- `test_examples_smoke.py` catches a lot, but the single worst
bug found during development (a leftover placeholder breaking RSS/Atom
feed generation) only showed up in an actual Pelican build, not in unit
tests alone:

```bash
mkdir -p /tmp/site/content && cp examples/*.typ /tmp/site/content/
cat > /tmp/site/pelicanconf.py << 'EOF'
AUTHOR = "test"; SITENAME = "test"; SITEURL = ""
PATH = "content"; TIMEZONE = "UTC"; DEFAULT_LANG = "en"
PLUGINS = ["typst"]
EOF
cd /tmp/site && python -m pelican content -s pelicanconf.py -o output
```

CI (`.github/workflows/tests.yml`) runs both of these automatically on
every push/PR, across Python 3.8-3.12 -- but running them locally first
saves a round trip.

## Type checking

`pyrightconfig.json` pins `"typeCheckingMode": "basic"` explicitly.
This is a deliberate choice, not an oversight -- worth knowing before
your editor's language server (Zed, VS Code/Pylance, etc.) surfaces a
pile of diagnostics that look alarming but aren't:

- **Basic mode** catches real bugs and is fully clean across the whole
  package. Three genuine issues were found and fixed this way during
  development (an incompatible method override, an `Optional` value
  passed where a dict key required a concrete type, and several
  possible-`None` attribute accesses on regex matches) -- this is the
  level worth keeping clean, and PRs should not introduce new basic-mode
  diagnostics.
- **Strict mode** is not used here. Turning it on produces over 1,500
  diagnostics, almost all "no explicit type annotation" rather than
  actual problems. The bigger issue is `math.py`'s AST nodes are plain
  dicts with a dozen-plus different shapes (`{"type": "frac", "num":
  ..., "den": ...}` and friends) -- satisfying strict mode properly
  would mean introducing `TypedDict`s (or real classes) per node shape
  and threading `Union` types through every recursive render function.
  That's a structural redesign of the math parser's data model, not a
  type-hinting pass, and isn't considered worth it for a best-effort
  converter that isn't shipping bugs strict mode would actually catch.

If your editor shows a wall of "Unknown" type diagnostics despite
`pyrightconfig.json` being present, check that your editor is actually
picking up the project's config file rather than applying its own
default `typeCheckingMode`.

## Releasing

`.github/workflows/publish.yml` builds and publishes to PyPI
automatically whenever a `*.*.*` tag is pushed -- runs the full test
suite first as a gate, then builds, then publishes via PyPI's Trusted
Publishing (OIDC). No API token is stored anywhere, in GitHub or
locally.

**Every release:**

```bash
# bump version in pyproject.toml, update CHANGELOG.md, commit
git tag <version_number>
git push origin <version_number>
```

That's it -- the tag push triggers the workflow, which tests, builds,
and publishes automatically. Watch the Actions tab for progress; the
package should appear on PyPI within a minute or two of the workflow
finishing.

## Where things live

See the docstring at the top of `pelican/plugins/typst/markup/__init__.py`
for the full package breakdown, and the README's "A note on debugging
with this structure" section for "which file do I open for which kind
of bug." Short version: `patterns.py` has every regex, `core.py` has
the two central methods (`convert()`'s main loop and `_inline()`'s
substitution pipeline), and the two mixins (`block_renderers.py`,
`inline_processors.py`) split everything else by whether it's block-
level structure or inline text substitution.

## Design philosophy -- read this before adding a new construct

This plugin has a consistent, deliberate stance that new contributions
should match rather than work around:

1. **Best-effort, not a Typst implementation.** This converts Typst
   source text directly, with no `typst` binary and no real evaluator.
   Anything requiring actual computation (`layout()`, `measure()`,
   arbitrary `#let` expressions, loops, conditionals) is out of scope,
   not a bug to fix.
2. **Degrade honestly, don't hide problems.** When something can't be
   fully resolved, prefer showing it visibly broken over silently
   making it disappear -- a visible gap tells the author something
   needs attention; a silent one doesn't. The `#let` forward-reference
   behavior and the unresolved-`@label` handling are the reference
   examples for this.
3. **Strip, don't leak, for things with no HTML meaning.** Constructs
   that are genuinely meaningless outside PDF/print (`#set page(...)`,
   `#pagebreak()`) or that we don't implement at all
   (`#bibliography()`, `#cite()`) should produce clean *no output*, not
   broken literal text -- especially since real `.typ` files are often
   compiled to both PDF and this HTML pipeline from the same source.
4. **Never crash the whole build over one bad construct.** See
   `convert_math()`'s try/except and the malformed-math handling in
   `examples/09-known-limitations.typ` -- a single broken equation or
   unparseable call degrades to plain text, it doesn't take the article
   (or the whole site build) down with it.
5. **Document what you didn't do, as clearly as what you did.** Every
   feature section in the README has an honest "simplifications worth
   knowing about" subsection. If your addition has a real limitation,
   write it down next to the feature, not just in a commit message.

## Adding a new Typst construct

Rough shape, based on how existing ones are built:

- **Block-level** (own line, like `#table(...)`, `#figure(...)`): add a
  start-marker regex to `patterns.py`, register it in
  `_BLOCK_START_RES`, handle it in `core.py`'s `convert()` main loop
  (reuse `_scan_multiline_paren_call` if it can span multiple lines),
  and put the actual rendering in `block_renderers.py`.
- **Inline** (mid-paragraph, like `#link(...)`, `#numbering(...)`): add
  handling inside `_inline()` in `core.py`, or add a new
  `_process_*(text, stash)` method to `inline_processors.py` if it
  needs its own multi-step scan. Use the `stash()`/placeholder pattern
  everywhere -- inserting raw HTML directly into the text stream
  without stashing it is how the italic-shorthand regression happened
  (see `test_markup_let_and_lorem.py`).
- Either way: add tests (including at least one deliberately-malformed
  input, to confirm it degrades rather than crashes), add a short demo
  to the relevant file in `examples/` if it's a significant feature,
  and update the README's feature table plus its own subsection.

## Scope note

Bibliography support and equation numbering are known, deliberately
deferred gaps (see README "Limitations"). If you want to tackle either,
worth opening an issue to discuss the approach first -- both have real
design forks (e.g. BibTeX vs. Hayagriva YAML for bibliographies) that
are easier to agree on before writing code than after.
