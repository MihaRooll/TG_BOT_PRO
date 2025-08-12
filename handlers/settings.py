# -*- coding: utf-8 -*-
from telebot import types
from bot import bot

from handlers.setup.A0_Overview import render_home
from handlers.setup.core import ensure

try:
    from handlers.order_flow import ORD
except Exception:
    ORD = {}


def _open_settings(chat_id: int, mid: int):
    ORD.pop(chat_id, None)
    ensure(chat_id, mid)
    render_home(chat_id)


@bot.message_handler(func=lambda m: (m.text or "").strip().lower() == "настройки")
def settings_msg(m: types.Message):
    _open_settings(m.chat.id, m.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_open")
def settings_cb(c: types.CallbackQuery):
    bot.answer_callback_query(c.id)
    _open_settings(c.message.chat.id, c.message.message_id)
