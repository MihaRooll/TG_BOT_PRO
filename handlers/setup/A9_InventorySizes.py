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
    kb.add(types.InlineKeyboardButton("Готово → Буквы", callback_data="setup:inv_letters"))
    edit(chat_id, "Шаг 4/4. 📦 Остатки — выберите Вид мерча.", kb)

def open_colors(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"inv_sz_colors:{mk}"
    colors = WIZ[chat_id]["data"]["merch"][mk]["colors"]
    kb = types.InlineKeyboardMarkup(row_width=3)
    for ck, ci in colors.items():
        kb.add(types.InlineKeyboardButton(ci["name_ru"], callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv_letters"))
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


LAT = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
CYR = list("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")

def _letters(chat_id: int):
    rules = WIZ[chat_id]["data"].setdefault("text_rules", {})
    letters = []
    if rules.get("allow_latin", True):
        letters += LAT
    if rules.get("allow_cyrillic"):
        letters += CYR
    return letters

def open_inventory_letters(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_letters_home"
    d = WIZ[chat_id]["data"]
    pal = d.get("text_palette", [])
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tc in pal:
        kb.add(types.InlineKeyboardButton(tc, callback_data=f"setup:inv_letters_chars:{tc}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("✅ Пропустить", callback_data="setup:finish"))
    edit(chat_id, "Остатки букв — выберите <b>цвет текста</b>.", kb)

def open_letters_chars(chat_id: int, tc: str):
    WIZ[chat_id]["stage"] = f"inv_lt_letters:{tc}"
    letters = _letters(chat_id)
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    kb = types.InlineKeyboardMarkup(row_width=6)
    for ch in letters:
        qty = inv.get(ch, 0)
        kb.add(types.InlineKeyboardButton(f"{ch}: {qty}", callback_data=f"setup:inv_lt_qty:{tc}:{ch}"))
    kb.add(types.InlineKeyboardButton("➕ Применить ко всем", callback_data=f"setup:inv_lt_apply_all:{tc}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv_letters"))
    edit(chat_id, f"Остатки букв: <b>{tc}</b> — выберите букву.", kb)

def open_letter_qty_spinner(chat_id: int, tc: str, ch: str):
    WIZ[chat_id]["stage"] = f"inv_lt_qty:{tc}:{ch}"
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    cur = inv.get(ch, 0)
    kb = types.InlineKeyboardMarkup(row_width=5)
    kb.add(
        types.InlineKeyboardButton("−10", callback_data=f"setup:inv_lt_adj:{tc}:{ch}:-10"),
        types.InlineKeyboardButton("−1",  callback_data=f"setup:inv_lt_adj:{tc}:{ch}:-1"),
        types.InlineKeyboardButton("+1",  callback_data=f"setup:inv_lt_adj:{tc}:{ch}:1"),
        types.InlineKeyboardButton("+10", callback_data=f"setup:inv_lt_adj:{tc}:{ch}:10"),
    )
    kb.add(
        types.InlineKeyboardButton("0", callback_data=f"setup:inv_lt_set:{tc}:{ch}:0"),
        types.InlineKeyboardButton("1", callback_data=f"setup:inv_lt_set:{tc}:{ch}:1"),
        types.InlineKeyboardButton("2", callback_data=f"setup:inv_lt_set:{tc}:{ch}:2"),
        types.InlineKeyboardButton("5", callback_data=f"setup:inv_lt_set:{tc}:{ch}:5"),
        types.InlineKeyboardButton("10", callback_data=f"setup:inv_lt_set:{tc}:{ch}:10"),
    )
    kb.add(types.InlineKeyboardButton("✅ Сохранить", callback_data=f"setup:inv_lt_save:{tc}:{ch}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к буквам", callback_data=f"setup:inv_letters_chars:{tc}"))
    edit(chat_id, f"Введите количество для <b>{ch}</b> цвета <b>{tc}</b>:\nТекущее: <b>{cur}</b>", kb)

def adjust_letter_qty(chat_id: int, tc: str, ch: str, delta: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    cur = inv.get(ch, 0) + delta
    if cur < 0:
        cur = 0
    inv[ch] = cur
    open_letter_qty_spinner(chat_id, tc, ch)

def set_letter_qty(chat_id: int, tc: str, ch: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    inv[ch] = max(0, val)
    open_letter_qty_spinner(chat_id, tc, ch)

def save_letter_qty(chat_id: int, tc: str, ch: str):
    open_letters_chars(chat_id, tc)

def apply_all_letters(chat_id: int, tc: str):
    WIZ[chat_id]["stage"] = f"inv_lt_apply_all:{tc}"
    kb = types.InlineKeyboardMarkup(row_width=5)
    for val in (0,1,2,5,10,15,20,25,30):
        kb.add(types.InlineKeyboardButton(str(val), callback_data=f"setup:inv_lt_all_set:{tc}:{val}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_letters_chars:{tc}"))
    edit(chat_id, f"Применить одно число ко всем буквам <b>{tc}</b>.", kb)

def set_all_letters(chat_id: int, tc: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    for ch in _letters(chat_id):
        if inv.get(ch, 0) == 0:
            inv[ch] = val
    open_letters_chars(chat_id, tc)
