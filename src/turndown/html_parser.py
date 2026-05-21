from __future__ import annotations

from html import escape as _html_escape
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "command",
        "embed",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

_RAW_TEXT_ELEMENTS = frozenset({"script", "style", "textarea", "title"})


class DomNode:
    __slots__ = (
        "nodeType",
        "nodeName",
        "nodeValue",
        "parentNode",
        "childNodes",
        "_attrs",
        "isBlock",
        "isCode",
        "isBlank",
        "flankingWhitespace",
    )

    def __init__(
        self,
        nodeType: int,
        nodeName: str,
        nodeValue: Optional[str] = None,
    ) -> None:
        self.nodeType = nodeType
        self.nodeName = nodeName
        self.nodeValue = nodeValue
        self.parentNode: Optional[DomNode] = None
        self.childNodes: List[DomNode] = []
        self._attrs: Dict[str, str] = {}
        self.isBlock = False
        self.isCode = False
        self.isBlank = False
        self.flankingWhitespace: Optional[Dict[str, str]] = None

    # ---- computed properties matching JS DOM ----

    @property
    def textContent(self) -> str:
        parts: List[str] = []
        for child in self.childNodes:
            if child.nodeType == 3:
                parts.append(child.nodeValue or "")
            elif child.nodeType == 1:
                parts.append(child.textContent)
        return "".join(parts)

    @property
    def firstChild(self) -> Optional[DomNode]:
        return self.childNodes[0] if self.childNodes else None

    @property
    def previousSibling(self) -> Optional[DomNode]:
        parent = self.parentNode
        if parent is None:
            return None
        idx = parent._index_of(self)
        if idx is not None and idx > 0:
            return parent.childNodes[idx - 1]
        return None

    @property
    def nextSibling(self) -> Optional[DomNode]:
        parent = self.parentNode
        if parent is None:
            return None
        idx = parent._index_of(self)
        if idx is not None and idx < len(parent.childNodes) - 1:
            return parent.childNodes[idx + 1]
        return None

    def _index_of(self, child: DomNode) -> Optional[int]:
        for i, c in enumerate(self.childNodes):
            if c is child:
                return i
        return None

    def getAttribute(self, name: str) -> str:
        return self._attrs.get(name, "")

    def getElementsByTagName(self, tagName: str) -> List[DomNode]:
        result: List[DomNode] = []
        tag_upper = tagName.upper()
        for child in list(self.childNodes):
            if child.nodeType == 1 and child.nodeName == tag_upper:
                result.append(child)
            if child.nodeType == 1:
                result.extend(child.getElementsByTagName(tagName))
        return result

    @property
    def children(self) -> List[DomNode]:
        return [c for c in self.childNodes if c.nodeType == 1]

    @property
    def lastElementChild(self) -> Optional[DomNode]:
        for child in reversed(self.childNodes):
            if child.nodeType == 1:
                return child
        return None

    # ---- mutation ----

    def cloneNode(self, deep: bool = False) -> DomNode:
        new = DomNode(self.nodeType, self.nodeName, self.nodeValue)
        new._attrs = dict(self._attrs)
        if deep:
            for child in self.childNodes:
                cloned = child.cloneNode(True)
                new.appendChild(cloned)
        return new

    def appendChild(self, child: DomNode) -> DomNode:
        child.parentNode = self
        self.childNodes.append(child)
        return child

    def insertBefore(self, newChild: DomNode, refChild: DomNode) -> DomNode:
        idx = self._index_of(refChild)
        if idx is None:
            raise ValueError("refChild is not a child of this node")
        newChild.parentNode = self
        self.childNodes.insert(idx, newChild)
        return newChild

    def removeChild(self, child: DomNode) -> DomNode:
        self.childNodes.remove(child)
        child.parentNode = None
        return child

    # ---- serialization ----

    @property
    def outerHTML(self) -> str:
        if self.nodeType == 3:
            return _html_escape(self.nodeValue or "", quote=False)
        tag = self.nodeName.lower()
        attrs_parts: List[str] = []
        for name, value in self._attrs.items():
            if value is not None:
                attrs_parts.append(f'{name}="{_html_escape(str(value), quote=True)}"')
            else:
                attrs_parts.append(name)
        attrs_str = " " + " ".join(attrs_parts) if attrs_parts else ""
        if tag in _VOID_ELEMENTS:
            return f"<{tag}{attrs_str}>"
        inner = "".join(c.outerHTML for c in self.childNodes)
        return f"<{tag}{attrs_str}>{inner}</{tag}>"

    def __repr__(self) -> str:
        if self.nodeType == 3:
            return f"TextNode({self.nodeValue!r})"
        return f"ElementNode({self.nodeName})"


# ---- helpers ----


def create_text_node(text: str) -> DomNode:
    return DomNode(3, "#text", text)


def create_element_node(
    tag: str,
    attrs: Optional[List[Tuple[str, Optional[str]]]] = None,
) -> DomNode:
    node = DomNode(1, tag.upper())
    if attrs:
        for name, value in attrs:
            node._attrs[name] = value if value is not None else ""
    return node


def is_element(node: DomNode) -> bool:
    return node.nodeType == 1


def is_text(node: DomNode) -> bool:
    return node.nodeType == 3


# ---- HTML parser ----


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = create_element_node("#document")
        self._stack: List[DomNode] = [self.root]
        self._raw_text = False
        self._current_raw_tag = ""

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if self._raw_text:
            return
        node = create_element_node(tag, attrs)
        self._stack[-1].appendChild(node)
        if tag not in _VOID_ELEMENTS:
            self._stack.append(node)
        if tag in _RAW_TEXT_ELEMENTS:
            self._raw_text = True
            self._current_raw_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if self._raw_text and tag == self._current_raw_tag:
            self._raw_text = False
            self._current_raw_tag = ""
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].nodeName == tag.upper():
                self._stack = self._stack[:i]
                break

    def handle_data(self, data: str) -> None:
        if not data:
            return
        text_node = create_text_node(data)
        self._stack[-1].appendChild(text_node)

    def handle_entityref(self, name: str) -> None:
        char = self.unescape(f"&{name};")
        if char:
            self.handle_data(char)

    def handle_comment(self, data: str) -> None:
        pass


def parse_html(html: str) -> DomNode:
    if not html:
        root = create_element_node("#document")
        return root
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()
    return builder.root
