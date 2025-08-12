# -*- coding: utf-8 -*-
"""Helpers for issuing sequential order numbers."""
from typing import Dict
from repositories.files import load_json, save_json

_SEQ_FILE = "order_seq.json"


def next_order_no() -> int:
    data: Dict[str, int] = load_json(_SEQ_FILE) or {"next": 1}
    n = data.get("next", 1)
    data["next"] = n + 1
    save_json(_SEQ_FILE, data)
    return n
