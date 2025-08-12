# -*- coding: utf-8 -*-
import logging
from telebot import types
from bot import bot
from services.settings import is_authorized, get_roles, log_rejected

log = logging.getLogger("access")

@bot.message_handler(func=lambda m: not is_authorized(m.from_user.id), content_types=['text','photo','audio','document','sticker','video','voice','location','contact'])
def gate_message(message: types.Message):
    cmd = message.text or ''
    log_rejected(message.from_user.id, cmd, 'not_allowed')
    # Ничего не отвечаем — сообщение игнорируется
    return
