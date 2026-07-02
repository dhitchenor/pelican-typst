import os
import re

import pytest

from pelican.plugins.typst.math import convert_math
from pelican.plugins.typst.markup import TypstToHTML

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

_ANNOTATION_RE = re.compile(r'application/x-tex">(.*?)</annotation>')
_MROW_RE = re.compile(r"<mrow>(.*?)</mrow><annotation")


@pytest.fixture
def converter():
    """A fresh TypstToHTML instance -- state (footnotes, headings,
    let-bindings, ...) must not leak between tests."""
    return TypstToHTML()


def latex_of(src, display=False):
    """Convert a Typst math snippet and pull out just the embedded
    LaTeX annotation, for easy assertions without hand-parsing MathML."""
    html_out = convert_math(src, display=display)
    m = _ANNOTATION_RE.search(html_out)
    assert m, f"no LaTeX annotation found in output for {src!r}"
    return m.group(1)


def mathml_of(src, display=False):
    """Convert a Typst math snippet and pull out the top-level MathML
    <mrow> content, for asserting on actual rendered characters (e.g.
    the Unicode alphabet-style remapping) rather than the LaTeX side."""
    html_out = convert_math(src, display=display)
    m = _MROW_RE.search(html_out)
    assert m, f"no <mrow> found in output for {src!r}"
    return m.group(1)
