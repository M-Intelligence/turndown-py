from __future__ import annotations

import re
from typing import Dict, List

from .html_parser import DomNode
from .rules import Rule
from .utilities import escape_markdown, repeat, trim_newlines


def build_rules() -> Dict[str, Rule]:
    rules: Dict[str, Rule] = {}

    rules["paragraph"] = Rule(
        filter="p",
        replacement=_paragraph_replacement,
    )

    rules["lineBreak"] = Rule(
        filter="br",
        replacement=_line_break_replacement,
    )

    rules["heading"] = Rule(
        filter=["h1", "h2", "h3", "h4", "h5", "h6"],
        replacement=_heading_replacement,
    )

    rules["blockquote"] = Rule(
        filter="blockquote",
        replacement=_blockquote_replacement,
    )

    rules["list"] = Rule(
        filter=["ul", "ol"],
        replacement=_list_replacement,
    )

    rules["listItem"] = Rule(
        filter="li",
        replacement=_list_item_replacement,
    )

    rules["indentedCodeBlock"] = Rule(
        filter=_indented_code_filter,
        replacement=_indented_code_replacement,
    )

    rules["fencedCodeBlock"] = Rule(
        filter=_fenced_code_filter,
        replacement=_fenced_code_replacement,
    )

    rules["horizontalRule"] = Rule(
        filter="hr",
        replacement=_horizontal_rule_replacement,
    )

    rules["inlineLink"] = Rule(
        filter=_inline_link_filter,
        replacement=_inline_link_replacement,
    )

    rules["referenceLink"] = ReferenceLinkRule()

    rules["emphasis"] = Rule(
        filter=["em", "i"],
        replacement=_emphasis_replacement,
    )

    rules["strong"] = Rule(
        filter=["strong", "b"],
        replacement=_strong_replacement,
    )

    rules["code"] = Rule(
        filter=_code_filter,
        replacement=_code_replacement,
    )

    rules["image"] = Rule(
        filter="img",
        replacement=_image_replacement,
    )

    return rules


# ---- paragraphs ----


def _paragraph_replacement(content: str, node: DomNode, options: Dict) -> str:
    return "\n\n" + content + "\n\n"


def _line_break_replacement(content: str, node: DomNode, options: Dict) -> str:
    return options["br"] + "\n"


def _horizontal_rule_replacement(content: str, node: DomNode, options: Dict) -> str:
    return "\n\n" + options["hr"] + "\n\n"


# ---- heading ----


def _heading_replacement(content: str, node: DomNode, options: Dict) -> str:
    h_level = int(node.nodeName[1])
    if options.get("headingStyle") == "setext" and h_level < 3:
        underline = repeat("=" if h_level == 1 else "-", len(content))
        return "\n\n" + content + "\n" + underline + "\n\n"
    return "\n\n" + repeat("#", h_level) + " " + content + "\n\n"


# ---- blockquote ----


def _blockquote_replacement(content: str, node: DomNode, options: Dict) -> str:
    content = re.sub(r"^", "> ", trim_newlines(content), flags=re.MULTILINE)
    return "\n\n" + content + "\n\n"


# ---- list ----


def _list_replacement(content: str, node: DomNode, options: Dict) -> str:
    parent = node.parentNode
    if parent is not None and parent.nodeName == "LI" and parent.lastElementChild is node:
        return "\n" + content
    return "\n\n" + content + "\n\n"


# ---- list item ----


def _list_item_replacement(content: str, node: DomNode, options: Dict) -> str:
    prefix = options.get("bulletListMarker", "*") + "   "
    parent = node.parentNode
    if parent is not None and parent.nodeName == "OL":
        start = parent.getAttribute("start")
        # find index within parent's element children
        children = parent.children
        try:
            index = children.index(node)
        except ValueError:
            index = 0
        if start:
            prefix = str(int(start) + index) + ".  "
        else:
            prefix = str(index + 1) + ".  "

    is_paragraph = bool(re.search(r"\n$", content))
    content = trim_newlines(content) + ("\n" if is_paragraph else "")
    content = re.sub(r"\n", "\n" + " " * len(prefix), content)
    suffix = "\n" if node.nextSibling is not None else ""
    return prefix + content + suffix


# ---- indented code block ----


def _indented_code_filter(node: DomNode, options: Dict) -> bool:
    return (
        options.get("codeBlockStyle") == "indented"
        and node.nodeName == "PRE"
        and node.firstChild is not None
        and node.firstChild.nodeName == "CODE"
    )


def _indented_code_replacement(content: str, node: DomNode, options: Dict) -> str:
    code_text = node.firstChild.textContent if node.firstChild else ""
    code_text = re.sub(r"\n", "\n    ", code_text) if node.firstChild else ""
    return "\n\n    " + code_text + "\n\n"


# ---- fenced code block ----


def _fenced_code_filter(node: DomNode, options: Dict) -> bool:
    return (
        options.get("codeBlockStyle") == "fenced"
        and node.nodeName == "PRE"
        and node.firstChild is not None
        and node.firstChild.nodeName == "CODE"
    )


