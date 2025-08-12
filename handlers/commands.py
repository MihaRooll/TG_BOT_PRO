# -*- coding: utf-8 -*-
from telebot import types
from bot import bot

@bot.message_handler(commands=["stock"])
def cmd_stock(message: types.Message):
    bot.send_message(message.chat.id, "ℹ️ Быстрая корректировка остатков пока не реализована.")

@bot.message_handler(commands=["promo_test"])
def cmd_promo(message: types.Message):
    bot.send_message(message.chat.id, "ℹ️ Топ пользователей по заказам недоступен.")

@bot.message_handler(commands=["analytics"])
def cmd_analytics(message: types.Message):
    bot.send_message(message.chat.id, "ℹ️ Аналитика ещё не реализована.")

@bot.message_handler(commands=["settings"])
def cmd_settings(message: types.Message):
    bot.send_message(message.chat.id, "🔧 Настройки доступны через главное меню.")

@bot.message_handler(commands=["admin"])
def cmd_admin(message: types.Message):
    bot.send_message(message.chat.id, "Админка в разработке.")
