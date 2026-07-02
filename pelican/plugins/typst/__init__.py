"""
Pelican plugin: read and convert .typ (Typst) source files into HTML,
the same way Pelican natively handles .md and .rst files.

Install with `pip install .` from the pelican-typst project root. Once
installed, Pelican auto-discovers it -- no PLUGINS entry required. If
you have an explicit PLUGINS list already (or are using `pip install -e .`,
where auto-discovery doesn't apply -- see README), add the short name:

    PLUGINS = ["typst"]

No external Typst installation is required -- this reads and converts
the Typst source directly in Python.
"""

from pelican import signals

from .reader import TypstReader


def add_reader(readers):
    readers.reader_classes["typ"] = TypstReader


def register():
    signals.readers_init.connect(add_reader)
