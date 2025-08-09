# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import get_settings

@bot.message_handler(commands=["start","help"])
def start_cmd(message: types.Message):
    s = get_settings()
    kb = types.InlineKeyboardMarkup()
    if not s.get("configured"):
        kb.add(types.InlineKeyboardButton("🔧 Запустить мастер настройки", callback_data="setup:init"))
        kb.add(types.InlineKeyboardButton("ℹ️ Привязка общего чата", callback_data="setup:bind_hint"))
        bot.send_message(message.chat.id, "Подготовка…", reply_markup=kb, parse_mode="HTML")
        return
    else:
        kb.add(types.InlineKeyboardButton("🛍 Оформить заказ", callback_data="order:start"))
        kb.add(types.InlineKeyboardButton("🔧 Настройки", callback_data="setup:init"))
        bot.send_message(message.chat.id, "Готов к работе.", reply_markup=kb)
