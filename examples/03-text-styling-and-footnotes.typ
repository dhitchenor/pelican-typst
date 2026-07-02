---
title: Text Styling and Footnotes
date: 2026-07-01
tags: [typst, testing]
category: Testing
slug: text-styling-and-footnotes
summary: Every supported text-level feature, plus footnotes (including one with a nested link and one with math).
---

= Text styling

Basic marks: #highlight[highlighted], #strike[struck through],
#underline[underlined], #overline[overlined], and #smallcaps[Small Caps].

Chemistry needs subscript: H#sub[2]O. Physics needs superscript:
E = mc#super[2].

#upper[This whole sentence is shouting] but this part stays
*bold* and _italic_ as normal. #lower[THIS ONE WHISPERS INSTEAD.]

Inline code the function way: #raw("let x = 5;", lang: "rust"). Same
thing the shorthand way: `let x = 5;`.

Styled text: #text(fill: red)[red], #text(fill: rgb("#0077cc"))[custom blue],
#text(weight: "bold", style: "italic")[bold italic], and
#text(size: 1.4em)[bigger text].

A line #linebreak() break via function call, and one via the \
backslash shorthand.

Typst auto-curls "straight quotes" and turns apostrophes like isn't,
don't, and it's into proper typographic marks -- not just at the start
of a sentence, but 'nested quotes' too.

= Footnotes

Typst source code should be self explanatory.#footnote[This is the
first footnote, and gets number 1 regardless of where it sits in the
document -- numbering is assigned in the order footnotes appear when
the file is converted.]

Footnotes can contain most inline markup: *bold*, math like
$e^(i pi) + 1 = 0$, and even links.#footnote[See #link("https://typst.app")[the Typst homepage]
for the real thing this plugin is approximating.]

A closing thought with a plain footnote, no special formatting needed
to make it work.#footnote[Just a plain note, alongside everything else
on this page.]
