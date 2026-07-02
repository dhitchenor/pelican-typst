"""Pelican Reader for .typ (Typst) source files."""

from datetime import date, datetime
from typing import Any, Dict, Tuple

from pelican.readers import BaseReader
from pelican.utils import pelican_open

from .markup import TypstToHTML
from .metadata import extract_metadata


def _normalize(value):
    """Coerce parsed metadata values (which may be Python lists, dates,
    bools, etc. straight out of YAML or the Typst dict parser) into the
    strings Pelican's built-in metadata processors expect."""
    if isinstance(value, (list, tuple)):
        return ", ".join(_normalize(v) for v in value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class TypstReader(BaseReader):
    enabled = True
    file_extensions = ["typ"]

    # Pelican's BaseReader.read() has no type annotations -- it's a
    # genuine no-op placeholder ("content = None; return content,
    # metadata") that every real reader is meant to override. Static
    # checkers that infer types from that unannotated body see it as
    # `-> tuple[None, dict]`, then flag any real subclass -- including
    # Pelican's own Markdown/RST readers, if they were checked this
    # strictly -- for returning actual string content instead of None.
    # This is a false positive against the base class's own typing,
    # not a real incompatibility; content is always a str here.
    def read(self, source_path) -> Tuple[str, Dict[str, Any]]:  # type: ignore[override]
        with pelican_open(source_path) as text:
            raw_metadata, body = extract_metadata(text)

        metadata = {}
        for name, value in raw_metadata.items():
            name = name.lower()
            metadata[name] = self.process_metadata(name, _normalize(value))

        content = TypstToHTML().convert(body)
        return content, metadata
