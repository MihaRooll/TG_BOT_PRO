# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import get_settings
from services.roles import is_admin, is_main_admin, is_employee


@bot.message_handler(commands=["start", "help", "menu"])
def start_cmd(message: types.Message):
    s = get_settings()
    uid = message.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=1)

    if is_admin(uid):
        if not s.get("configured"):
            kb.add(types.InlineKeyboardButton("🔧 Запустить мастер настройки", callback_data="setup:init"))
            kb.add(types.InlineKeyboardButton("ℹ️ Привязка общего чата", callback_data="setup:bind_hint"))
            msg = "<b>Мастер настройки</b> — нажмите кнопку ниже 👇"
            parse = "HTML"
        else:
            kb.add(types.InlineKeyboardButton("🔧 Настройки", callback_data="setup:init"))
            msg = "Выберите действие:"
            parse = None
        kb.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="order:start"))
        if is_main_admin(uid):
            kb.add(types.InlineKeyboardButton("👥 Раздача прав", callback_data="rights:init"))
        bot.send_message(message.chat.id, msg, reply_markup=kb, parse_mode=parse)
        return

    if is_employee(uid):
        if not s.get("configured"):
            bot.send_message(message.chat.id, "Бот ещё не настроен. Обратитесь к администратору.")
            return
        kb.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="order:start"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=kb)
        return

    bot.send_message(message.chat.id, "Доступ запрещён. Обратитесь к администратору.")
