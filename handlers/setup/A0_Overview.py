# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit, home_text

def render_home(chat_id: int):
    d = WIZ[chat_id].setdefault("data", {})
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("1) Мерч", callback_data="setup:merch"),
        types.InlineKeyboardButton("2) Буквы", callback_data="setup:letters"),
    )
    kb.add(
        types.InlineKeyboardButton("3) Цифры", callback_data="setup:numbers"),
        types.InlineKeyboardButton("2.1) Соответствия", callback_data="setup:map_text_colors")
    )
    kb.add(
        types.InlineKeyboardButton("4) Макеты", callback_data="setup:tmpls"),
        types.InlineKeyboardButton("5) Остатки", callback_data="setup:inv")
    )
    if d.get("_inv_merch"):
        kb.add(types.InlineKeyboardButton("Завершить настройку ☑", callback_data="setup:finish"))
    edit(chat_id, home_text(d), kb)
    WIZ[chat_id]["stage"] = "home"
