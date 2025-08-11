# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit, home_text

from services.settings import get_settings
from services.inventory import (
    get_merch_inv, get_letters_inv, get_numbers_inv, get_templates_inv,
)

def render_home(chat_id: int):
    d = WIZ[chat_id].setdefault("data", {})
    if not d:
        s = get_settings()
        d.update({
            "merch": s.get("merch", {}),
            "features": s.get("features", {"letters": True, "numbers": True}),
            "text_rules": s.get("text_rules", {
                "allow_latin": True,
                "allow_cyrillic": False,
                "allow_space": True,
                "max_text_len": 12,
                "max_number": 99,
            }),
            "text_palette": s.get("text_palette", ["white", "black"]),
            "text_colors": s.get("text_colors", {}),
            "templates": s.get("templates", {}),
            "_inv_merch": get_merch_inv(),
            "_inv_letters": get_letters_inv(),
            "_inv_numbers": get_numbers_inv(),
            "_inv_tmpls": get_templates_inv(),
        })
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("1) Мерч", callback_data="setup:merch"),
           types.InlineKeyboardButton("2) Буквы", callback_data="setup:letters"))
    kb.add(types.InlineKeyboardButton("2.1) Соответствия", callback_data="setup:map_text_colors"),
           types.InlineKeyboardButton("3) Макеты", callback_data="setup:tmpls"))
    kb.add(types.InlineKeyboardButton("4) Остатки", callback_data="setup:inv"),
           types.InlineKeyboardButton("Готово ✅", callback_data="setup:finish"))
    edit(chat_id, home_text(d), kb)
    WIZ[chat_id]["stage"] = "home"
