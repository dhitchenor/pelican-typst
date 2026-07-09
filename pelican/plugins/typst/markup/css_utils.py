"""
Typst value -> CSS mapping helpers: colors, sizes, font weights, and the
layout-wrapper CSS builders (align/box/pad/place/scale). Pure functions,
no shared state.
"""

import re

from .patterns import _ALIGN_H_MAP, _NAMED_COLORS, _WEIGHT_MAP
from .text_utils import _split_top_level


def _parse_color(value):
    value = value.strip()
    m = re.match(r'^rgb\(\s*"(#[0-9a-fA-F]{3,8})"\s*\)$', value)
    if m:
        return m.group(1)
    m = re.match(
        r'^rgb\(\s*([\d.]+%?)\s*,\s*([\d.]+%?)\s*,\s*([\d.]+%?)\s*'
        r'(?:,\s*([\d.]+%?)\s*)?\)$', value
    )
    if m:
        r, g, b, a = m.groups()
        return f"rgba({r}, {g}, {b}, {a})" if a else f"rgb({r}, {g}, {b})"
    m = re.match(r'^"(#[0-9a-fA-F]{3,8})"$', value)
    if m:
        return m.group(1)
    bare = value.strip('"')
    if bare.lower() in _NAMED_COLORS:
        return bare.lower()
    return None


def _parse_size(value):
    value = value.strip()
    if re.match(r"^-?\d+(\.\d+)?(pt|em|cm|mm|in|%)$", value):
        return value
    return None


def _parse_stroke(value):
    """Parse a Typst stroke value, e.g. `0.5pt + gray`, `1pt`, or `red`,
    into a CSS border spec like "0.5pt solid gray". Falls back to
    sensible defaults for whichever half (width/color) isn't present or
    isn't recognised."""
    parts = [p.strip() for p in _split_top_level(value, "+")]
    width = None
    color = None
    for p in parts:
        size = _parse_size(p)
        if size:
            width = size
            continue
        c = _parse_color(p)
        if c:
            color = c
    return f"{width or '1pt'} solid {color or 'currentColor'}"


def _map_weight(value):
    v = value.strip().strip('"')
    if v in _WEIGHT_MAP:
        return _WEIGHT_MAP[v]
    if re.match(r"^\d+$", v):
        return v
    return None


def _parse_text_style_args(args_src):
    css = []
    for part in _split_top_level(args_src, ","):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        key, value = key.strip(), value.strip()
        if key == "fill":
            color = _parse_color(value)
            if color:
                css.append(f"color: {color}")
        elif key == "size":
            size = _parse_size(value)
            if size:
                css.append(f"font-size: {size}")
        elif key == "weight":
            weight = _map_weight(value)
            if weight:
                css.append(f"font-weight: {weight}")
        elif key == "style":
            v = value.strip('"')
            if v in ("italic", "normal", "oblique"):
                css.append(f"font-style: {v}")
        elif key == "font":
            css.append('font-family: "' + value.strip('"') + '"')
    return "; ".join(css)


def _align_css(value):
    tokens = [t.strip() for t in value.split("+")]
    for t in tokens:
        if t in _ALIGN_H_MAP:
            return f"text-align: {_ALIGN_H_MAP[t]};"
    return ""


def _box_css(named):
    css = []
    if "width" in named:
        w = _parse_size(named["width"]) or named["width"].strip('"')
        css.append(f"width: {w};")
    if "height" in named:
        h = _parse_size(named["height"]) or named["height"].strip('"')
        css.append(f"height: {h};")
    if "fill" in named:
        color = _parse_color(named["fill"])
        if color:
            css.append(f"background-color: {color};")
    if "inset" in named:
        inset = _parse_size(named["inset"])
        if inset:
            css.append(f"padding: {inset};")
    if "radius" in named:
        radius = _parse_size(named["radius"])
        if radius:
            css.append(f"border-radius: {radius};")
    if "stroke" in named:
        css.append("border: 1px solid currentColor;")
    return " ".join(css)


def _pad_css(named, positional):
    if positional:
        val = _parse_size(positional[0]) or positional[0]
        return f"padding: {val};"
    css = []
    for key, css_key in (("left", "padding-left"), ("right", "padding-right"),
                          ("top", "padding-top"), ("bottom", "padding-bottom")):
        if key in named:
            v = _parse_size(named[key]) or named[key]
            css.append(f"{css_key}: {v};")
    if "x" in named:
        v = _parse_size(named["x"]) or named["x"]
        css.append(f"padding-left: {v}; padding-right: {v};")
    if "y" in named:
        v = _parse_size(named["y"]) or named["y"]
        css.append(f"padding-top: {v}; padding-bottom: {v};")
    return " ".join(css)


def _place_css(target, named):
    css = ["position: absolute;"]
    tokens = [t.strip() for t in target.split("+")]
    if "top" in tokens:
        css.append("top: 0;")
    if "bottom" in tokens:
        css.append("bottom: 0;")
    if "left" in tokens or "start" in tokens:
        css.append("left: 0;")
    if "right" in tokens or "end" in tokens:
        css.append("right: 0;")
    if "center" in tokens or "horizon" in tokens:
        css.append("margin: auto;")
    if "dx" in named:
        dx = _parse_size(named["dx"]) or named["dx"]
        css.append(f"margin-left: {dx};")
    if "dy" in named:
        dy = _parse_size(named["dy"]) or named["dy"]
        css.append(f"margin-top: {dy};")
    return " ".join(css)


def _scale_factor(value):
    value = value.strip()
    m = re.match(r"^(-?\d+(?:\.\d+)?)%$", value)
    if m:
        return str(float(m.group(1)) / 100)
    return value
