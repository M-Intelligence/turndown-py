from __future__ import annotations

import pytest

from turndown import TurndownService


def normalize(s: str) -> str:
    """Normalize whitespace in expected/actual output for comparison."""
    return s.strip()


@pytest.mark.parametrize(
    "case_name",
    [
        pytest.param("p"),
        pytest.param("multiple ps"),
        pytest.param("em"),
        pytest.param("i"),
        pytest.param("strong"),
        pytest.param("b"),
        pytest.param("code"),
        pytest.param("code containing a backtick"),
        pytest.param("code containing three or more backticks"),
        pytest.param("code containing one or more backticks"),
        pytest.param("code starting with a backtick"),
        pytest.param("code containing markdown syntax"),
        pytest.param("code containing markdown syntax in a span"),
        pytest.param("h1"),
        pytest.param("escape = when used as heading"),
        pytest.param("not escaping = outside of a heading"),
        pytest.param("h1 as atx"),
        pytest.param("h2"),
        pytest.param("h2 as atx"),
        pytest.param("h3"),
        pytest.param("heading with child"),
        pytest.param("invalid heading"),
        pytest.param("hr"),
        pytest.param("hr with closing tag"),
        pytest.param("hr with option"),
        pytest.param("br"),
        pytest.param("br with visible line-ending"),
        pytest.param("img with no alt"),
        pytest.param("img with relative src"),
        pytest.param("img with alt"),
        pytest.param("img with escaped content in alt"),
        pytest.param("img with no src"),
        pytest.param("img with parenthesis in src"),
        pytest.param("img with a new line in alt"),
        pytest.param("img with more than one new line in alt"),
        pytest.param("img with new lines in title"),
        pytest.param("img with quotes in title"),
        pytest.param("img with space in URL"),
        pytest.param("a"),
        pytest.param("a with space in URL"),
        pytest.param("a with title"),
        pytest.param("a with multiline title"),
        pytest.param("a with quotes in title"),
        pytest.param("a with parenthesis in query"),
        pytest.param("a without a src"),
        pytest.param("a with a child"),
        pytest.param("a with a brackets in text"),
        pytest.param("a reference"),
        pytest.param("a reference with space in URL"),
        pytest.param("a reference with collapsed style"),
        pytest.param("a reference with shortcut style"),
        pytest.param("a reference with title"),
        pytest.param("pre/code block"),
        pytest.param("multiple pre/code blocks"),
        pytest.param("pre/code block with multiple new lines"),
        pytest.param("fenced pre/code block"),
        pytest.param("pre/code block fenced with ~"),
        pytest.param("escaping ~~~"),
        pytest.param("not escaping ~~~"),
        pytest.param("fenced pre/code block with language"),
        pytest.param("empty pre does not throw error"),
        pytest.param("ol"),
        pytest.param("ol with start"),
        pytest.param("ol with content"),
        pytest.param("list spacing"),
        pytest.param("ul"),
        pytest.param("ul with custom bullet"),
        pytest.param("ul with paragraph"),
        pytest.param("ol with paragraphs"),
        pytest.param("nested uls"),
        pytest.param("nested ols and uls"),
        pytest.param("ul with blockquote"),
        pytest.param("blockquote"),
        pytest.param("nested blockquotes"),
        pytest.param("html in blockquote"),
        pytest.param("multiple divs"),
        pytest.param("comment"),
        pytest.param("pre/code with comment"),
        pytest.param("leading whitespace in heading"),
        pytest.param("trailing whitespace in li"),
        pytest.param("multilined and bizarre formatting"),
        pytest.param("whitespace between inline elements"),
        pytest.param("whitespace in inline elements"),
        pytest.param("whitespace in nested inline elements"),
        pytest.param("blank inline elements"),
        pytest.param("blank block elements"),
        pytest.param("blank inline element with br"),
        pytest.param("whitespace between blocks"),
        pytest.param("escaping backslashes"),
        pytest.param("escaping headings with #"),
        pytest.param("not escaping # outside of a heading"),
        pytest.param("escaping em markdown with *"),
        pytest.param("escaping em markdown with _"),
        pytest.param("not escaping within code"),
        pytest.param("escaping strong markdown with *"),
        pytest.param("escaping strong markdown with _"),
        pytest.param("escaping hr markdown with *"),
        pytest.param("escaping hr markdown with -"),
        pytest.param("escaping hr markdown with _"),
        pytest.param("escaping hr markdown without spaces"),
        pytest.param("escaping hr markdown with more than 3 characters"),
        pytest.param("escaping ol markdown"),
        pytest.param("not escaping . outside of an ol"),
        pytest.param("escaping ul markdown *"),
        pytest.param("escaping ul markdown -"),
        pytest.param("escaping ul markdown +"),
        pytest.param("not escaping - outside of a ul"),
        pytest.param("not escaping + outside of a ul"),
        pytest.param("escaping *"),
        pytest.param("escaping ** inside strong tags"),
        pytest.param("escaping _ inside em tags"),
        pytest.param("escaping > as blockquote"),
        pytest.param("escaping > as blockquote without space"),
        pytest.param("not escaping > outside of a blockquote"),
        pytest.param("escaping code"),
        pytest.param("escaping []"),
        pytest.param("escaping ["),
        pytest.param("escaping * performance"),
        pytest.param("escaping multiple asterisks"),
        pytest.param("escaping delimiters around short words and numbers"),
        pytest.param("non-markdown block elements"),
        pytest.param("non-markdown inline elements"),
        pytest.param("blank inline elements"),
        pytest.param("elements with a single void element"),
        pytest.param("elements with a nested void element"),
        pytest.param("text separated by a space in an element"),
        pytest.param("text separated by a non-breaking space in an element"),
        pytest.param("triple tildes inside code"),
        pytest.param("triple ticks inside code"),
        pytest.param("four ticks inside code"),
        pytest.param("empty line in start/end of code block"),
        pytest.param("text separated by ASCII and nonASCII space in an element"),
        pytest.param("list-like text with non-breaking spaces"),
        pytest.param("element with trailing nonASCII WS followed by nonWS"),
        pytest.param("element with trailing nonASCII WS followed by nonASCII WS"),
        pytest.param("element with trailing ASCII WS followed by nonASCII WS"),
        pytest.param("element with trailing nonASCII WS followed by ASCII WS"),
        pytest.param("nonWS followed by element with leading nonASCII WS"),
        pytest.param("nonASCII WS followed by element with leading nonASCII WS"),
        pytest.param("nonASCII WS followed by element with leading ASCII WS"),
        pytest.param("ASCII WS followed by element with leading nonASCII WS"),
        pytest.param("preformatted code with leading whitespace"),
        pytest.param("preformatted code with trailing whitespace"),
        pytest.param("preformatted code tightly surrounded"),
        pytest.param("preformatted code loosely surrounded"),
        pytest.param("preformatted code with newlines"),
    ],
)
def test_golden(test_cases, case_name):
    case = next(c for c in test_cases if c["name"] == case_name)
    options = case.get("options", {}) or {}
    ts = TurndownService(options)
    actual = ts.turndown(case["input"])
    assert normalize(actual) == normalize(case["expected"]), (
        f"Case '{case_name}' failed.\nExpected: {case['expected']!r}\nGot:      {actual!r}"
    )


