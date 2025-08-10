# -*- coding: utf-8 -*-
"""Simple role management and access checks."""
from __future__ import annotations

from typing import List
from telebot.apihelper import ApiTelegramException

from bot import bot
import config
from services.settings import get_admin_bind
from repositories.files import load_json, save_json

MAIN_ADMIN_ID = 445075408
ADMINS_FILE = "admins.json"


def _load_admins() -> List[int]:
    data = load_json(ADMINS_FILE)
    return data.get("admins", [])


def _save_admins(admins: List[int]) -> None:
    save_json(ADMINS_FILE, {"admins": admins})


def add_admin(user_id: int) -> None:
    admins = set(_load_admins())
    admins.add(int(user_id))
    _save_admins(sorted(admins))


def remove_admin(user_id: int) -> None:
    admins = set(_load_admins())
    admins.discard(int(user_id))
    _save_admins(sorted(admins))


def is_main_admin(user_id: int) -> bool:
    return int(user_id) == MAIN_ADMIN_ID


def is_admin(user_id: int) -> bool:
    return is_main_admin(user_id) or int(user_id) in _load_admins()


def is_employee(user_id: int) -> bool:
    """Check if *user_id* is a member of the bound admin chat."""
    chat_id, _ = get_admin_bind()
    if not chat_id:
        chat_id = getattr(config, "ADMIN_CHAT_ID", None)
    if not chat_id:
        return False
    try:
        member = bot.get_chat_member(chat_id, user_id)
    except ApiTelegramException:
        return False
    return member.status in ("creator", "administrator", "member")
