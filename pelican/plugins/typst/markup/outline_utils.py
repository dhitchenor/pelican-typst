"""
Turns the flat, document-order heading list into a nested <ul> tree for
#outline(). Pure functions, no shared state.
"""

import html


def _entries_to_tree(entries):
    """Flat [(level, id, text), ...] in document order -> a nested tree
    of {"id", "text", "children"} dicts. Robust to level skips (e.g.
    jumping from level 1 straight to level 3)."""
    root = []
    stack = [(0, root)]
    for level, hid, text in entries:
        while stack and stack[-1][0] >= level:
            stack.pop()
        node = {"id": hid, "text": text, "children": []}
        stack[-1][1].append(node)
        stack.append((level, node["children"]))
    return root


def _render_outline_tree(nodes):
    if not nodes:
        return ""
    parts = ["<ul>"]
    for node in nodes:
        parts.append(f'<li><a href="#{html.escape(node["id"], quote=True)}">'
                      f'{node["text"]}</a>')
        if node["children"]:
            parts.append(_render_outline_tree(node["children"]))
        parts.append("</li>")
    parts.append("</ul>")
    return "".join(parts)
