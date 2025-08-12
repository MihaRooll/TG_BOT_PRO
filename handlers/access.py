# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import (
    get_admins,
    get_coordinators,
    is_admin,
    get_admin_bind,
)


def _is_general_member(user_id: int) -> bool:
    chat_id, _ = get_admin_bind()
    if not chat_id:
        return False
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator", "member")
    except Exception:
        return False


def is_allowed(user_id: int) -> bool:
    if not get_admins():
        # until an admin is added, allow everyone
        return True
    if is_admin(user_id):
        return True
    if user_id in get_coordinators():
        return True
    if _is_general_member(user_id):
        return True
    return False


@bot.message_handler(func=lambda m: not is_allowed(m.from_user.id))
def block_users(m: types.Message):
    bot.reply_to(m, "⛔️ Доступ запрещён")


@bot.callback_query_handler(func=lambda c: not is_allowed(c.from_user.id))
def block_callbacks(c: types.CallbackQuery):
    bot.answer_callback_query(c.id, "Доступ запрещён", show_alert=True)

