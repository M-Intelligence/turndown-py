"""
turndown-py — HTML to Markdown converter.

Python port of Turndown (https://github.com/mixmark-io/turndown).
"""

try:
    from importlib.metadata import version as _version
except ImportError:
    from importlib_metadata import version as _version  # type: ignore

__version__ = _version("turndown-py")
