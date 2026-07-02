#metadata((
  title: "Why I Switched My Notes to Typst",
  date: "2026-06-22",
  modified: "2026-06-23",
  tags: ("typst", "workflow", "opensuse"),
  category: "Programming",
  slug: "native-metadata-demo",
  authors: ("Dale Hitchenor",),
  summary: "The alternative to YAML front matter: a native #metadata() call. Shares a category and tag with the getting-started post to check cross-style category/tag aggregation.",
))

= Why I switched my notes to Typst

This post uses `#metadata()` instead of YAML front matter -- everything
else about the body works identically either way. It deliberately
shares the *Programming* category and the `typst` tag with the
getting-started post, so if category and tag pages are working
correctly, both posts should show up together on the "Programming"
category page and the "typst" tag page, even though they were written
in two different metadata styles.

== Quick recap of why

- Plain text source, easy to diff in git
- Real math support instead of fighting image exports
- No lock-in to a specific editor

== One inline equation for good measure

The golden ratio $phi = frac(1 + sqrt(5), 2)$ shows up more often in
note-taking apps than you'd expect.
