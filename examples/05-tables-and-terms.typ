---
title: Tables and Term Lists
date: 2026-07-02
tags: [typst, testing]
category: Testing
slug: tables-and-terms
summary: Table headers and cell markup, plus term/definition lists.
---

= Tables and term lists

== A basic table

#table(
  columns: 3,
  table.header([Name], [Role], [Team]),
  [Alice], [Engineer], [Platform],
  [Bob], [Designer], [Product],
  [Carol], [*Lead*], [Platform],
)

== A table with math and links in cells

#table(
  columns: 2,
  table.header([Expression], [Notes]),
  [$x^2 + y^2 = z^2$], [The Pythagorean theorem],
  [See #link("https://typst.app")[Typst docs]], [External reference],
)

== A term list

/ Typst: A modern markup-based typesetting system.
/ Pelican: A static site generator written in Python.
/ MathML: A markup language for describing mathematical notation, with automatic *browser-native* rendering support.
