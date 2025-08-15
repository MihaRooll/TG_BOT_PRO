# -*- coding: utf-8 -*-
"""Helpers for issuing order numbers and tracking user activity."""

from typing import Dict

from repositories.files import load_json, save_json

_SEQ_FILE = "order_seq.json"
_USER_ORDERS_FILE = "user_orders.json"


def next_order_no() -> int:
    """Return the next sequential order number."""
    data: Dict[str, int] = load_json(_SEQ_FILE) or {"next": 1}
    n = data.get("next", 1)
    data["next"] = n + 1
    save_json(_SEQ_FILE, data)
    return n


def inc_user_orders(user_id: int) -> int:
    """Increment and return the number of orders placed by *user_id*."""
    data: Dict[str, int] = load_json(_USER_ORDERS_FILE) or {}
    key = str(user_id)
    data[key] = data.get(key, 0) + 1
    save_json(_USER_ORDERS_FILE, data)
    return data[key]


def get_user_orders(user_id: int) -> int:
    """Return total orders for *user_id*."""
    data: Dict[str, int] = load_json(_USER_ORDERS_FILE) or {}
    return data.get(str(user_id), 0)


def get_all_user_orders() -> Dict[int, int]:
    """Return mapping of user_id -> order_count."""
    data: Dict[str, int] = load_json(_USER_ORDERS_FILE) or {}
    return {int(uid): count for uid, count in data.items()}
