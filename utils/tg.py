# -*- coding: utf-8 -*-
from telebot import TeleBot, types

def safe_delete(bot: TeleBot, chat_id: int, message_id: int | None) -> None:
    if not message_id:
        return
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def safe_edit_message(bot: TeleBot, chat_id: int, message_id: int, text: str,
                      markup: types.InlineKeyboardMarkup | None = None) -> None:
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        pass
