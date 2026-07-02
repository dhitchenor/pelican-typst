---
title: Known Limitations
date: 2026-06-25
tags: [typst, testing]
category: Testing
slug: known-limitations
summary: Deliberately awkward content to see exactly how the converter degrades, rather than assuming.
---

= Known limitations

This file is deliberately awkward. The goal isn't pretty output -- it's
to see exactly how each feature behaves, including the ones that don't
fully work yet, so there are no surprises.

== A list that tries to nest (known limitation)

- Top level item one
  - Attempted sub-item (indented)
  - Another attempted sub-item
- Top level item two

Expected: the converter currently only recognises bullets flush at the
start of a line, so the indented lines above will most likely get
absorbed into a paragraph instead of forming a nested `<ul>`. That's a
real limitation, not a bug you need to chase -- worth confirming what it
actually does rather than assuming.

== A code block

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

== An image reference

#image("diagram.png")

== A display equation with a matrix

$ mat(1, 2, 3; 4, 5, 6; 7, 8, 9) $

== Deliberately broken math

Unbalanced parentheses: $ frac(a, (b + c $

An unknown function typst doesn't have: $ frobnicate(x, y) + zorp^2 $

Just garbage tokens: $ @@@ ### $$$ $

Expected: none of the above should crash the build. Each malformed
equation should fall back to plain text (or a best-effort partial
render) rather than taking the whole site down with it.
