from __future__ import annotations

import re
from typing import Any, Dict, FrozenSet, List

from .html_parser import DomNode, is_element

# ---- object merge ----


def extend(destination: Dict[str, Any], *sources: Dict[str, Any]) -> Dict[str, Any]:
    for source in sources:
        for key, value in source.items():
            destination[key] = value
    return destination


# ---- string repetition ----


def repeat(character: str, count: int) -> str:
    return character * count


# ---- newline trimming ----


def trim_leading_newlines(string: str) -> str:
    return re.sub(r"^\n*", "", string)


def trim_trailing_newlines(string: str) -> str:
    idx = len(string)
    while idx > 0 and string[idx - 1] == "\n":
        idx -= 1
    return string[:idx]


def trim_newlines(string: str) -> str:
    return trim_trailing_newlines(trim_leading_newlines(string))


# ---- block / void element sets ----

_BLOCK_ELEMENTS: FrozenSet[str] = frozenset(
    {
        "ADDRESS",
        "ARTICLE",
        "ASIDE",
        "AUDIO",
        "BLOCKQUOTE",
        "BODY",
        "CANVAS",
        "CENTER",
        "DD",
        "DIR",
        "DIV",
        "DL",
        "DT",
        "FIELDSET",
        "FIGCAPTION",
        "FIGURE",
        "FOOTER",
        "FORM",
        "FRAMESET",
        "H1",
        "H2",
        "H3",
        "H4",
        "H5",
        "H6",
        "HEADER",
        "HGROUP",
        "HR",
        "HTML",
        "ISINDEX",
        "LI",
        "MAIN",
        "MENU",
        "NAV",
        "NOFRAMES",
        "NOSCRIPT",
        "OL",
        "OUTPUT",
        "P",
        "PRE",
        "SECTION",
        "TABLE",
        "TBODY",
        "TD",
        "TFOOT",
        "TH",
        "THEAD",
        "TR",
        "UL",
    }
)


def is_block(node: DomNode) -> bool:
    return is_element(node) and node.nodeName in _BLOCK_ELEMENTS


_VOID_ELEMENTS: FrozenSet[str] = frozenset(
    {
        "AREA",
        "BASE",
        "BR",
        "COL",
        "COMMAND",
        "EMBED",
        "HR",
        "IMG",
        "INPUT",
        "KEYGEN",
        "LINK",
        "META",
        "PARAM",
        "SOURCE",
        "TRACK",
        "WBR",
    }
)


def is_void(node: DomNode) -> bool:
    return is_element(node) and node.nodeName in _VOID_ELEMENTS


def has_void(node: DomNode) -> bool:
    if not is_element(node):
        return False
    for tag in _VOID_ELEMENTS:
        if node.getElementsByTagName(tag):
            return True
    return False


_MEANINGFUL_WHEN_BLANK: FrozenSet[str] = frozenset(
    {
        "A",
        "TABLE",
        "THEAD",
        "TBODY",
        "TFOOT",
        "TH",
        "TD",
        "IFRAME",
        "SCRIPT",
        "AUDIO",
        "VIDEO",
    }
)


def is_meaningful_when_blank(node: DomNode) -> bool:
    return is_element(node) and node.nodeName in _MEANINGFUL_WHEN_BLANK


def has_meaningful_when_blank(node: DomNode) -> bool:
    if not is_element(node):
        return False
    for tag in _MEANINGFUL_WHEN_BLANK:
        if node.getElementsByTagName(tag):
            return True
    return False


# ---- escape Markdown syntax ----

_MARKDOWN_ESCAPES: List[List[Any]] = [
    [re.compile(r"\\"), r"\\\\"],
    [re.compile(r"\*"), r"\*"],
    [re.compile(r"^-"), r"\-"],
    [re.compile(r"^\+ "), r"\+ "],
    [re.compile(r"^(=+)"), r"\\\1"],
    [re.compile(r"^(#{1,6}) "), r"\\\1 "],
    [re.compile(r"`"), r"\`"],
    [re.compile(r"^~~~"), r"\~~~"],
    [re.compile(r"\["), r"\["],
    [re.compile(r"\]"), r"\]"],
    [re.compile(r"^>"), r"\>"],
    [re.compile(r"_"), r"\_"],
    [re.compile(r"^(\d+)\. "), r"\1\\. "],
]


def escape_markdown(string: str) -> str:
    result = string
    for pattern, replacement in _MARKDOWN_ESCAPES:
        result = pattern.sub(replacement, result)
    return result