def _fenced_code_replacement(content: str, node: DomNode, options: Dict) -> str:
    first_child = node.firstChild
    class_name = first_child.getAttribute("class") if first_child else ""
    language_match = re.search(r"language-(\S+)", class_name)
    language = language_match.group(1) if language_match else ""

    code = first_child.textContent if first_child else ""

    fence_char = options.get("fence", "```")[0]
    fence_size = 3

    fence_in_code_regex = re.compile(r"^" + re.escape(fence_char) + r"{3,}", re.MULTILINE)
    for match in fence_in_code_regex.finditer(code):
        if len(match.group(0)) >= fence_size:
            fence_size = len(match.group(0)) + 1

    fence = repeat(fence_char, fence_size)

    return "\n\n" + fence + language + "\n" + re.sub(r"\n\Z", "", code) + "\n" + fence + "\n\n"


# ---- inline link ----


def _inline_link_filter(node: DomNode, options: Dict) -> bool:
    return (
        options.get("linkStyle") == "inlined"
        and node.nodeName == "A"
        and bool(node.getAttribute("href"))
    )


def _inline_link_replacement(content: str, node: DomNode, options: Dict) -> str:
    href = _escape_link_destination(node.getAttribute("href"))
    title = _escape_link_title(_clean_attribute(node.getAttribute("title")))
    title_part = ' "' + title + '"' if title else ""
    return "[" + content + "](" + href + title_part + ")"


# ---- reference link ----


class ReferenceLinkRule(Rule):
    def __init__(self) -> None:
        super().__init__(
            filter=self._filter,
            replacement=self._replacement,
            append=self._append,
        )
        self.references: List[str] = []

    def _filter(self, node: DomNode, options: Dict) -> bool:
        return (
            options.get("linkStyle") == "referenced"
            and node.nodeName == "A"
            and bool(node.getAttribute("href"))
        )

    def _replacement(self, content: str, node: DomNode, options: Dict) -> str:
        href = _escape_link_destination(node.getAttribute("href"))
        title = _clean_attribute(node.getAttribute("title"))
        if title:
            title = ' "' + _escape_link_title(title) + '"'

        link_ref_style = options.get("linkReferenceStyle", "full")

        if link_ref_style == "collapsed":
            replacement = "[" + content + "][]"
            reference = "[" + content + "]: " + href + title
        elif link_ref_style == "shortcut":
            replacement = "[" + content + "]"
            reference = "[" + content + "]: " + href + title
        else:
            ref_id = len(self.references) + 1
            replacement = "[" + content + "][" + str(ref_id) + "]"
            reference = "[" + str(ref_id) + "]: " + href + title

        self.references.append(reference)
        return replacement

    def _append(self, options: Dict) -> str:
        if self.references:
            result = "\n\n" + "\n".join(self.references) + "\n\n"
            self.references = []
            return result
        return ""


# ---- emphasis ----


def _emphasis_replacement(content: str, node: DomNode, options: Dict) -> str:
    if not content.strip():
        return ""
    return options["emDelimiter"] + content + options["emDelimiter"]


# ---- strong ----


def _strong_replacement(content: str, node: DomNode, options: Dict) -> str:
    if not content.strip():
        return ""
    return options["strongDelimiter"] + content + options["strongDelimiter"]


# ---- code ----


def _code_filter(node: DomNode, options: Dict) -> bool:
    has_siblings = node.previousSibling is not None or node.nextSibling is not None
    is_code_block = (
        node.parentNode is not None and node.parentNode.nodeName == "PRE" and not has_siblings
    )
    return node.nodeName == "CODE" and not is_code_block


def _code_replacement(content: str, node: DomNode, options: Dict) -> str:
    if not content:
        return ""
    content = re.sub(r"\r?\n|\r", " ", content)

    extra_space = " " if re.search(r"^`|^ .*?[^ ].* $|`$", content) else ""
    delimiter = "`"
    matches = re.findall(r"`+", content)
    while delimiter in matches:
        delimiter = delimiter + "`"

    return delimiter + extra_space + content + extra_space + delimiter


# ---- image ----


def _image_replacement(content: str, node: DomNode, options: Dict) -> str:
    alt = escape_markdown(_clean_attribute(node.getAttribute("alt")))
    src = _escape_link_destination(node.getAttribute("src") or "")
    title = _clean_attribute(node.getAttribute("title"))
    title_part = ' "' + _escape_link_title(title) + '"' if title else ""
    return "![" + alt + "](" + src + title_part + ")" if src else ""


# ---- helpers ----


def _clean_attribute(attribute: str) -> str:
    if not attribute:
        return ""
    return re.sub(r"(\n+\s*)+", "\n", attribute)


def _escape_link_destination(destination: str) -> str:
    escaped = re.sub(r"([<>()])", r"\\\1", destination)
    if " " in escaped:
        return "<" + escaped + ">"
    return escaped


def _escape_link_title(title: str) -> str:
    return title.replace('"', '\\"')