# ---- API tests ----


def test_plugin_use():
    ts = TurndownService()
    calls = []

    def plugin(service):
        calls.append(service)

    result = ts.use(plugin)
    assert result is ts
    assert calls == [ts]


def test_plugin_array():
    ts = TurndownService()
    calls = []

    def p1(s):
        calls.append("p1")

    def p2(s):
        calls.append("p2")

    result = ts.use([p1, p2])
    assert result is ts
    assert calls == ["p1", "p2"]


def test_plugin_invalid():
    ts = TurndownService()
    with pytest.raises(TypeError):
        ts.use("not a function")


def test_add_rule_chaining():
    ts = TurndownService()
    rule = {
        "filter": ["del", "s", "strike"],
        "replacement": lambda content, node, options: "~~" + content + "~~",
    }
    result = ts.add_rule("strikethrough", rule)
    assert result is ts


def test_add_rule_works():
    ts = TurndownService()
    rule = {
        "filter": ["del", "s", "strike"],
        "replacement": lambda content, node, options: "~~" + content + "~~",
    }
    ts.add_rule("strikethrough", rule)
    assert ts.turndown("<del>hello</del>").strip() == "~~hello~~"


def test_keep_returns_instance():
    ts = TurndownService()
    result = ts.keep(["del", "ins"])
    assert result is ts


def test_keep_elements():
    ts = TurndownService()
    result = ts.turndown("<p>Hello <del>world</del><ins>World</ins></p>")
    assert result.strip() == "Hello worldWorld"

    ts.keep(["del", "ins"])
    result = ts.turndown("<p>Hello <del>world</del><ins>World</ins></p>")
    assert "Hello <del>world</del><ins>World</ins>" in result


def test_keep_overridden_by_standard_rules():
    ts = TurndownService()
    ts.keep("p")
    assert ts.turndown("<p>Hello world</p>").strip() == "Hello world"


def test_keep_blank_with_significant_elements():
    ts = TurndownService()
    ts.keep("figure")
    result = ts.turndown('<figure><iframe src="http://example.com"></iframe></figure>')
    assert '<iframe src="http://example.com"></iframe>' in result


def test_custom_keep_replacement():
    ts = TurndownService(
        {"keepReplacement": lambda content, node, options=None: "\n\n" + node.outerHTML + "\n\n"}
    )
    ts.keep(["del", "ins"])
    result = ts.turndown("<p>Hello <del>world</del><ins>World</ins></p>")
    assert result == "Hello \n\n<del>world</del>\n\n<ins>World</ins>"


def test_remove_returns_instance():
    ts = TurndownService()
    result = ts.remove(["del", "ins"])
    assert result is ts


def test_remove_elements():
    ts = TurndownService()
    assert ts.turndown("<del>Please redact me</del>").strip() == "Please redact me"
    ts.remove("del")
    assert ts.turndown("<del>Please redact me</del>").strip() == ""


def test_remove_overridden_by_rules():
    ts = TurndownService()
    ts.remove("p")
    assert ts.turndown("<p>Hello world</p>").strip() == "Hello world"


def test_remove_overridden_by_keep():
    ts = TurndownService()
    ts.keep(["del", "ins"])
    ts.remove(["del", "ins"])
    result = ts.turndown("<p>Hello <del>world</del><ins>World</ins></p>")
    assert "Hello <del>world</del><ins>World</ins>" in result


def test_null_input():
    ts = TurndownService()
    with pytest.raises(TypeError):
        ts.turndown(None)


def test_empty_string():
    ts = TurndownService()
    assert ts.turndown("") == ""


def test_escape_method():
    ts = TurndownService()
    assert ts.escape("*hello*") == "\\*hello\\*"
    assert ts.escape("_hello_") == "\\_hello\\_"


def test_blank_inline_elements():
    ts = TurndownService()
    result = ts.turndown("Hello <em></em>world")
    assert normalize(result) == "Hello world"
