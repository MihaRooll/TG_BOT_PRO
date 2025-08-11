# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit
from utils.tg import color_name_ru


def open_inventory_home(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_home"
    d = WIZ[chat_id]["data"]
    inv_merch = d.get("_inv_merch", {})
    inv_letters = d.get("_inv_letters", {})
    inv_numbers = d.get("_inv_numbers", {})
    inv_tmpls = d.get("_inv_tmpls", {})
    inv_on = bool(inv_merch or inv_letters or inv_numbers or inv_tmpls)
    block = [
        f"📦 Остатки [✅ ВКЛ]{' ✅ — внесли' if inv_on else ' — не внесли'}",
        f"├─ Размеры: {'✅ — внесли' if inv_merch else '— не внесли'}",
        f"├─ Буквы: {'✅ — внесли' if inv_letters else '— не внесли'}",
        f"├─ Цифры: {'✅ — внесли' if inv_numbers else '— не внесли'}",
        f"└─ Макеты: {'✅ — внесли' if inv_tmpls else '— не внесли'}",
    ]
    block_txt = "\n".join(block)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("Размеры", callback_data="setup:inv_merch"))
    kb.add(types.InlineKeyboardButton("Буквы", callback_data="setup:inv_letters"))
    kb.add(types.InlineKeyboardButton("Цифры", callback_data="setup:inv_numbers"))
    kb.add(types.InlineKeyboardButton("Макеты", callback_data="setup:inv_templates"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
    kb.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="setup:home"))
    edit(
        chat_id,
        f"Шаг 4/4. 📦 Остатки — выберите Вид мерча.\n<pre>{block_txt}</pre>",
        kb,
    )


def open_merch_list(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_merch"
    d = WIZ[chat_id]["data"]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for mk, info in d.get("merch", {}).items():
        kb.add(
            types.InlineKeyboardButton(
                info["name_ru"], callback_data=f"setup:inv_sizes_colors:{mk}"
            )
        )
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv"))
    edit(chat_id, "Остатки: выберите вид мерча.", kb)

def open_colors(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"inv_sz_colors:{mk}"
    colors = WIZ[chat_id]["data"]["merch"][mk]["colors"]
    kb = types.InlineKeyboardMarkup(row_width=3)
    for ck, ci in colors.items():
        kb.add(types.InlineKeyboardButton(ci["name_ru"], callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv_merch"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv_merch"))
    edit(chat_id, f"Остатки: <b>{WIZ[chat_id]['data']['merch'][mk]['name_ru']}</b> — выберите цвет.", kb)

def open_sizes(chat_id: int, mk: str, ck: str):
    WIZ[chat_id]["stage"] = f"inv_sz_sizes:{mk}:{ck}"
    sizes = WIZ[chat_id]["data"]["merch"][mk]["sizes"]
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    for sz in sizes:
        qty = inv.get(sz, 0)
        kb.add(types.InlineKeyboardButton(f"{sz}: {qty}", callback_data=f"setup:inv_sz_qty:{mk}:{ck}:{sz}"))
    kb.add(types.InlineKeyboardButton("Задать число для всех", callback_data=f"setup:inv_sz_apply_all:{mk}:{ck}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data=f"setup:inv_sizes_colors:{mk}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_sizes_colors:{mk}"))
    merch_name = WIZ[chat_id]["data"]["merch"][mk]["name_ru"]
    color_name = WIZ[chat_id]["data"]["merch"][mk]["colors"][ck]["name_ru"]
    edit(
        chat_id,
        f"Остатки: <b>{merch_name}/{color_name}</b> — выберите размер или задайте число для всех.",
        kb,
    )

def open_qty_spinner(chat_id: int, mk: str, ck: str, sz: str):
    WIZ[chat_id]["stage"] = f"inv_sz_qty:{mk}:{ck}:{sz}"
    inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    cur = inv.get(sz, 0)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    edit(chat_id, f"Введите количество для <b>{mk}/{ck}/{sz}</b>:\nТекущее: <b>{cur}</b>", kb)


def apply_all_sizes(chat_id: int, mk: str, ck: str):
    WIZ[chat_id]["stage"] = f"inv_sz_all:{mk}:{ck}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_sizes_sizes:{mk}:{ck}"))
    edit(chat_id, f"Введите одно число для всех размеров <b>{mk}/{ck}</b>.", kb)


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
        kb.add(types.InlineKeyboardButton(color_name_ru(tc), callback_data=f"setup:inv_letters_chars:{tc}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv"))
    edit(chat_id, "Остатки букв — выберите <b>цвет текста</b>.", kb)

def open_letters_chars(chat_id: int, tc: str):
    WIZ[chat_id]["stage"] = f"inv_lt_letters:{tc}"
    letters = _letters(chat_id)
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    for ch in letters:
        qty = inv.get(ch, 0)
        kb.add(types.InlineKeyboardButton(f"{ch}: {qty}", callback_data=f"setup:inv_lt_qty:{tc}:{ch}"))
    kb.add(types.InlineKeyboardButton("Задать число для всех", callback_data=f"setup:inv_lt_apply_all:{tc}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv_letters"))
    edit(chat_id, f"Остатки букв: <b>{color_name_ru(tc)}</b> — выберите букву.", kb)

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
    edit(chat_id, f"Введите количество для <b>{ch}</b> цвета <b>{color_name_ru(tc)}</b>:\nТекущее: <b>{cur}</b>", kb)

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
    WIZ[chat_id]["stage"] = f"inv_lt_all:{tc}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_letters_chars:{tc}"))
    edit(chat_id, f"Введите одно число для всех букв <b>{color_name_ru(tc)}</b>.", kb)


