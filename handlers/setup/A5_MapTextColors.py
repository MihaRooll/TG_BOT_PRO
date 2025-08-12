\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit
from utils.tg import color_name_ru


def render_pair(chat_id: int, mk: str, ck: str) -> None:
    """Show palette selection for a concrete merch/color pair."""
    d = WIZ[chat_id]["data"]
    pal = d.get("text_palette", [])
    merch = d.get("merch", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    cur = set(d.setdefault("text_colors", {}).setdefault(mk, {}).setdefault(ck, []))
    for tc in pal:
        mark = "✅" if tc in cur else "□"
        kb.add(
            types.InlineKeyboardButton(
                f"{mark} {color_name_ru(tc)}",
                callback_data=f"setup:maptc_toggle:{mk}:{ck}:{tc}",
            )
        )
    kb.add(types.InlineKeyboardButton("Готово", callback_data="setup:maptc_next"))
    kb.add(
        types.InlineKeyboardButton("Сбросить выбор", callback_data=f"setup:maptc_reset:{mk}:{ck}")
    )
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))

    merch_name = merch[mk]["name_ru"]
    color_name = merch[mk]["colors"][ck]["name_ru"]
    lines = [
        f"📍 Шаг 2.1 / 4 — Настройка палитры для {merch_name}",
        f"👕 Вид мерча: {merch_name}",
        f"🎨 Цвет товара: {color_name}",
        "",
        "Выберите допустимые цвета букв и цифр:",
    ]
    text = "\n".join(lines)
    edit(chat_id, text, kb)
    WIZ[chat_id]["stage"] = "map_text_colors"

    # mark this pair as reviewed under current palette size
    seen = d.setdefault("_maptc_seen", {}).setdefault(mk, {})
    seen[ck] = len(pal)


def render_next_pair(chat_id: int) -> None:
    d = WIZ[chat_id]["data"]
    pal = d.get("text_palette", [])
    merch = d.get("merch", {})
    kb = types.InlineKeyboardMarkup(row_width=3)

    if not merch:
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
        edit(chat_id, "Сначала добавьте мерч и цвета.", kb)
        WIZ[chat_id]["stage"] = "map_text_colors"
        return
    if not pal:
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
        edit(chat_id, "Сначала выберите палитру цветов текста.", kb)
        WIZ[chat_id]["stage"] = "map_text_colors"
        return

    seen = d.setdefault("_maptc_seen", {})
    for mk, mi in merch.items():
        for ck in mi.get("colors", {}):
            cur = d.setdefault("text_colors", {}).setdefault(mk, {}).setdefault(ck, [])
            if seen.get(mk, {}).get(ck) != len(pal):
                render_pair(chat_id, mk, ck)
                return
            if not cur and pal:
                render_pair(chat_id, mk, ck)
                return

    kb.add(types.InlineKeyboardButton("Изменить настройки соответствий", callback_data="setup:maptc_edit"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
    edit(chat_id, "Соответствия заданы для всех цветов мерча. ✅", kb)
    WIZ[chat_id]["stage"] = "map_text_colors"


def toggle_map(chat_id: int, mk: str, ck: str, tc: str) -> None:
    d = WIZ[chat_id]["data"].setdefault("text_colors", {})
    cur = d.setdefault(mk, {}).setdefault(ck, [])
    if tc in cur:
        cur.remove(tc)
    else:
        cur.append(tc)
    render_pair(chat_id, mk, ck)


def reset_map(chat_id: int, mk: str, ck: str) -> None:
    d = WIZ[chat_id]["data"].setdefault("text_colors", {})
    d.setdefault(mk, {})[ck] = []
    render_pair(chat_id, mk, ck)


def next_pair(chat_id: int) -> None:
    render_next_pair(chat_id)


def edit_all(chat_id: int) -> None:
    """Re-open the correspondence editor with existing values."""
    WIZ[chat_id]["data"].pop("_maptc_seen", None)
    render_next_pair(chat_id)
