---
title: Getting Started with Typst and Pelican
date: 2026-06-15
modified: 2026-06-16
tags: [typst, pelican, python, math]
category: Programming
slug: getting-started-typst-pelican
authors: [Dale Hitchenor]
summary: A short demo post covering headings, lists, code, and math.
---

// this whole line is a comment and should vanish
= Introduction

This is a *bold* claim and this is _italic_ text, with some `inline code`
mixed in. Here's a link: #link("https://typst.app")[the Typst homepage].

== A list of things

- First item
- Second item with *emphasis*
- Third item

+ Step one
+ Step two
+ Step three

== Some code

```python
def hello(name):
    print(f"Hello, {name}!")
```

== Math

Euler's identity is $ e^(i pi) + 1 = 0 $ and it's genuinely one of the
best equations. Inline math like $x^2 + y^2 = z^2$ also works fine mid
sentence.

The quadratic formula:

$ x = frac(-b plus.minus sqrt(b^2 - 4a c), 2a) $

A matrix:

$ mat(1, 2; 3, 4) $

#quote[Simplicity is the ultimate sophistication.]

#figure(image("diagram.png"), caption: [An example diagram.])
