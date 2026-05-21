from __future__ import annotations

import html
import json
import os
import re
from typing import Any, Dict, List

import pytest


def _clean_expected(value: str) -> str:
    value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    value = html.unescape(value)
    return value


@pytest.fixture(scope="session")
def test_cases() -> List[Dict[str, Any]]:
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    with open(os.path.join(fixtures_dir, "cases.json")) as f:
        cases = json.load(f)
    for case in cases:
        case["expected"] = _clean_expected(case["expected"])
    return cases
