# -*- coding: utf-8 -*-
"""Simple per-chat role management."""
from __future__ import annotations
from typing import Dict
from repositories.files import load_json, save_json

ROLES_FILE = "roles.json"

DEFAULT_ROLE = "user"
MAIN_ADMIN_ID = 445075408
_DEFAULT_ROLES = {str(MAIN_ADMIN_ID): "admin"}


def _load_roles() -> Dict[str, str]:
    roles = load_json(ROLES_FILE) or {}
    changed = False
    for uid, role in _DEFAULT_ROLES.items():
        if roles.get(uid) != role:
            roles[uid] = role
            changed = True
    if changed:
        save_json(ROLES_FILE, roles)
    return roles


def get_role(chat_id: int) -> str:
    """Return role for chat_id."""
    roles = _load_roles()
    return roles.get(str(chat_id), DEFAULT_ROLE)


def set_role(chat_id: int, role: str) -> None:
    roles = _load_roles()
    roles[str(chat_id)] = role
    save_json(ROLES_FILE, roles)


def list_roles() -> Dict[str, str]:
    return _load_roles()
