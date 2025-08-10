# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import get_settings
from utils.tg import set_chat_commands

@bot.message_handler(commands=["start","help"])
def start_cmd(message: types.Message):
    set_chat_commands(bot, message.chat.id)
    s = get_settings()
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not s.get("configured"):
        kb.add(types.InlineKeyboardButton("🔧 Запустить мастер настройки", callback_data="setup:init"))
        kb.add(types.InlineKeyboardButton("ℹ️ Привязка общего чата", callback_data="setup:bind_hint"))
        bot.send_message(message.chat.id, "<b>Мастер настройки</b> — нажмите кнопку ниже 👇", reply_markup=kb, parse_mode="HTML")
    else:
        kb.add(types.InlineKeyboardButton("🔧 Настройки", callback_data="setup:init"))
        bot.send_message(message.chat.id, "Бот настроен. Выберите действие:", reply_markup=kb)
