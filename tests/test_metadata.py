"""Tests for pelican.plugins.typst.metadata (YAML front matter + native
#metadata() dict parsing) and simpleyaml (the bundled YAML-subset
parser that replaces pyyaml)."""

import datetime

from pelican.plugins.typst import simpleyaml
from pelican.plugins.typst.metadata import extract_metadata


class TestSimpleYAML:
    def test_flat_scalars(self):
        result = simpleyaml.safe_load("title: My First Post\nslug: my-first-post\n")
        assert result["title"] == "My First Post"
        assert result["slug"] == "my-first-post"

    def test_date_and_datetime(self):
        result = simpleyaml.safe_load("date: 2026-06-01\nmodified: 2026-06-02 10:30\n")
        assert result["date"] == datetime.date(2026, 6, 1)
        assert result["modified"] == datetime.datetime(2026, 6, 2, 10, 30)

    def test_inline_list(self):
        result = simpleyaml.safe_load("tags: [typst, pelican, python]\n")
        assert result["tags"] == ["typst", "pelican", "python"]

    def test_block_list(self):
        result = simpleyaml.safe_load("authors:\n  - Dale Hitchenor\n")
        assert result["authors"] == ["Dale Hitchenor"]

    def test_booleans_and_numbers(self):
        result = simpleyaml.safe_load(
            "published: true\ndraft: false\nrating: 4.5\ncount: 12\n"
        )
        assert result["published"] is True
        assert result["draft"] is False
        assert result["rating"] == 4.5
        assert result["count"] == 12

    def test_quoted_string_with_comma(self):
        result = simpleyaml.safe_load('summary: "A summary, with a comma, inside it"\n')
        assert result["summary"] == "A summary, with a comma, inside it"

    def test_hash_inside_single_quotes_is_not_a_comment(self):
        result = simpleyaml.safe_load("note: 'text with a # inside'\n")
        assert result["note"] == "text with a # inside"

    def test_trailing_comment_is_stripped(self):
        result = simpleyaml.safe_load("value: hello # trailing comment\n")
        assert result["value"] == "hello"


class TestExtractMetadata:
    def test_yaml_front_matter(self):
        doc = "---\ntitle: My First Post\ntags: [typst, pelican]\n---\n= Body\n"
        meta, body = extract_metadata(doc)
        assert meta["title"] == "My First Post"
        assert meta["tags"] == ["typst", "pelican"]
        assert body.strip() == "= Body"

    def test_native_metadata_call(self):
        doc = (
            "#metadata((\n"
            '  title: "Native Post",\n'
            '  tags: ("typst", "native"),\n'
            "))\n\n"
            "= Body\n"
        )
        meta, body = extract_metadata(doc)
        assert meta["title"] == "Native Post"
        assert meta["tags"] == ["typst", "native"]
        assert body.strip() == "= Body"

    def test_native_metadata_skips_leading_comment(self):
        doc = '// a leading comment\n#metadata((title: "Post"))\n\n= Body\n'
        meta, _body = extract_metadata(doc)
        assert meta["title"] == "Post"

    def test_no_metadata_returns_empty_dict(self):
        doc = "= Just a heading\n\nNo metadata here.\n"
        meta, body = extract_metadata(doc)
        assert meta == {}
        assert body == doc
