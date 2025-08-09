# -*- coding: utf-8 -*-
import os, json
from typing import Any, Dict
import config

def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def _path(filename: str) -> str:
    _ensure_dir(config.JSON_DIR)
    if filename.startswith(config.JSON_DIR):
        return filename
    return os.path.join(config.JSON_DIR, filename)

def load_json(filename: str) -> Dict[str, Any]:
    path = _path(filename)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
            return json.loads(text) if text else {}
    except Exception:
        return {}

def save_json(filename: str, data: Dict[str, Any]) -> None:
    path = _path(filename)
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
