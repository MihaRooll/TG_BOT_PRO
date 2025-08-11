# -*- coding: utf-8 -*-
"""Order utilities: persistent counters and saving."""
from typing import Dict, Any
from repositories.files import load_json, save_json

COUNTER_FILE = "order_counter.json"
ORDERS_FILE = "orders.json"


def get_next_order_number() -> int:
    data = load_json(COUNTER_FILE) or {"last": 0}
    data["last"] = data.get("last", 0) + 1
    save_json(COUNTER_FILE, data)
    return data["last"]


def reset_order_counter() -> None:
    save_json(COUNTER_FILE, {"last": 0})


def save_order(order: Dict[str, Any]) -> None:
    data = load_json(ORDERS_FILE) or []
    data.append(order)
    save_json(ORDERS_FILE, data)


def clear_orders() -> None:
    save_json(ORDERS_FILE, [])
