from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from .html_parser import DomNode

FilterType = Union[str, List[str], Callable[[DomNode, Dict], bool]]


class Rule:
    def __init__(
        self,
        filter: FilterType,
        replacement: Callable[[str, DomNode, Dict], str],
        append: Optional[Callable[[Dict], str]] = None,
    ) -> None:
        self.filter = filter
        self.replacement = replacement
        self.append = append

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class Rules:
    def __init__(self, options: Dict) -> None:
        self.options = options
        self._keep: List[Dict] = []
        self._remove: List[Dict] = []

        self.blank_rule = {
            "replacement": options["blankReplacement"],
        }
        self.keep_replacement = options["keepReplacement"]
        self.default_rule = {
            "replacement": options["defaultReplacement"],
        }

        self.array: List[Rule] = []
        for key in options["rules"]:
            self.array.append(options["rules"][key])

    def add(self, key: str, rule: Rule) -> None:
        self.array.insert(0, rule)

    def keep(self, filter: FilterType) -> None:
        self._keep.insert(
            0,
            {
                "filter": filter,
                "replacement": self.keep_replacement,
            },
        )

    def remove(self, filter: FilterType) -> None:
        self._remove.insert(
            0,
            {
                "filter": filter,
                "replacement": _empty_replacement,
            },
        )

    def for_node(self, node: DomNode) -> Dict:
        if node.isBlank:
            return self.blank_rule

        rule = _find_rule(self.array, node, self.options)
        if rule is not None:
            return rule

        rule = _find_rule(self._keep, node, self.options)
        if rule is not None:
            return rule

        rule = _find_rule(self._remove, node, self.options)
        if rule is not None:
            return rule

        return self.default_rule

    def for_each(self, fn: Callable[[Rule, int], None]) -> None:
        for i, rule in enumerate(self.array):
            fn(rule, i)


def _find_rule(rules: List, node: DomNode, options: Dict) -> Optional[Any]:
    for rule in rules:
        if _filter_value(rule, node, options):
            return rule
    return None


def _empty_replacement(content: str, node: DomNode, options: Dict = None) -> str:
    return ""


def _filter_value(rule: Any, node: DomNode, options: Dict) -> bool:
    filter_val = rule["filter"] if isinstance(rule, dict) else rule.filter
    if isinstance(filter_val, str):
        return filter_val == node.nodeName.lower()
    elif isinstance(filter_val, list):
        return node.nodeName.lower() in filter_val
    elif callable(filter_val):
        return filter_val(node, options)
    else:
        raise TypeError("`filter` needs to be a string, array, or function")