def set_all_letters(chat_id: int, tc: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
    for ch in _letters(chat_id):
        inv[ch] = val
    open_letters_chars(chat_id, tc)


# --------- numbers inventory ----------
DIGITS = list("0123456789")

def open_inventory_numbers(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_numbers_home"
    d = WIZ[chat_id]["data"]
    pal = d.get("text_palette", [])
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tc in pal:
        kb.add(types.InlineKeyboardButton(color_name_ru(tc), callback_data=f"setup:inv_numbers_digits:{tc}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv"))
    edit(chat_id, "Остатки цифр — выберите <b>цвет цифр</b>.", kb)

def open_numbers_digits(chat_id: int, tc: str):
    WIZ[chat_id]["stage"] = f"inv_nb_digits:{tc}"
    inv = WIZ[chat_id]["data"].setdefault("_inv_numbers", {}).setdefault(tc, {}).setdefault("numbers", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    for dg in DIGITS:
        qty = inv.get(dg, 0)
        kb.add(types.InlineKeyboardButton(f"{dg}: {qty}", callback_data=f"setup:inv_nb_qty:{tc}:{dg}"))
    kb.add(types.InlineKeyboardButton("Задать число для всех", callback_data=f"setup:inv_nb_apply_all:{tc}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv_numbers"))
    edit(chat_id, f"Остатки цифр: <b>{color_name_ru(tc)}</b> — выберите цифру.", kb)

def open_number_qty_spinner(chat_id: int, tc: str, dg: str):
    WIZ[chat_id]["stage"] = f"inv_nb_qty:{tc}:{dg}"
    inv = WIZ[chat_id]["data"].setdefault("_inv_numbers", {}).setdefault(tc, {}).setdefault("numbers", {})
    cur = inv.get(dg, 0)
    kb = types.InlineKeyboardMarkup(row_width=5)
    kb.add(
        types.InlineKeyboardButton("−10", callback_data=f"setup:inv_nb_adj:{tc}:{dg}:-10"),
        types.InlineKeyboardButton("−1",  callback_data=f"setup:inv_nb_adj:{tc}:{dg}:-1"),
        types.InlineKeyboardButton("+1",  callback_data=f"setup:inv_nb_adj:{tc}:{dg}:1"),
        types.InlineKeyboardButton("+10", callback_data=f"setup:inv_nb_adj:{tc}:{dg}:10"),
    )
    kb.add(
        types.InlineKeyboardButton("0", callback_data=f"setup:inv_nb_set:{tc}:{dg}:0"),
        types.InlineKeyboardButton("1", callback_data=f"setup:inv_nb_set:{tc}:{dg}:1"),
        types.InlineKeyboardButton("2", callback_data=f"setup:inv_nb_set:{tc}:{dg}:2"),
        types.InlineKeyboardButton("5", callback_data=f"setup:inv_nb_set:{tc}:{dg}:5"),
        types.InlineKeyboardButton("10", callback_data=f"setup:inv_nb_set:{tc}:{dg}:10"),
    )
    kb.add(types.InlineKeyboardButton("✅ Сохранить", callback_data=f"setup:inv_nb_save:{tc}:{dg}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к цифрам", callback_data=f"setup:inv_numbers_digits:{tc}"))
    edit(chat_id, f"Введите количество для цифры <b>{dg}</b> цвета <b>{color_name_ru(tc)}</b>:\nТекущее: <b>{cur}</b>", kb)

def adjust_number_qty(chat_id: int, tc: str, dg: str, delta: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_numbers", {}).setdefault(tc, {}).setdefault("numbers", {})
    cur = inv.get(dg, 0) + delta
    if cur < 0:
        cur = 0
    inv[dg] = cur
    open_number_qty_spinner(chat_id, tc, dg)

def set_number_qty(chat_id: int, tc: str, dg: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_numbers", {}).setdefault(tc, {}).setdefault("numbers", {})
    inv[dg] = max(0, val)
    open_number_qty_spinner(chat_id, tc, dg)

def save_number_qty(chat_id: int, tc: str, dg: str):
    open_numbers_digits(chat_id, tc)

def apply_all_numbers(chat_id: int, tc: str):
    WIZ[chat_id]["stage"] = f"inv_nb_all:{tc}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_numbers_digits:{tc}"))
    edit(chat_id, f"Введите одно число для всех цифр <b>{color_name_ru(tc)}</b>.", kb)


def set_all_numbers(chat_id: int, tc: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_numbers", {}).setdefault(tc, {}).setdefault("numbers", {})
    for dg in DIGITS:
        inv[dg] = val
    open_numbers_digits(chat_id, tc)


# --------- templates inventory ----------
def open_inventory_templates(chat_id: int):
    WIZ[chat_id]["stage"] = "inv_tmpls_home"
    d = WIZ[chat_id]["data"]
    kb = types.InlineKeyboardMarkup(row_width=1)
    for mk, tinfo in d.get("templates", {}).items():
        if tinfo.get("templates"):
            name = d.get("merch", {}).get(mk, {}).get("name_ru", mk)
            kb.add(types.InlineKeyboardButton(name, callback_data=f"setup:inv_tmpl_nums:{mk}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv"))
    edit(chat_id, "Остатки макетов — выберите <b>вид мерча</b>.", kb)

def open_template_numbers(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"inv_tmpl_nums:{mk}"
    tpls = WIZ[chat_id]["data"].get("templates", {}).get(mk, {}).get("templates", {})
    inv = WIZ[chat_id]["data"].setdefault("_inv_tmpls", {}).setdefault(mk, {}).setdefault("templates", {})
    nums_sorted = sorted(tpls.keys(), key=lambda x: (len(x), x))
    kb = types.InlineKeyboardMarkup(row_width=4)
    for num in nums_sorted:
        qty = inv.get(num, {}).get("qty", 0)
        kb.add(types.InlineKeyboardButton(f"{num}: {qty}", callback_data=f"setup:inv_tmpl_qty:{mk}:{num}"))
    kb.add(types.InlineKeyboardButton("Задать число для всех", callback_data=f"setup:inv_tmpl_apply_all:{mk}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:inv"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:inv_templates"))
    edit(chat_id,
         f"Остатки макетов — выберите номера макетов ({WIZ[chat_id]['data']['merch'][mk]['name_ru']}).",
         kb)

def open_template_qty_spinner(chat_id: int, mk: str, num: str):
    WIZ[chat_id]["stage"] = f"inv_tmpl_qty:{mk}:{num}"
    inv = WIZ[chat_id]["data"].setdefault("_inv_tmpls", {}).setdefault(mk, {}).setdefault("templates", {})
    cur = inv.setdefault(num, {}).get("qty", 0)
    kb = types.InlineKeyboardMarkup(row_width=5)
    kb.add(
        types.InlineKeyboardButton("−10", callback_data=f"setup:inv_tmpl_adj:{mk}:{num}:-10"),
        types.InlineKeyboardButton("−1",  callback_data=f"setup:inv_tmpl_adj:{mk}:{num}:-1"),
        types.InlineKeyboardButton("+1",  callback_data=f"setup:inv_tmpl_adj:{mk}:{num}:1"),
        types.InlineKeyboardButton("+10", callback_data=f"setup:inv_tmpl_adj:{mk}:{num}:10"),
    )
    kb.add(
        types.InlineKeyboardButton("0", callback_data=f"setup:inv_tmpl_set:{mk}:{num}:0"),
        types.InlineKeyboardButton("1", callback_data=f"setup:inv_tmpl_set:{mk}:{num}:1"),
        types.InlineKeyboardButton("2", callback_data=f"setup:inv_tmpl_set:{mk}:{num}:2"),
        types.InlineKeyboardButton("5", callback_data=f"setup:inv_tmpl_set:{mk}:{num}:5"),
        types.InlineKeyboardButton("10", callback_data=f"setup:inv_tmpl_set:{mk}:{num}:10"),
    )
    kb.add(types.InlineKeyboardButton("✅ Сохранить", callback_data=f"setup:inv_tmpl_save:{mk}:{num}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к номерам", callback_data=f"setup:inv_tmpl_nums:{mk}"))
    edit(chat_id, f"Введите количество макетов <b>{num}</b> для {WIZ[chat_id]['data']['merch'][mk]['name_ru']}:\nТекущее: <b>{cur}</b>", kb)

def adjust_template_qty(chat_id: int, mk: str, num: str, delta: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_tmpls", {}).setdefault(mk, {}).setdefault("templates", {})
    cur = inv.setdefault(num, {}).get("qty", 0) + delta
    if cur < 0:
        cur = 0
    inv[num]["qty"] = cur
    open_template_qty_spinner(chat_id, mk, num)

def set_template_qty(chat_id: int, mk: str, num: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_tmpls", {}).setdefault(mk, {}).setdefault("templates", {})
    inv.setdefault(num, {})["qty"] = max(0, val)
    open_template_qty_spinner(chat_id, mk, num)

def save_template_qty(chat_id: int, mk: str, num: str):
    open_template_numbers(chat_id, mk)

def apply_all_templates(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"inv_tmpl_all:{mk}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:inv_tmpl_nums:{mk}"))
    edit(chat_id, f"Введите одно число ко всем макетам <b>{WIZ[chat_id]['data']['merch'][mk]['name_ru']}</b>.", kb)


def set_all_templates(chat_id: int, mk: str, val: int):
    inv = WIZ[chat_id]["data"].setdefault("_inv_tmpls", {}).setdefault(mk, {}).setdefault("templates", {})
    nums = WIZ[chat_id]["data"].get("templates", {}).get(mk, {}).get("templates", {})
    for num in nums.keys():
        inv.setdefault(num, {})["qty"] = val
    open_template_numbers(chat_id, mk)
