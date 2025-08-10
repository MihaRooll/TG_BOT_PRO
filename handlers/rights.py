# -*- coding: utf-8 -*-
"""Handlers for granting admin rights."""
from telebot import types
from bot import bot
from services.roles import add_admin, is_main_admin
from utils.tg import safe_delete

RIGHTS_WAIT = set()


@bot.callback_query_handler(func=lambda c: c.data == "rights:init")
def rights_init(c: types.CallbackQuery):
    if not is_main_admin(c.from_user.id):
        bot.answer_callback_query(c.id)
        return
    RIGHTS_WAIT.add(c.message.chat.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Отмена", callback_data="rights:cancel"))
    bot.edit_message_text(
        "Перешлите сообщение пользователя или отправьте его ID для выдачи прав администратора.",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data == "rights:cancel")
def rights_cancel(c: types.CallbackQuery):
    RIGHTS_WAIT.discard(c.message.chat.id)
    bot.edit_message_text("Отменено.", c.message.chat.id, c.message.message_id)


@bot.message_handler(func=lambda m: m.chat.id in RIGHTS_WAIT)
def rights_handle(m: types.Message):
    if not is_main_admin(m.from_user.id):
        return
    uid = None
    if m.forward_from:
        uid = m.forward_from.id
    else:
        try:
            uid = int(m.text.strip())
        except Exception:
            pass
    if not uid:
        bot.reply_to(m, "Не удалось определить ID.")
        return
    add_admin(uid)
    bot.reply_to(m, f"Пользователь {uid} назначен администратором.")
    RIGHTS_WAIT.discard(m.chat.id)
    safe_delete(bot, m.chat.id, m.message_id)
