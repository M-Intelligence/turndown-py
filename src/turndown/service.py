from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Union

from .commonmark_rules import build_rules
from .html_parser import DomNode, is_element, is_text
from .node import annotate_node
from .root_node import create_root_node
from .rules import FilterType, Rule, Rules
from .utilities import escape_markdown, extend, trim_leading_newlines, trim_trailing_newlines


class TurndownService:
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        defaults: Dict[str, Any] = {
            "rules": build_rules(),
            "headingStyle": "setext",
            "hr": "* * *",
            "bulletListMarker": "*",
            "codeBlockStyle": "indented",
            "fence": "```",
            "emDelimiter": "_",
            "strongDelimiter": "**",
            "linkStyle": "inlined",
            "linkReferenceStyle": "full",
            "br": "  ",
            "preformattedCode": False,
            "blankReplacement": self._default_blank_replacement,
            "keepReplacement": self._default_keep_replacement,
            "defaultReplacement": self._default_replacement,
        }
        if options is not None:
            self.options = extend(defaults, options)
        else:
            self.options = defaults
        self.rules = Rules(self.options)

    # ---- default replacement functions ----

    @staticmethod
    def _default_blank_replacement(content: str, node: DomNode, options: Dict = None) -> str:
        return "\n\n" if node.isBlock else ""

    @staticmethod
    def _default_keep_replacement(content: str, node: DomNode, options: Dict = None) -> str:
        if node.isBlock:
            return "\n\n" + node.outerHTML + "\n\n"
        return node.outerHTML

    @staticmethod
    def _default_replacement(content: str, node: DomNode, options: Dict = None) -> str:
        if node.isBlock:
            return "\n\n" + content + "\n\n"
        return content

    # ---- public API ----

    def turndown(self, input: str) -> str:
        self._reset_references()
        if not self._can_convert(input):
            raise TypeError(str(input) + " is not a string, or an element/document/fragment node.")

        if input == "":
            return ""

        root = create_root_node(input, self.options)
        output = self._process(root)
        return self._post_process(output)

    def _reset_references(self) -> None:
        for rule in self.rules.array:
            if hasattr(rule, "references"):
                rule.references = []

    def use(self, plugin: Union[Callable, List[Callable]]) -> "TurndownService":
        if isinstance(plugin, list):
            for p in plugin:
                self.use(p)
        elif callable(plugin):
            plugin(self)
        else:
            raise TypeError("plugin must be a Function or an Array of Functions")
        return self

    def add_rule(self, key: str, rule: Rule) -> "TurndownService":
        self.rules.add(key, rule)
        return self

    def keep(self, filter: FilterType) -> "TurndownService":
        self.rules.keep(filter)
        return self

    def remove(self, filter: FilterType) -> "TurndownService":
        self.rules.remove(filter)
        return self

    def escape(self, string: str) -> str:
        return escape_markdown(string)

    # ---- private methods ----

    def _process(self, parent_node: DomNode) -> str:
        output = ""
        for child in parent_node.childNodes:
            node = annotate_node(child, self.options)

            replacement = ""
            if is_text(node):
                replacement = node.nodeValue if node.isCode else self.escape(node.nodeValue or "")
            elif is_element(node):
                replacement = self._replacement_for_node(node)

            output = self._join(output, replacement)
        return output

    def _post_process(self, output: str) -> str:
        def _apply_append(rule: Rule, idx: int) -> None:
            nonlocal output
            if hasattr(rule, "append") and rule.append is not None:
                output = self._join(output, rule.append(self.options))

        self.rules.for_each(_apply_append)

        output = re.sub(r"^[\t\r\n]+", "", output)
        output = re.sub(r"[\t\r\n\s]+$", "", output)
        return output

    def _replacement_for_node(self, node: DomNode) -> str:
        rule = self.rules.for_node(node)
        content = self._process(node)
        whitespace = node.flankingWhitespace
        if whitespace and (whitespace.get("leading") or whitespace.get("trailing")):
            content = content.strip()

        leading = (whitespace or {}).get("leading", "")
        trailing = (whitespace or {}).get("trailing", "")
        return leading + rule["replacement"](content, node, self.options) + trailing

    @staticmethod
    def _join(output: str, replacement: str) -> str:
        s1 = trim_trailing_newlines(output)
        s2 = trim_leading_newlines(replacement)
        nls = max(len(output) - len(s1), len(replacement) - len(s2))
        separator = "\n\n"[:nls]
        return s1 + separator + s2

    @staticmethod
    def _can_convert(input: Any) -> bool:
        if input is None:
            return False
        if isinstance(input, str):
            return True
        if hasattr(input, "nodeType"):
            return input.nodeType in (1, 9, 11)
        return False
