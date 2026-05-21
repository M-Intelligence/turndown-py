from __future__ import annotations

try:
    from importlib.metadata import version as _version
except ImportError:
    from importlib_metadata import version as _version  # type: ignore

from .html_parser import DomNode
from .rules import Rule
from .service import TurndownService

__all__ = ["TurndownService", "Rule", "DomNode"]

__version__ = _version("turndown-py")
