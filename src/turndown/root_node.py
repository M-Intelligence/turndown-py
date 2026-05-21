from __future__ import annotations

from typing import Dict, Optional

from .collapse_whitespace import collapse_whitespace
from .html_parser import DomNode, create_element_node, is_element, parse_html
from .utilities import is_block, is_void


def create_root_node(input: str, options: Dict) -> DomNode:
    if isinstance(input, str):
        doc = parse_html('<x-turndown id="turndown-root">' + input + "</x-turndown>")
        root = _get_element_by_id(doc, "turndown-root")
        if root is None:
            root = create_element_node("x-turndown")
    else:
        root = input.cloneNode(True)

    collapse_whitespace(
        element=root,
        is_block=is_block,
        is_void=is_void,
        is_pre=_is_pre_or_code if options.get("preformattedCode") else None,
    )

    return root


def _get_element_by_id(node: DomNode, id: str) -> Optional[DomNode]:
    if is_element(node) and node.getAttribute("id") == id:
        return node
    for child in node.childNodes:
        result = _get_element_by_id(child, id)
        if result is not None:
            return result
    return None


def _is_pre_or_code(node: DomNode) -> bool:
    return node.nodeName == "PRE" or node.nodeName == "CODE"
