\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit

def ask_collages_or_next(chat_id: int):
    d = WIZ[chat_id]["data"]
    has = [mk for mk, t in d.get("templates", {}).items() if t.get("templates")]
    if not has:
        from .A9_InventorySizes import open_inventory_home
        open_inventory_home(chat_id); return
    mk = has[0]
    WIZ[chat_id]["data"]["_mk_collages"] = mk
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("Готово ✅", callback_data="setup:tmpl_collages_done"))
    kb.add(types.InlineKeyboardButton("Пропустить", callback_data="setup:tmpl_collages_done"))
    kb.add(types.InlineKeyboardButton("Сбросить изображения (все макеты)", callback_data="setup:tmpl_collages_reset_all"))
    kb.add(types.InlineKeyboardButton("Сбросить изображения (этот макет)", callback_data=f"setup:tmpl_collages_reset_one:{mk}"))
    cnt = len(d["templates"][mk].get("collages", []))
    edit(chat_id,
         f"Шаг 3.3/4. Пришлите 1–5 изображений‑коллажей (со списком макетов).\nЗагружено коллажей: {cnt}",
         kb)
    WIZ[chat_id]["stage"] = f"tmpl_collages:{mk}"

def collages_done(chat_id: int):
    from .A9_InventorySizes import open_inventory_home
    open_inventory_home(chat_id)

def reset_all(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpl_collages"))
    edit(chat_id, "Type СБРОС to remove all layout images.", kb)
    WIZ[chat_id]["stage"] = "tmpl_collages_reset_all"

def reset_one(chat_id: int, mk: str):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpl_collages"))
    edit(chat_id, f"Type DELETE to remove images for {mk}.", kb)
    WIZ[chat_id]["stage"] = f"tmpl_collages_reset_one:{mk}"
