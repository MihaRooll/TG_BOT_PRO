# handlers/setup/router.py
# -*- coding: utf-8 -*-
from telebot import types
from bot import bot

# Пример хэндлера мастера настройки
@bot.message_handler(commands=["setup"])
def setup_start(message: types.Message):
    bot.reply_to(message, "Мастер настройки запущен ✅")
