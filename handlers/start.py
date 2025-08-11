# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import get_settings
from utils.tg import set_chat_commands

@bot.message_handler(commands=["start"])
def start_cmd(message: types.Message):
    chat_id = message.chat.id
    set_chat_commands(bot, chat_id)
    s = get_settings()
    from services.roles import get_role

    if not s.get("configured"):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🔧 Запустить мастер настройки", callback_data="setup:init"))
        kb.add(types.InlineKeyboardButton("ℹ️ Привязка общего чата", callback_data="setup:bind_hint"))
        bot.send_message(chat_id, "<b>Мастер настройки</b> — нажмите кнопку ниже 👇", reply_markup=kb, parse_mode="HTML")
        return

    role = get_role(chat_id)
    if role == "user":
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    if role in ("promo", "coord", "admin"):
        kb.add(types.InlineKeyboardButton("🛒 Оформить заказ", callback_data="order:start"))
    if role in ("coord", "admin"):
        kb.add(types.InlineKeyboardButton("🔧 Настройки", callback_data="setup:init"))
    if role == "admin":
        kb.add(types.InlineKeyboardButton("⚙️ Админка", callback_data="admin:home"))

    bot.send_message(chat_id, "Выберите действие:", reply_markup=kb)
