# turndown-py

A Python port of [Turndown](https://github.com/mixmark-io/turndown) (v7.2.4),
an HTML to Markdown converter originally written in JavaScript by Dom Christie.

## Project Status

**Conversion fidelity:** 203 tests passing — 147 golden test cases ported from upstream (all match JS output), 39 internal/unit tests, 14 API tests.

- ✅ `ruff check` — clean
- ✅ `ruff format` — clean
- ✅ `pytest tests/` — 203/203 passed

🎉 Additional tests in `tests/test_internals.py`:
- **Pickle serialization** — `TurndownService` round-trips through `pickle.dumps`/`loads` (required for Spark UDFs)
- **Thread safety** — 8 concurrent threads converting different HTML inputs produce correct, isolated results
- **Statelessness** — repeated calls with same input yield identical output
- **Reference link isolation** — per-call `references` state prevents cross-call contamination

## Installation

```bash
pip install turndown-py
```

Requires Python 3.7+.

## Development

```bash
# Clone and enter the repo
git clone https://github.com/M-Intelligence/turndown-py
cd turndown-py

# Create virtualenv and install dev dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Package Structure

| Python Module | Ported From | Description |
|---|---|---|
| `html_parser.py` | `html-parser.js` | Pure-Python DOM tree via `html.parser.HTMLParser` with `DomNode` adapter providing JS-like `childNodes`, `textContent`, `outerHTML`, `cloneNode()`, `getAttribute()`, sibling traversal |
| `utilities.py` | `utilities.js` | Block/void element sets, `escapeMarkdown()`, `extend()`, `repeat()`, newline trimming helpers |
| `collapse_whitespace.py` | `collapse-whitespace.js` | DFS whitespace collapse preserving `<pre>` subtrees |
| `node.py` | `node.js` | `annotate_node()` — `isBlock`, `isCode`, `isBlank`, `flankingWhitespace` |
| `rules.py` | `rules.js` | Three-bucket rule system: `forNode()`, `keep()`, `remove()`, `add()` |
| `commonmark_rules.py` | `commonmark-rules.js` | All 15 CommonMark rules — paragraphs, headings, lists, code blocks, links, emphasis, images |
| `root_node.py` | `root-node.js` | Input normalization: parse HTML + collapse whitespace |
| `service.py` | `turndown.js` | `TurndownService` with full public API, pickle support, thread safety |

## Usage

```python
from turndown import TurndownService

ts = TurndownService()
markdown = ts.turndown('<h1>Hello <em>world</em></h1>')
# => 'Hello _world_\n============='
```

## License

GPL-3.0-or-later. The original turndown.js MIT license is retained in `LICENSE_MIT`.
Attribution in `CREDITS`.
