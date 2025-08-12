# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Tuple
from repositories.files import load_json, save_json

SETTINGS_FILE = "settings.json"
ADMIN_BIND_FILE = "admin_chat.json"

SUPERADMINS = [445075408]
PROMO_GROUP_ID = None
PROMO_MEMBERS: set[int] = set()


def get_settings() -> Dict[str, Any]:
    data = load_json(SETTINGS_FILE)
    if not data:
        data = {
            "configured": False,
            "text_rules": {
                "allow_latin": True,
                "allow_cyrillic": False,
                "allow_space": True,
                "max_text_len": 12,
                "max_number": 99,
            },
            "merch": {},
            "text_colors": {},
            "templates": {},
            "color_names": {},
            "layouts": {
                "max_per_order": 3,
                "selected_indicator": "🟩",
            },
            "admins": [],
            "coordinators": [],
        }
    else:
        data.setdefault("color_names", {})
        data.setdefault("layouts", {})
        data.setdefault("admins", [])
        data.setdefault("coordinators", [])
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


def get_admins() -> List[int]:
    return get_settings().get("admins", [])


def get_coordinators() -> List[int]:
    return get_settings().get("coordinators", [])


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


def is_superadmin(user_id: int) -> bool:
    return user_id in SUPERADMINS


def is_admin(user_id: int) -> bool:
    return user_id in SUPERADMINS or user_id in get_admins()


def is_coordinator(user_id: int) -> bool:
    return user_id in get_coordinators()


def refresh_promo_members(bot) -> None:
    global PROMO_MEMBERS
    if PROMO_GROUP_ID is None:
        PROMO_MEMBERS = set()
        return
    try:
        members = bot.get_chat_administrators(PROMO_GROUP_ID)
        PROMO_MEMBERS = {m.user.id for m in members}
    except Exception:
        PROMO_MEMBERS = set()


def is_promo(user_id: int) -> bool:
    return user_id in PROMO_MEMBERS


def is_authorized(user_id: int) -> bool:
    return (
        is_superadmin(user_id)
        or user_id in get_admins()
        or is_coordinator(user_id)
        or is_promo(user_id)
    )


def delete_layout(layout_id: str) -> bool:
    data = get_settings()
    found = False
    for meta in data.get("templates", {}).values():
        tpls = meta.get("templates", {})
        if layout_id in tpls:
            del tpls[layout_id]
            found = True
    if found:
        save_settings(data)
    return found
