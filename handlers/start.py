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
        kb.add(types.InlineKeyboardButton("1) Настройки проекта", callback_data="setup:init"))
        if is_main_admin(uid):
            kb.add(types.InlineKeyboardButton("2) Админка", callback_data="rights:init"))
        kb.add(types.InlineKeyboardButton("3) Создание заказа", callback_data="order:start"))
        bot.send_message(message.chat.id, "Выберите команду:", reply_markup=kb)
        return

    if is_employee(uid):
        if not s.get("configured"):
            bot.send_message(message.chat.id, "Бот ещё не настроен. Обратитесь к администратору.")
            return
        kb.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="order:start"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=kb)
        return

    bot.send_message(message.chat.id, "Доступ запрещён. Обратитесь к администратору.")
