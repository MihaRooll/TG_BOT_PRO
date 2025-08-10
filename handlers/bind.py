# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import save_admin_bind
from services.roles import is_main_admin

@bot.message_handler(commands=["bind_here"])
def bind_here_cmd(message: types.Message):
    if not is_main_admin(message.from_user.id):
        return
    thread_id = getattr(message, "message_thread_id", None)
    save_admin_bind(message.chat.id, thread_id)
    bot.reply_to(message, "✅ Чат привязан.")
