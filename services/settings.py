# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Tuple
from repositories.files import load_json, save_json

SETTINGS_FILE = "settings.json"
ADMIN_BIND_FILE = "admin_chat.json"

def get_settings() -> Dict[str, Any]:
    data = load_json(SETTINGS_FILE)
    if not data:
        # Базовая заготовка до настройки
        data = {
            "configured": False,
            "text_rules": {
                "allow_latin": True,
                "allow_cyrillic": False,
                "allow_space": True,
                "max_text_len": 12,
                "max_number": 99
            },
            "merch": {},           # {merch_key: {name_ru, colors:{color_key:{name_ru}}, sizes:[...] } }
            "text_colors": {},     # {merch_key:{color_key:[text_color,...]}, "palette":[...]}
            "templates": {},        # {merch_key:{templates:{num:{allowed_colors:[...] }}, collages:[file_id,...]}}
            "color_names": {},
            "layouts": {
                "max_per_order": 3,
                "selected_indicator": "🟩"
            }
        }
    else:
        data.setdefault("color_names", {})
        data.setdefault("layouts", {})
        data["layouts"].setdefault("max_per_order", 3)
        data["layouts"].setdefault("selected_indicator", "🟩")
    return data

def save_settings(data: Dict[str, Any]) -> None:
    save_json(SETTINGS_FILE, data)

def get_admin_bind() -> Tuple[Any, Any]:
    b = load_json(ADMIN_BIND_FILE)
    return (b.get("chat_id"), b.get("thread_id")) if b else (None, None)

def save_admin_bind(chat_id, thread_id=None) -> None:
    save_json(ADMIN_BIND_FILE, {"chat_id": chat_id, "thread_id": thread_id})
