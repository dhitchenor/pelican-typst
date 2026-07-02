---
title: Layout
date: 2026-07-07
tags: [typst, testing]
category: Testing
slug: layout
summary: All 14 layout functions, plus PDF-only directives that should vanish cleanly.
---

// This file deliberately includes PDF-only page setup, exactly like a
// real dual-purpose document that's also compiled to PDF via `typst
// compile`. None of this section should produce any visible HTML output.
#set page(
  width: 21cm,
  height: 29.7cm,
  margin: (x: 2.5cm, y: 3cm),
  numbering: "1",
)

= Layout

This document tests every layout function. If PDF-only directives are
handled correctly, you won't see anything broken above this heading.

== Alignment and boxes

#align(center)[This text is centered.]

#block(fill: rgb("#eef"), inset: 1em, radius: 6pt)[
A block with a light background, padding, and rounded corners.
]

Some prose with an inline #box(fill: yellow, inset: 3pt)[highlighted box]
in the middle of a sentence.

== Grid and stack

#grid(
  columns: 3,
  gutter: 1em,
  [Alpha], [Beta], [Gamma],
  [1], [2], [3],
)

#stack(dir: ltr, spacing: 1em, [Left], [Middle], [Right])

== Transforms

#rotate(-5deg)[Slightly rotated text.]
#scale(120%)[Scaled up text.]

== Spacing

Before some space#h(1cm)and after it, on the same line.

#v(1.5cm)

That was a vertical gap above this line.

#pagebreak()

This paragraph comes after a pagebreak in the source -- for PDF output
that would start a new page; here it should just flow normally as the
next paragraph, since a scrolling web page has no pages to break
between.

== Repeat and hide

Leader dots approximation: #repeat[.]

Some #hide[invisible] text you can't see (but it still takes up space,
matching Typst's hide() semantics).
