\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit

def open_inventory_sizes(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_sizes_home"
    d = WIZ[chat_id]["data"]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for mk, info in d.get("merch", {}).items():
        kb.add(types.InlineKeyboardButton(info["name_ru"], callback_data=f"setup:inv_sizes_colors:{mk}"))
    kb.add(types.InlineKeyboardButton("Готово → Буквы", callback_data="setup:inv_letters_next"))
    edit(chat_id, "Шаг 4/4. 📦 Остатки — выберите Вид мерча.", kb)

def open_colors(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"inv_sz_colors:{mk}"
    colors = WIZ[chat_id]["data"]["merch"][mk]["colors"]
    kb = types.InlineKeyboardMarkup(row_width=3)
    for ck, ci in colors.items():
        kb.add(types.InlineKeyboardButton(ci["name_ru"], callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv_sizes_home"))
    edit(chat_id, f"Остатки: <b>{WIZ[chat_id]['data']['merch'][mk]['name_ru']}</b> — выберите цвет.", kb)

def open_sizes(chat_id: int, mk: str, ck: str):
    WIZ[chat_id]["stage"] = f"inv_sz_sizes:{mk}:{ck}"
    sizes = WIZ[chat_id]["data"]["merch"][mk]["sizes"]
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    for sz in sizes:
        qty = inv.get(sz, 0)
        kb.add(types.InlineKeyboardButton(f"{sz}: {qty}", callback_data=f"setup:inv_sz_qty:{mk}:{ck}:{sz}"))
    kb.add(types.InlineKeyboardButton("➕ Применить ко всем размерам", callback_data=f"setup:inv_sz_apply_all:{mk}:{ck}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_sizes_colors:{mk}"))
    edit(chat_id, f"Остатки: <b>{WIZ[chat_id]['data']['merch'][mk]['name_ru']}/{WIZ[chat_id]['data']['merch'][mk]['colors'][ck]['name_ru']}</b> — выберите размер или задайте число для всех.", kb)

def open_qty_spinner(chat_id: int, mk: str, ck: str, sz: str):
    WIZ[chat_id]["stage"] = f"inv_sz_qty:{mk}:{ck}:{sz}"
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    cur = inv.get(sz, 0)
    kb = types.InlineKeyboardMarkup(row_width=5)
    kb.add(
        types.InlineKeyboardButton("−10", callback_data=f"setup:inv_sz_adj:{mk}:{ck}:{sz}:-10"),
        types.InlineKeyboardButton("−1",  callback_data=f"setup:inv_sz_adj:{mk}:{ck}:{sz}:-1"),
        types.InlineKeyboardButton("+1",  callback_data=f"setup:inv_sz_adj:{mk}:{ck}:{sz}:1"),
        types.InlineKeyboardButton("+10", callback_data=f"setup:inv_sz_adj:{mk}:{ck}:{sz}:10"),
    )
    kb.add(
        types.InlineKeyboardButton("0", callback_data=f"setup:inv_sz_set:{mk}:{ck}:{sz}:0"),
        types.InlineKeyboardButton("1", callback_data=f"setup:inv_sz_set:{mk}:{ck}:{sz}:1"),
        types.InlineKeyboardButton("2", callback_data=f"setup:inv_sz_set:{mk}:{ck}:{sz}:2"),
        types.InlineKeyboardButton("5", callback_data=f"setup:inv_sz_set:{mk}:{ck}:{sz}:5"),
        types.InlineKeyboardButton("10", callback_data=f"setup:inv_sz_set:{mk}:{ck}:{sz}:10"),
    )
    kb.add(types.InlineKeyboardButton("✅ Сохранить", callback_data=f"setup:inv_sz_save:{mk}:{ck}:{sz}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к размерам", callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    edit(chat_id, f"Введите количество для <b>{mk}/{ck}/{sz}</b>:\nТекущее: <b>{cur}</b>", kb)

def adjust_qty(chat_id: int, mk: str, ck: str, sz: str, delta: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    cur = inv.get(sz, 0)
    cur += delta
    if cur < 0: cur = 0
    inv[sz] = cur
    open_qty_spinner(chat_id, mk, ck, sz)

def set_qty(chat_id: int, mk: str, ck: str, sz: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    inv[sz] = max(0, val)
    open_qty_spinner(chat_id, mk, ck, sz)

def save_qty(chat_id: int, mk: str, ck: str, sz: str):
    open_sizes(chat_id, mk, ck)

def apply_all_sizes(chat_id: int, mk: str, ck: str):
    WIZ[chat_id]["stage"] = f"inv_sz_apply_all:{mk}:{ck}"
    kb = types.InlineKeyboardMarkup(row_width=5)
    for val in (0,1,2,5,10,15,20,25,30):
        kb.add(types.InlineKeyboardButton(str(val), callback_data=f"setup:inv_sz_all_set:{mk}:{ck}:{val}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    edit(chat_id, f"Применить одно число ко всем размерам <b>{mk}/{ck}</b>.", kb)

def set_all_sizes(chat_id: int, mk: str, ck: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    sizes = WIZ[chat_id]["data"]["merch"][mk]["sizes"]
    for sz in sizes:
        if inv.get(sz, 0) == 0:
            inv[sz] = val
    open_sizes(chat_id, mk, ck)


def open_letters_stub(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_letters_stub"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("✅ Пропустить", callback_data="setup:finish"))
    edit(chat_id, "Остатки букв пока не реализованы. Нажмите 'Пропустить' чтобы завершить.", kb)
