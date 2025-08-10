# -*- coding: utf-8 -*-
"""Handlers for administering admin rights."""
from telebot import types
from bot import bot
from services.roles import (
    add_admin,
    remove_admin,
    get_admins,
    is_main_admin,
    MAIN_ADMIN_ID,
)
from utils.tg import safe_delete

# chat.id -> mode ("add" or "del") waiting for a forwarded message/ID
RIGHTS_WAIT = {}


@bot.callback_query_handler(func=lambda c: c.data == "rights:init")
def rights_menu(c: types.CallbackQuery):
    if not is_main_admin(c.from_user.id):
        bot.answer_callback_query(c.id)
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("➕ Выдать права", callback_data="rights:add"),
        types.InlineKeyboardButton("➖ Удалить права", callback_data="rights:del"),
        types.InlineKeyboardButton("📋 Список админов", callback_data="rights:list"),
    )
    bot.edit_message_text("Выберите действие:", c.message.chat.id, c.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data in {"rights:add", "rights:del"})
def rights_prompt(c: types.CallbackQuery):
    if not is_main_admin(c.from_user.id):
        bot.answer_callback_query(c.id)
        return
    mode = "add" if c.data.endswith("add") else "del"
    RIGHTS_WAIT[c.message.chat.id] = mode
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Отмена", callback_data="rights:cancel"))
    action = "выдачи" if mode == "add" else "удаления"
    bot.edit_message_text(
        f"Перешлите сообщение пользователя или отправьте его ID для {action} прав администратора.",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data == "rights:list")
def rights_list(c: types.CallbackQuery):
    if not is_main_admin(c.from_user.id):
        bot.answer_callback_query(c.id)
        return
    admins = get_admins()
    text = "Список админов:\n" + "\n".join([str(MAIN_ADMIN_ID)] + [str(a) for a in admins])
    bot.answer_callback_query(c.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "rights:cancel")
def rights_cancel(c: types.CallbackQuery):
    RIGHTS_WAIT.pop(c.message.chat.id, None)
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
    mode = RIGHTS_WAIT.pop(m.chat.id)
    if mode == "add":
        add_admin(uid)
        bot.reply_to(m, f"Пользователь {uid} назначен администратором.")
    else:
        remove_admin(uid)
        bot.reply_to(m, f"Пользователь {uid} удалён из администраторов.")
    safe_delete(bot, m.chat.id, m.message_id)
