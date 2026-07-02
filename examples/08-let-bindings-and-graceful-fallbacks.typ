---
title: Let Bindings and Graceful Fallbacks
date: 2026-07-08
tags: [typst, testing]
category: Testing
slug: let-bindings-and-graceful-fallbacks
summary: #let literal substitution, generic #set/#import/#bibliography stripping, generalized quote/figure/image, flexible raw() argument order, and #lorem().
---

// Simulating a real dual-purpose document: font/paragraph setup that's
// meaningful for PDF, meaningless here, and a template import. None of
// this section should produce visible output.
#set text(font: "New Computer Modern", size: 11pt)
#set par(justify: true, leading: 0.65em)
#import "shared-template.typ": *

#let product_name = "TachKing"
#let current_year = 2026
#let is_beta = true

= Let bindings

This post is about #product_name, released in #current_year. Beta
status: #is_beta. If the PDF-only setup and the import above were
stripped correctly, nothing looks broken above this heading either.

We reference #product_name again here -- every use of a bound name
resolves, not just the first.

== What still doesn't work (by design, not by accident)

#let describe(x) = "Item: " + x

Function definitions like the one above get their own line stripped
cleanly (you won't see the definition itself), but we can't evaluate
function calls -- there's no attempt to resolve one here.

A genuinely undefined reference like #totally_undefined_name stays
visibly broken rather than silently disappearing, which is the correct
tradeoff: a visible gap tells you something needs fixing, a silent one
doesn't.

= Graceful fallbacks

== Generalized quote

#quote(attribution: [Ada Lovelace])[
That brain of mine is something more than merely mortal.
]

== Generalized figure

A figure without a caption:

#figure(image("diagram.png"))

A figure wrapping a table instead of an image:

#figure(
  table(columns: 2, [Metric], [Value], [Speed], [Fast]),
  caption: [Benchmark results],
)

== Generalized image

#image("photo.jpg", width: 60%)

== Function-form emphasis

This is #strong[strongly] stated, and this is #emph[emphasized] too.

== Flexible raw() argument order

#raw(lang: "python", "def f(): pass")

== Placeholder text

#lorem(20)

== Bibliography (not implemented -- should vanish cleanly)

Some claim needing a citation #cite(<example2026>).

#bibliography("refs.bib")

This paragraph comes after the bibliography call and should render
completely normally.
