from __future__ import annotations

import pickle
import threading

from turndown import TurndownService
from turndown.html_parser import create_element_node, create_text_node
from turndown.node import _edge_whitespace
from turndown.utilities import (
    escape_markdown,
    extend,
    has_meaningful_when_blank,
    has_void,
    is_block,
    is_meaningful_when_blank,
    is_void,
    repeat,
    trim_leading_newlines,
    trim_newlines,
    trim_trailing_newlines,
)


class TestEdgeWhitespace:
    def _ews(self, leading_ascii, leading_non_ascii, trailing_non_ascii, trailing_ascii):
        return {
            "leading": leading_ascii + leading_non_ascii,
            "leadingAscii": leading_ascii,
            "leadingNonAscii": leading_non_ascii,
            "trailing": trailing_non_ascii + trailing_ascii,
            "trailingNonAscii": trailing_non_ascii,
            "trailingAscii": trailing_ascii,
        }

    def test_basic_ascii_whitespace(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"{ws}HELLO WORLD{ws}")
        expected = self._ews(ws, "", "", ws)
        assert result == expected

    def test_ascii_whitespace_with_single_char(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"{ws}H{ws}")
        expected = self._ews(ws, "", "", ws)
        assert result == expected

    def test_mixed_ascii_and_non_ascii_whitespace(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"{ws}\xa0{ws}HELLO{ws}WORLD{ws}\xa0{ws}")
        expected = self._ews(ws, f"\xa0{ws}", f"{ws}\xa0", ws)
        assert result == expected

    def test_non_ascii_surrounding(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"\xa0{ws}HELLO{ws}WORLD{ws}\xa0")
        expected = self._ews("", f"\xa0{ws}", f"{ws}\xa0", "")
        assert result == expected

    def test_only_non_ascii_whitespace(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"\xa0{ws}\xa0")
        expected = self._ews("", f"\xa0{ws}\xa0", "", "")
        assert result == expected

    def test_leading_ascii_then_non_ascii(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"{ws}\xa0{ws}")
        expected = self._ews(ws, f"\xa0{ws}", "", "")
        assert result == expected

    def test_leading_non_ascii_only(self):
        ws = "\r\n \t"
        result = _edge_whitespace(f"{ws}\xa0")
        expected = self._ews(ws, "\xa0", "", "")
        assert result == expected

    def test_no_whitespace(self):
        result = _edge_whitespace("HELLO WORLD")
        expected = self._ews("", "", "", "")
        assert result == expected

    def test_empty_string(self):
        result = _edge_whitespace("")
        expected = self._ews("", "", "", "")
        assert result == expected

    def test_long_string_performance(self):
        long_string = "TEST" + (" " * 32768) + "END"
        result = _edge_whitespace(long_string)
        expected = self._ews("", "", "", "")
        assert result == expected


class TestUtilities:
    def test_extend(self):
        dest = {"a": 1}
        result = extend(dest, {"b": 2}, {"c": 3})
        assert result == {"a": 1, "b": 2, "c": 3}
        assert result is dest

    def test_repeat(self):
        assert repeat("=", 5) == "====="
        assert repeat("*", 0) == ""
        assert repeat("ab", 3) == "ababab"

    def test_trim_leading_newlines(self):
        assert trim_leading_newlines("\n\nhello") == "hello"
        assert trim_leading_newlines("hello") == "hello"
        assert trim_leading_newlines("\n\n") == ""

    def test_trim_trailing_newlines(self):
        assert trim_trailing_newlines("hello\n\n") == "hello"
        assert trim_trailing_newlines("hello") == "hello"
        assert trim_trailing_newlines("\n\n") == ""

    def test_trim_newlines(self):
        assert trim_newlines("\n\nhello\n\n") == "hello"

    def test_is_block(self):
        p = create_element_node("p")
        assert is_block(p)
        span = create_element_node("span")
        assert not is_block(span)
        text = create_text_node("hello")
        assert not is_block(text)

    def test_is_void(self):
        br = create_element_node("br")
        assert is_void(br)
        hr = create_element_node("hr")
        assert is_void(hr)
        p = create_element_node("p")
        assert not is_void(p)

    def test_has_void(self):
        parent = create_element_node("div")
        child = create_element_node("br")
        parent.appendChild(child)
        assert has_void(parent)

    def test_is_meaningful_when_blank(self):
        a = create_element_node("a")
        assert is_meaningful_when_blank(a)
        p = create_element_node("p")
        assert not is_meaningful_when_blank(p)

    def test_has_meaningful_when_blank(self):
        parent = create_element_node("div")
        child = create_element_node("iframe")
        parent.appendChild(child)
        assert has_meaningful_when_blank(parent)

    def test_escape_markdown(self):
        assert escape_markdown("*hello*") == "\\*hello\\*"
        assert escape_markdown("_hello_") == "\\_hello\\_"
        assert escape_markdown("[hello]") == "\\[hello\\]"
        assert escape_markdown("`code`") == "\\`code\\`"
        assert escape_markdown("plain text") == "plain text"


