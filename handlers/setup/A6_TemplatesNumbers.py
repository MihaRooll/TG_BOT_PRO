# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit


def start_for_merch(chat_id: int, mk: str):
    data = WIZ[chat_id]["data"].setdefault("templates", {})
    data.setdefault(mk, {"templates": {}, "collages": []})
    WIZ[chat_id]["data"]["_tmpl_current_mk"] = mk
    render_prompt(chat_id)


def render_prompt(chat_id: int):
    mk = WIZ[chat_id]["data"]["_tmpl_current_mk"]
    d = WIZ[chat_id]["data"]["templates"][mk]["templates"]
    existing = ", ".join(sorted(d.keys())) or "—"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:tmpl_num_done"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
    edit(chat_id,
         f"Шаг 3/4. Введите номера макетов ({mk}) через запятую.\nСписок: {existing}",
         kb)
    WIZ[chat_id]["stage"] = "tmpl_nums_enter"


def handle_input(chat_id: int, text: str):
    import re
    mk = WIZ[chat_id]["data"]["_tmpl_current_mk"]
    d = WIZ[chat_id]["data"]["templates"][mk]["templates"]
    parts = [p.strip() for p in text.replace("\n", ",").split(",")]
    for p in parts:
        if not p:
            continue
        token = p.upper()
        if len(token) <= 6 and re.fullmatch(r"[0-9A-ZА-Я]+", token):
            d.setdefault(token, {"allowed_colors": []})
    render_prompt(chat_id)


def done(chat_id: int):
    from .A7_TemplatesColors import render_for_next_template
    render_for_next_template(chat_id)
