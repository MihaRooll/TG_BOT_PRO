# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit

def start_for_merch(chat_id: int, mk: str):
    WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})
    WIZ[chat_id]["data"]["_tmpl_current_mk"] = mk
    WIZ[chat_id]["data"]["_num_buf"] = ""
    render_builder(chat_id)

def render_builder(chat_id: int):
    mk = WIZ[chat_id]["data"]["_tmpl_current_mk"]
    d = WIZ[chat_id]["data"]["templates"][mk]["templates"]
    buf = WIZ[chat_id]["data"].get("_num_buf","")
    existing = ", ".join(sorted(d.keys())) or "—"
    kb = types.InlineKeyboardMarkup(row_width=3)
    for row in (("1","2","3"),("4","5","6"),("7","8","9")):
        kb.add(*(types.InlineKeyboardButton(x, callback_data=f"setup:tmpl_num_key:{x}") for x in row))
    kb.add(types.InlineKeyboardButton("⌫", callback_data="setup:tmpl_num_back"), types.InlineKeyboardButton("0", callback_data="setup:tmpl_num_key:0"), types.InlineKeyboardButton("✖", callback_data="setup:tmpl_num_clear"))
    kb.add(types.InlineKeyboardButton("➕ Добавить номер", callback_data="setup:tmpl_num_add"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:tmpl_num_done"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
    edit(chat_id, f"Шаг 3/4. Ввод номеров макетов ({mk}).\\nТекущий: <b>{buf or '—'}</b>\\nСписок: {existing}", kb)
    WIZ[chat_id]["stage"] = "tmpl_numbers_builder"

def keypress(chat_id: int, k: str):
    buf = WIZ[chat_id]["data"].get("_num_buf","")
    if len(buf) < 6:
        buf += k
    WIZ[chat_id]["data"]["_num_buf"] = buf
    render_builder(chat_id)

def backspace(chat_id: int):
    buf = WIZ[chat_id]["data"].get("_num_buf","")
    buf = buf[:-1]
    WIZ[chat_id]["data"]["_num_buf"] = buf
    render_builder(chat_id)

def clearbuf(chat_id: int):
    WIZ[chat_id]["data"]["_num_buf"] = ""
    render_builder(chat_id)

def add_number(chat_id: int):
    mk = WIZ[chat_id]["data"]["_tmpl_current_mk"]
    buf = WIZ[chat_id]["data"].get("_num_buf","").strip()
    if buf:
        WIZ[chat_id]["data"]["templates"][mk]["templates"].setdefault(buf, {"allowed_colors": []})
        WIZ[chat_id]["data"]["_num_buf"] = ""
    render_builder(chat_id)

def done(chat_id: int):
    from .A7_TemplatesColors import render_for_next_template
    render_for_next_template(chat_id)
