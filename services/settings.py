# -*- coding: utf-8 -*-
"""Helpers for storing configuration and determining user roles.

The bot keeps a small JSON settings file for persistent configuration such as
administrators, coordinators and the ID of a group whose members receive the
``PROMO`` role.  A single immutable super administrator is hard coded and
cannot be removed.  The module exposes helper functions to check a user's
roles and whether they are allowed to interact with the bot.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Set
import logging

from repositories.files import load_json, save_json
from bot import bot


log = logging.getLogger(__name__)

SETTINGS_FILE = "settings.json"
ADMIN_BIND_FILE = "admin_chat.json"

# Hard coded superadmins.  Stored as a ``set`` for fast membership checks and
# to make it obvious that callers must not mutate it.
SUPERADMINS: Set[int] = {445075408}

# Cached members of the promo group chat.  Populated on first use or via the
# ``refresh_promo_cache`` function which is exposed to a management command.
_PROMO_CACHE: Set[int] = set()


def get_settings() -> Dict[str, Any]:
    """Return settings dictionary creating defaults on first use."""

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
            "merch": {},  # {merch_key:{name_ru, colors:{color_key:{name_ru}}, sizes:[...]}}
            "text_colors": {},  # {merch_key:{color_key:[text_color,...]}, "palette":[...]}
            "templates": {},  # {merch_key:{templates:{num:{allowed_colors:[...] }}, collages:[file_id,...]}}
            "color_names": {},
            "layouts": {
                "max_per_order": 3,
                "selected_indicator": "🟩",
            },
            # Persistent role lists / config
            "admins": [],
            "coordinators": [],
            "group_chat_id": None,
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


# ---------------------------------------------------------------------------
# Role management helpers

def get_admins() -> List[int]:
    """Return a copy of administrators list."""

    return list(get_settings().get("admins", []))


def add_admin(user_id: int) -> None:
    data = get_settings()
    admins = data.setdefault("admins", [])
    if user_id not in admins and user_id not in SUPERADMINS:
        admins.append(user_id)
        save_settings(data)


def del_admin(user_id: int) -> None:
    data = get_settings()
    admins = data.setdefault("admins", [])
    if user_id in admins:
        admins.remove(user_id)
        save_settings(data)


def get_coordinators() -> List[int]:
    """Return a copy of coordinators list."""

    return list(get_settings().get("coordinators", []))


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


def get_group_chat_id() -> int | None:
    return get_settings().get("group_chat_id")


def set_group_chat_id(chat_id: int | None) -> None:
    data = get_settings()
    data["group_chat_id"] = chat_id
    save_settings(data)


def is_superadmin(user_id: int) -> bool:
    return user_id in SUPERADMINS


def is_admin(user_id: int) -> bool:
    return user_id in SUPERADMINS or user_id in get_admins()


def is_coordinator(user_id: int) -> bool:
    return user_id in get_coordinators()


def _refresh_promo_cache() -> None:
    """Populate promo cache from the configured group chat.

    The Telegram Bot API does not expose a direct method for fetching all
    members of a chat.  As a best effort we fetch the list of administrators
    which at least keeps the cache non-empty for testing purposes.  Any
    network errors are logged and ignored.
    """

    global _PROMO_CACHE
    _PROMO_CACHE = set()
    chat_id = get_group_chat_id()
    if not chat_id:
        return
    try:  # pragma: no cover - relies on network
        admins = bot.get_chat_administrators(chat_id)
        _PROMO_CACHE.update(a.user.id for a in admins)
    except Exception as e:  # pragma: no cover - network errors
        log.warning("Failed to refresh promo cache: %s", e)


def refresh_promo_cache() -> None:
    _refresh_promo_cache()


def promo_members() -> Set[int]:
    if not _PROMO_CACHE:
        _refresh_promo_cache()
    return set(_PROMO_CACHE)


def is_promo(user_id: int) -> bool:
    return user_id in promo_members()


def user_roles(user_id: int) -> List[str]:
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


def has_access(user_id: int) -> bool:
    return bool(user_roles(user_id))


def log_rejected(user_id: int, command: str, reason: str) -> None:
    roles = user_roles(user_id)
    log.info(
        "Rejected command",
        extra={
            "user_id": user_id,
            "roles": roles,
            "command": command,
            "reason": reason,
        },
    )