class TestDomNode:
    def test_element_creation(self):
        node = create_element_node("div", [("class", "foo")])
        assert node.nodeName == "DIV"
        assert node.nodeType == 1
        assert node.getAttribute("class") == "foo"

    def test_text_node(self):
        node = create_text_node("hello")
        assert node.nodeName == "#text"
        assert node.nodeType == 3
        assert node.nodeValue == "hello"

    def test_text_content(self):
        parent = create_element_node("p")
        parent.appendChild(create_text_node("Hello "))
        child = create_element_node("strong")
        child.appendChild(create_text_node("world"))
        parent.appendChild(child)
        assert parent.textContent == "Hello world"

    def test_children(self):
        parent = create_element_node("div")
        c1 = create_element_node("p")
        c2 = create_element_node("span")
        t = create_text_node("text")
        parent.appendChild(c1)
        parent.appendChild(t)
        parent.appendChild(c2)
        assert parent.children == [c1, c2]

    def test_clone_deep(self):
        parent = create_element_node("div")
        child = create_element_node("p")
        child.appendChild(create_text_node("hello"))
        parent.appendChild(child)
        cloned = parent.cloneNode(True)
        assert cloned.nodeName == "DIV"
        assert len(cloned.childNodes) == 1
        assert cloned.childNodes[0].nodeName == "P"
        assert cloned.childNodes[0].childNodes[0].nodeValue == "hello"

    def test_clone_shallow(self):
        parent = create_element_node("div")
        child = create_element_node("p")
        parent.appendChild(child)
        cloned = parent.cloneNode(False)
        assert cloned.nodeName == "DIV"
        assert len(cloned.childNodes) == 0

    def test_siblings(self):
        parent = create_element_node("div")
        c1 = create_element_node("p")
        c2 = create_element_node("span")
        c3 = create_element_node("div")
        parent.appendChild(c1)
        parent.appendChild(c2)
        parent.appendChild(c3)
        assert c1.nextSibling is c2
        assert c2.nextSibling is c3
        assert c3.nextSibling is None
        assert c3.previousSibling is c2
        assert c2.previousSibling is c1
        assert c1.previousSibling is None

    def test_remove_child(self):
        parent = create_element_node("div")
        child = create_element_node("p")
        parent.appendChild(child)
        removed = parent.removeChild(child)
        assert removed is child
        assert child.parentNode is None
        assert len(parent.childNodes) == 0

    def test_outer_html(self):
        node = create_element_node("p")
        node.appendChild(create_text_node("hello"))
        assert node.outerHTML == "<p>hello</p>"

    def test_outer_html_with_attrs(self):
        node = create_element_node("a", [("href", "http://example.com"), ("title", "Example")])
        node.appendChild(create_text_node("click"))
        assert node.outerHTML == '<a href="http://example.com" title="Example">click</a>'

    def test_outer_html_void_element(self):
        node = create_element_node("br")
        assert node.outerHTML == "<br>"

    def test_outer_html_img(self):
        node = create_element_node("img", [("src", "logo.png"), ("alt", "Logo")])
        assert node.outerHTML == '<img src="logo.png" alt="Logo">'

    def test_get_elements_by_tag_name(self):
        parent = create_element_node("div")
        p1 = create_element_node("p")
        p1.appendChild(create_text_node("first"))
        p2 = create_element_node("p")
        p2.appendChild(create_text_node("second"))
        span = create_element_node("span")
        parent.appendChild(p1)
        parent.appendChild(span)
        parent.appendChild(p2)
        result = parent.getElementsByTagName("p")
        assert len(result) == 2
        assert result[0] is p1
        assert result[1] is p2

    def test_first_child(self):
        parent = create_element_node("div")
        assert parent.firstChild is None
        child = create_text_node("hello")
        parent.appendChild(child)
        assert parent.firstChild is child

    def test_last_element_child(self):
        parent = create_element_node("div")
        p1 = create_element_node("p")
        t = create_text_node("text")
        p2 = create_element_node("span")
        parent.appendChild(p1)
        parent.appendChild(t)
        parent.appendChild(p2)
        assert parent.lastElementChild is p2


class TestSerialization:
    def test_pickle_roundtrip(self):
        ts = TurndownService()
        pickled = pickle.dumps(ts)
        ts2 = pickle.loads(pickled)
        assert ts2.turndown("<p>Hello</p>").strip() == "Hello"

    def test_stateless(self):
        ts = TurndownService()
        result1 = ts.turndown("<p>Hello</p>")
        result2 = ts.turndown("<p>Hello</p>")
        assert result1 == result2


class TestThreadSafety:
    def test_concurrent_calls(self):
        ts = TurndownService()
        errors = []
        lock = threading.Lock()

        def convert(html, expected):
            try:
                result = ts.turndown(html)
                assert result.strip() == expected
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = []
        inputs = [
            ("<p>Hello</p>", "Hello"),
            ("<em>emphasis</em>", "_emphasis_"),
            ("<strong>bold</strong>", "**bold**"),
            ("<h1>Heading</h1>", "Heading\n======="),
        ]
        for html, expected in inputs:
            for _ in range(2):
                t = threading.Thread(target=convert, args=(html, expected))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        assert not errors, f"Errors occurred: {errors}"
