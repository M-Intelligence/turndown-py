from __future__ import annotations

import re
from typing import Callable, Optional

from .html_parser import DomNode, is_element, is_text


def collapse_whitespace(
    element: DomNode,
    is_block: Callable[[DomNode], bool],
    is_void: Callable[[DomNode], bool],
    is_pre: Optional[Callable[[DomNode], bool]] = None,
) -> None:
    if is_pre is None:
        is_pre = _default_is_pre

    if not element.firstChild or is_pre(element):
        return

    prev_text: Optional[DomNode] = None
    keep_leading_ws = False

    prev: Optional[DomNode] = None
    node = _next(prev, element, is_pre)

    while node is not element:
        if is_text(node):
            text = re.sub(r"[ \r\n\t]+", " ", node.nodeValue or "")

            if (
                (not prev_text or prev_text.nodeValue and prev_text.nodeValue.endswith(" "))
                and not keep_leading_ws
                and text.startswith(" ")
            ):
                text = text[1:]

            if not text:
                node = _remove(node)
                continue

            node.nodeValue = text
            prev_text = node

        elif is_element(node):
            if is_block(node) or node.nodeName == "BR":
                if prev_text is not None and prev_text.nodeValue is not None:
                    prev_text.nodeValue = re.sub(r" $", "", prev_text.nodeValue)
                prev_text = None
                keep_leading_ws = False
            elif is_void(node) or is_pre(node):
                prev_text = None
                keep_leading_ws = True
            elif prev_text is not None:
                keep_leading_ws = False

        else:
            node = _remove(node)
            continue

        next_node = _next(prev, node, is_pre)
        prev = node
        node = next_node

    if prev_text is not None and prev_text.nodeValue is not None:
        prev_text.nodeValue = re.sub(r" $", "", prev_text.nodeValue)
        if not prev_text.nodeValue:
            _remove(prev_text)


def _remove(node: DomNode) -> DomNode:
    nxt = node.nextSibling or node.parentNode
    if node.parentNode is not None:
        node.parentNode.removeChild(node)
    return nxt if nxt is not None else node


def _next(
    prev: Optional[DomNode],
    current: DomNode,
    is_pre: Callable[[DomNode], bool],
) -> DomNode:
    if (prev is not None and prev.parentNode is current) or is_pre(current):
        nxt = current.nextSibling or current.parentNode
        return nxt if nxt is not None else current
    return current.firstChild or current.nextSibling or current.parentNode or current


def _default_is_pre(node: DomNode) -> bool:
    return node.nodeName == "PRE"
