# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import save_admin_bind
from utils.tg import set_chat_commands

@bot.message_handler(commands=["bind_here"])
def bind_here_cmd(message: types.Message):
    thread_id = getattr(message, "message_thread_id", None)
    save_admin_bind(message.chat.id, thread_id)
    set_chat_commands(bot, message.chat.id)
    bot.reply_to(message, "✅ Чат привязан.")
