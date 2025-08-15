# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Tuple
from repositories.files import load_json, save_json

SETTINGS_FILE = "settings.json"
ADMIN_BIND_FILE = "admin_chat.json"

SUPERADMINS: List[int] = []

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
            },
            "admins": [],
            "coordinators": [],
            "promoters": []
        }
    else:
        data.setdefault("color_names", {})
        data.setdefault("layouts", {})
        data.setdefault("admins", [])
        data.setdefault("coordinators", [])
        data.setdefault("promoters", [])
        data["layouts"].setdefault("max_per_order", 3)
        data["layouts"].setdefault("selected_indicator", "🟩")
    return data

def save_settings(data: Dict[str, Any]) -> None:
    save_json(SETTINGS_FILE, data)

def get_admin_bind() -> Tuple[Any, Any]:
    """Return the bound admin chat or a fallback from config.

    The bot previously required an explicit ``/bind_here`` before it could
    recognise members of the main chat.  Until the binding file is created the
    function returned ``(None, None)`` which caused ``is_allowed`` to deny
    access even for existing chat participants.  We now fall back to the
    ``ADMIN_CHAT_ID`` from ``config`` so a fresh deployment still respects the
    preconfigured general chat.
    """

    b = load_json(ADMIN_BIND_FILE)
    if b and b.get("chat_id"):
        return b.get("chat_id"), b.get("thread_id")

    import config

    return getattr(config, "ADMIN_CHAT_ID", None), None

def save_admin_bind(chat_id, thread_id=None) -> None:
    save_json(ADMIN_BIND_FILE, {"chat_id": chat_id, "thread_id": thread_id})


def get_admins() -> List[int]:
    return get_settings().get("admins", [])


def add_admin(user_id: int) -> None:
    data = get_settings()
    admins = data.setdefault("admins", [])
    if user_id not in admins:
        admins.append(user_id)
        save_settings(data)


def del_admin(user_id: int) -> None:
    data = get_settings()
    admins = data.setdefault("admins", [])
    if user_id in admins:
        admins.remove(user_id)
        save_settings(data)


def is_superadmin(user_id: int) -> bool:
    return user_id in SUPERADMINS


def is_admin(user_id: int) -> bool:
    return user_id in SUPERADMINS or user_id in get_admins()


def get_coordinators() -> List[int]:
    return get_settings().get("coordinators", [])


def add_coordinator(user_id: int) -> None:
    data = get_settings()
    coords = data.setdefault("coordinators", [])
    if user_id not in coords:
        coords.append(user_id)
        save_settings(data)


def del_coordinator(user_id: int) -> None:
    data = get_settings()
    coords = data.setdefault("coordinators", [])
    if user_id in coords:
        coords.remove(user_id)
        save_settings(data)


def get_promoters() -> List[int]:
    return get_settings().get("promoters", [])


def add_promoter(user_id: int) -> None:
    data = get_settings()
    promos = data.setdefault("promoters", [])
    if user_id not in promos:
        promos.append(user_id)
        save_settings(data)


def del_promoter(user_id: int) -> None:
    data = get_settings()
    promos = data.setdefault("promoters", [])
    if user_id in promos:
        promos.remove(user_id)
        save_settings(data)
