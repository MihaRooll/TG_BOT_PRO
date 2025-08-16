\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit

def start_for_merchs(chat_id: int, mks: list[str], done_cb=None):
    d = WIZ[chat_id]["data"]
    d["_collages_queue"] = mks
    d["_collages_done"] = done_cb
    _next(chat_id)


def _next(chat_id: int):
    d = WIZ[chat_id]["data"]
    queue = d.get("_collages_queue", [])
    while queue:
        mk = queue[0]
        if d.get("templates", {}).get(mk, {}).get("templates"):
            d["_mk_collages"] = mk
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("Готово ✅", callback_data="setup:tmpl_collages_done"))
            kb.add(types.InlineKeyboardButton("Пропустить", callback_data="setup:tmpl_collages_done"))
            kb.add(types.InlineKeyboardButton("Сбросить изображения (все макеты)", callback_data="setup:tmpl_collages_reset_all"))
            kb.add(types.InlineKeyboardButton(
                "Сбросить изображения (этот макет)",
                callback_data=f"setup:tmpl_collages_reset_one:{mk}",
            ))
            cnt = len(d["templates"][mk].get("collages", []))
            edit(
                chat_id,
                f"Шаг 3.3/4. Пришлите 1–5 изображений‑коллажей (со списком макетов).\nЗагружено коллажей: {cnt}",
                kb,
            )
            WIZ[chat_id]["stage"] = f"tmpl_collages:{mk}"
            return
        else:
            queue.pop(0)
    done = d.pop("_collages_done", None)
    if callable(done):
        done(chat_id)
    else:
        from .A9_InventorySizes import open_inventory_home
        open_inventory_home(chat_id)

def collages_done(chat_id: int):
    d = WIZ[chat_id]["data"]
    queue = d.get("_collages_queue", [])
    if queue:
        queue.pop(0)
    _next(chat_id)


def resume(chat_id: int):
    _next(chat_id)

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
