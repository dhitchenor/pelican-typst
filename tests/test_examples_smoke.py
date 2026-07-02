"""Smoke test: every .typ file in examples/ actually goes through the
real TypstReader (BaseReader subclass, same object Pelican itself
instantiates) -- not just TypstToHTML in isolation. Catches anything
that only breaks in the full metadata + BaseReader.process_metadata
pipeline, and catches leftover unrestored stash placeholders (see the
test_markup_strip_constructs.py regression test for why that matters)."""

import glob
import os

import pytest

from conftest import EXAMPLES_DIR

from pelican.plugins.typst.reader import TypstReader

_EXAMPLE_FILES = sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.typ")))


@pytest.fixture
def reader():
    # FORMATTED_FIELDS empty is fine here -- we're checking the reader
    # doesn't crash and produces clean output, not exercising Pelican's
    # own summary-formatting behaviour.
    return TypstReader(settings={"FORMATTED_FIELDS": []})


@pytest.mark.parametrize("path", _EXAMPLE_FILES, ids=[os.path.basename(p) for p in _EXAMPLE_FILES])
def test_example_reads_without_error(reader, path):
    content, metadata = reader.read(path)
    assert content, f"{path} produced empty content"
    assert "title" in metadata, f"{path} has no title metadata"


@pytest.mark.parametrize("path", _EXAMPLE_FILES, ids=[os.path.basename(p) for p in _EXAMPLE_FILES])
def test_example_has_no_leftover_stash_placeholders(reader, path):
    content, _metadata = reader.read(path)
    assert "\x00" not in content, (
        f"{path} left an unrestored stash placeholder in the output "
        "(a literal null byte) -- this breaks RSS/Atom feed generation."
    )


def test_at_least_the_expected_number_of_examples_were_found():
    # A trivial guard against the glob silently matching nothing (e.g.
    # if EXAMPLES_DIR were ever pointed at the wrong path).
    assert len(_EXAMPLE_FILES) >= 9
