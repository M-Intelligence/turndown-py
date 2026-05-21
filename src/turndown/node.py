from __future__ import annotations

import re
from typing import Dict

from .html_parser import DomNode, is_element, is_text
from .utilities import (
    has_meaningful_when_blank,
    has_void,
    is_block,
    is_meaningful_when_blank,
    is_void,
)


def annotate_node(node: DomNode, options: Dict) -> DomNode:
    node.isBlock = is_block(node)
    node.isCode = node.nodeName == "CODE" or (
        node.parentNode is not None and node.parentNode.isCode
    )
    node.isBlank = _is_blank(node)
    node.flankingWhitespace = _flanking_whitespace(node, options)
    return node


def _is_blank(node: DomNode) -> bool:
    return (
        not is_void(node)
        and not is_meaningful_when_blank(node)
        and bool(re.match(r"^\s*$", node.textContent))
        and not has_void(node)
        and not has_meaningful_when_blank(node)
    )


def _flanking_whitespace(node: DomNode, options: Dict) -> Dict[str, str]:
    if node.isBlock or (options.get("preformattedCode") and node.isCode):
        return {"leading": "", "trailing": ""}

    edges = _edge_whitespace(node.textContent)

    if edges["leadingAscii"] and _is_flanked_by_whitespace("left", node, options):
        edges["leading"] = edges["leadingNonAscii"]

    if edges["trailingAscii"] and _is_flanked_by_whitespace("right", node, options):
        edges["trailing"] = edges["trailingNonAscii"]

    return {"leading": edges["leading"], "trailing": edges["trailing"]}


_EDGE_WHITESPACE_RE = re.compile(r"^(([ \t\r\n]*)(\s*))(?:(?=\S)[\s\S]*\S)?((\s*?)([ \t\r\n]*))$")


def _edge_whitespace(string: str) -> Dict[str, str]:
    m = _EDGE_WHITESPACE_RE.match(string)
    if m:
        return {
            "leading": m.group(1),
            "leadingAscii": m.group(2),
            "leadingNonAscii": m.group(3),
            "trailing": m.group(4),
            "trailingNonAscii": m.group(5),
            "trailingAscii": m.group(6),
        }
    return {
        "leading": "",
        "leadingAscii": "",
        "leadingNonAscii": "",
        "trailing": "",
        "trailingNonAscii": "",
        "trailingAscii": "",
    }


def _is_flanked_by_whitespace(side: str, node: DomNode, options: Dict) -> bool:
    if side == "left":
        sibling = node.previousSibling
        reg_exp = re.compile(r" $")
    else:
        sibling = node.nextSibling
        reg_exp = re.compile(r"^ ")

    if sibling is None:
        return False

    if is_text(sibling):
        return bool(reg_exp.search(sibling.nodeValue or ""))
    elif options.get("preformattedCode") and sibling.nodeName == "CODE":
        return False
    elif is_element(sibling) and not is_block(sibling):
        return bool(reg_exp.search(sibling.textContent))

    return False
