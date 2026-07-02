---
title: Numbering and References
date: 2026-07-04
tags: [typst, testing]
category: Testing
slug: numbering-and-references
summary: The #numbering() formatter, auto-numbered headings, labels, cross-references (including forward references), and #outline() all together.
---

#set heading(numbering: "1.1.1")

#outline(title: [Contents])

= Introduction <intro>

This paper builds on the methodology described in @methods below --
that's a forward reference, pointing at a section that hasn't appeared
yet in the document, and it still resolves correctly.

== The #numbering() formatter, directly

Before the auto-numbered sections below, here's the raw formatter
function on its own, since it's the same algorithm powering every
heading number in this document: arabic #numbering("1.", 1),
#numbering("1.", 2), #numbering("1.", 3); lowercase letters
#numbering("a)", 1), #numbering("a)", 27) (rolls over past z); roman
numerals #numbering("I.", 4), #numbering("I.", 2026); star markers
#numbering("*", 1), #numbering("*", 2). A multi-level pattern like
#numbering("1.1.1", 2, 3, 4) reads as chapter 2, section 3, subsection 4.

= Background

== Prior Work <prior-work>

Some background details.

== Motivation

As covered in @prior-work above, this is well established. See also
#ref(<intro>) for the framing.

= Methods <methods>

== Data Collection

=== Survey Design

Details on how data was gathered, referenced earlier from @intro -- and
note this is a level-3 heading, so it picks up a three-part number like
"3.1.1".

== Analysis

Standard analysis techniques.

= Conclusion <conclusion>

Bringing it all together, as promised back in @methods.
