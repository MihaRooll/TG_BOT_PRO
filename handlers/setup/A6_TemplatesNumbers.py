# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit


def start_for_merch(chat_id: int, mk: str):
    """Запрашивает список номеров макетов для выбранного вида мерча."""
    WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})
    render_prompt(chat_id, mk)


def render_prompt(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"tmpl_nums_input:{mk}"
    tmpl_map = WIZ[chat_id]["data"]["templates"][mk]["templates"]
    existing = ", ".join(sorted(tmpl_map.keys(), key=lambda x: (len(x), x))) or "—"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:tmpl_num_done"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
    edit(
        chat_id,
        f"Шаг 3/4. Ввод номеров макетов ({mk}).\nСписок: {existing}\n\n"
        "Отправьте номера макетов через запятую: <b>1,2,3,A1,А2</b>",
        kb,
    )


def handle_text(chat_id: int, mk: str, text: str):
    """Обрабатывает введённую пользователем строку с номерами макетов."""
    tmpl_map = WIZ[chat_id]["data"]["templates"][mk]["templates"]
    items = [t.strip() for t in text.replace("\n", ",").split(",")]
    for item in items:
        if item:
            tmpl_map.setdefault(item, {"allowed_colors": []})
    render_prompt(chat_id, mk)


def done(chat_id: int):
    from .A7_TemplatesColors import render_for_next_template

    render_for_next_template(chat_id)

