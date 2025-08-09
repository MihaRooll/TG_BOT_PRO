\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit

def render_next_pair(chat_id: int):
    d = WIZ[chat_id]["data"]
    pal = d.get("text_palette", [])
    merch = d.get("merch", {})
    ctx = WIZ[chat_id].setdefault("ctx", {})

    pair = ctx.get("maptc_pair")
    if pair is None:
        for mk, mi in merch.items():
            for ck in mi.get("colors", {}).keys():
                cur = d.setdefault("text_colors", {}).setdefault(mk, {}).setdefault(ck, [])
                if not cur and pal:
                    pair = (mk, ck)
                    break
            if pair:
                break

    kb = types.InlineKeyboardMarkup(row_width=3)
    if not merch:
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
        edit(chat_id, "Сначала добавьте мерч и цвета.", kb)
        WIZ[chat_id]["stage"] = "map_text_colors"; return
    if not pal:
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
        edit(chat_id, "Сначала выберите палитру цветов текста.", kb)
        WIZ[chat_id]["stage"] = "map_text_colors"; return

    if pair is None:
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
        edit(chat_id, "Соответствия заданы для всех цветов мерча. ☑", kb)
        WIZ[chat_id]["stage"] = "map_text_colors"; return

    mk, ck = pair
    ctx["maptc_pair"] = pair
    merch_name = merch[mk]["name_ru"]
    color_name = merch[mk]["colors"][ck]["name_ru"]
    cur = set(d["text_colors"][mk][ck])
    for tc in pal:
        mark = "✓" if tc in cur else "·"
        kb.add(types.InlineKeyboardButton(f"{tc} {mark}", callback_data=f"setup:maptc_toggle:{mk}:{ck}:{tc}"))
    kb.add(types.InlineKeyboardButton("Далее →", callback_data="setup:maptc_next"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
    edit(chat_id, f"Шаг 2.1/4. {merch_name} / {color_name}: выберите допустимые <b>цвета букв/цифр</b> (можно несколько).", kb)
    WIZ[chat_id]["stage"] = "map_text_colors"

def toggle_map(chat_id: int, mk: str, ck: str, tc: str):
    d = WIZ[chat_id]["data"].setdefault("text_colors", {})
    d.setdefault(mk, {})
    cur = d[mk].setdefault(ck, [])
    if tc in cur: cur.remove(tc)
    else: cur.append(tc)
    render_next_pair(chat_id)

def next_pair(chat_id: int):
    WIZ[chat_id].setdefault("ctx", {})["maptc_pair"] = None
    render_next_pair(chat_id)
