# -*- coding: utf-8 -*-
"""Access control and membership tracking."""

from telebot import types
from bot import bot
from services.settings import (
    get_admins,
    get_coordinators,
    is_admin,
    get_admin_bind,
    get_promoters,
    add_promoter,
    del_promoter,
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
    if user_id in get_promoters():
        return True
    if _is_general_member(user_id):
        add_promoter(user_id)
        return True
    return False


@bot.message_handler(func=lambda m: not is_allowed(m.from_user.id))
def block_users(m: types.Message):
    bot.reply_to(m, "⛔️ Доступ запрещён")


@bot.callback_query_handler(func=lambda c: not is_allowed(c.from_user.id))
def block_callbacks(c: types.CallbackQuery):
    bot.answer_callback_query(c.id, "Доступ запрещён", show_alert=True)


@bot.chat_member_handler()
def track_members(update: types.ChatMemberUpdated):
    chat_id, _ = get_admin_bind()
    if not chat_id or update.chat.id != chat_id:
        return
    user_id = update.new_chat_member.user.id
    status = update.new_chat_member.status
    if status in ("member", "administrator", "creator"):
        add_promoter(user_id)
    elif status in ("left", "kicked"):
        del_promoter(user_id)

