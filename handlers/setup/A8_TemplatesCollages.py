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
    kb = types.InlineKeyboardMarkup()
    cnt = len(d["templates"][mk].get("collages", []))
    if cnt:
        kb.add(types.InlineKeyboardButton("🗑 Очистить", callback_data="setup:tmpl_coll_del"))
    kb.add(types.InlineKeyboardButton("Готово ✅", callback_data="setup:tmpl_collages_done"))
    kb.add(types.InlineKeyboardButton("Пропустить", callback_data="setup:tmpl_collages_done"))
    edit(chat_id,
         f"Шаг 3.3/4. Пришлите 1–5 изображений‑коллажей (со списком макетов).\nЗагружено коллажей: {cnt}",
         kb)
    WIZ[chat_id]["stage"] = f"tmpl_collages:{mk}"

def collages_done(chat_id: int):
    from .A9_InventorySizes import open_inventory_home
    open_inventory_home(chat_id)


def clear_collages(chat_id: int) -> None:
    mk = WIZ[chat_id]["data"].get("_mk_collages")
    if not mk:
        return
    WIZ[chat_id]["data"].get("templates", {}).get(mk, {}).setdefault("collages", []).clear()
    ask_collages_or_next(chat_id)
