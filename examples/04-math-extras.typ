---
title: Math Extras
date: 2026-07-06
tags: [typst, testing]
category: Testing
slug: math-extras
summary: Accents, primes, alphabet styles, cancel, sizes, underover, and accessible equations.
---

= Math extras

== Accents

Velocity is often written $hat(v)$ or with a tilde $tilde(x)$. A vector
might use $arrow(v)$, and calculus notation often needs $dot(x)$ or
$ddot(x)$ for first and second derivatives.

== Primes

The derivative $f'(x)$, second derivative $f''(x)$, and third
derivative $f'''(x)$ all use prime notation.

== Alphabet styles

The reals are $bb(R)$, a calligraphic set might be $cal(A)$, and old
German-style notation uses fraktur like $frak(g)$. Plain styling: bold
$bold(x)$ and italic $italic(y)$.

== Cancel and sizes

Cancelling a term: $ cancel(x) + y = y $ (after cancelling $x$).

Forcing display style inline: $display(sum_(i=1)^n i)$ versus normal
inline $sum_(i=1)^n i$.

== Braces

$ overbrace(a + b + c, "three terms") $

$ underbrace(x y z, "product") $

== Accessible equations

#math.equation(
  alt: "d S equals delta q divided by T",
  block: true,
  $ dif S = (delta q) / T $,
)

Inline with alt: #math.equation(alt: "E equals m c squared", $E=mc^2$).
