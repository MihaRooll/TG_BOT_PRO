# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Tuple, Set
import logging
from repositories.files import load_json, save_json

SETTINGS_FILE = "settings.json"
ADMIN_BIND_FILE = "admin_chat.json"

# Нельзя удалить или изменить этого супер-админа
SUPERADMINS: Set[int] = {445075408}

# Кэш участников промо-группы (пополняется при запуске и через /promo_refresh)
PROMO_CACHE: Set[int] = set()
log = logging.getLogger("access")

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
            "group_chat_id": None
        }
    else:
        data.setdefault("color_names", {})
        data.setdefault("layouts", {})
        data.setdefault("admins", [])
        data.setdefault("coordinators", [])
        data.setdefault("group_chat_id", None)
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


def is_coordinator(user_id: int) -> bool:
    return user_id in get_coordinators()


def get_group_chat_id() -> int | None:
    return get_settings().get("group_chat_id")


def set_group_chat_id(chat_id: int) -> None:
    data = get_settings()
    data["group_chat_id"] = chat_id
    save_settings(data)


def refresh_promo_cache(bot=None) -> None:
    """Rescan group chat members and refresh PROMO cache."""
    global PROMO_CACHE
    PROMO_CACHE = set()
    gid = get_group_chat_id()
    if not bot or not gid:
        return
    try:
        members = bot.get_chat_administrators(gid)
        PROMO_CACHE.update(m.user.id for m in members)
    except Exception as e:
        log.warning("promo_refresh failed: %s", e)


def is_promo(user_id: int) -> bool:
    return user_id in PROMO_CACHE


def get_roles(user_id: int) -> List[str]:
    roles: List[str] = []
    if is_superadmin(user_id):
        roles.append("SUPERADMIN")
    if user_id in get_admins():
        roles.append("ADMIN")
    if is_coordinator(user_id):
        roles.append("COORDINATOR")
    if is_promo(user_id):
        roles.append("PROMO")
    return roles


def is_authorized(user_id: int) -> bool:
    return bool(get_roles(user_id))


def log_rejected(user_id: int, command: str, reason: str) -> None:
    roles = get_roles(user_id)
    log.info("rejected command: %s", {"user_id": user_id, "roles": roles, "command": command, "reason": reason})
