\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit, slugify, merch_tree
from utils.tg import color_key_from_ru, register_color_name

DEFAULT_MERCH  = [("tshirt","Футболки"),("shopper","Шопперы"),("mug","Кружки")]
DEFAULT_COLORS = [("white","Белый"),("black","Чёрный"),("red","Красный"),("blue","Синий"),("green","Зелёный"),("brown","Коричневый")]
DEFAULT_SIZES  = ["XS","S","M","L","XL","XXL"]
ONESIZE        = ["OneSize"]

def _header_with_tree(chat_id: int, title: str) -> str:
    d = WIZ[chat_id]["data"]
    tree = merch_tree(d)
    return f"<b>{title}</b>\n<pre>Структура\n{tree}\n</pre>"

def render_types(chat_id: int):
    d = WIZ[chat_id].setdefault("data", {})
    merch = d.setdefault("merch", {})
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in DEFAULT_MERCH:
        mark = "✓" if key in merch else "·"
        kb.add(types.InlineKeyboardButton(f"{name} {mark}", callback_data=f"setup:merch_toggle:{key}"))
    kb.add(types.InlineKeyboardButton("➕ Добавить вид", callback_data="setup:merch_add"))
    if merch:
        kb.add(types.InlineKeyboardButton("Далее: цвета/размеры →", callback_data="setup:colors_sizes"))
    kb.add(types.InlineKeyboardButton("🏠 Меню", callback_data="setup:home"))
    edit(chat_id, _header_with_tree(chat_id, "Шаг 1/4. Выберите виды мерча (переключатели)."), kb)
    WIZ[chat_id]["stage"] = "merch"

def toggle_type(chat_id: int, mk: str):
    d = WIZ[chat_id]["data"].setdefault("merch", {})
    if mk in d: d.pop(mk, None)
    else: d[mk] = {"name_ru": dict(DEFAULT_MERCH).get(mk, mk), "colors": {}, "sizes": []}
    render_types(chat_id)

def ask_custom(chat_id: int):
    WIZ[chat_id]["stage"] = "merch_add"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:merch"))
    edit(chat_id, _header_with_tree(chat_id, "Введите <b>название</b> нового мерча (ключ создадим автоматически)."), kb)

def handle_custom_input(chat_id: int, text: str):
    name = text.strip()
    d = WIZ[chat_id]["data"].setdefault("merch", {})
    key = slugify(name, used=list(d.keys()))
    d[key] = {"name_ru": name, "colors": {}, "sizes": []}
    render_types(chat_id)

def start_colors_iter(chat_id: int):
    keys = list(WIZ[chat_id]["data"].get("merch", {}).keys())
    WIZ[chat_id]["data"]["_merch_iter"] = keys
    if keys:
        render_colors(chat_id, keys.pop(0))
    else:
        render_types(chat_id)

def render_colors(chat_id: int, mk: str):
    d = WIZ[chat_id]["data"]
    item = d["merch"][mk]
    colors = item.setdefault("colors", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    for key, name in DEFAULT_COLORS:
        mark = "✓" if key in colors else "·"
        kb.add(types.InlineKeyboardButton(f"{name} {mark}", callback_data=f"setup:color_toggle:{mk}:{key}"))
    kb.add(types.InlineKeyboardButton("➕ Свой цвет", callback_data=f"setup:color_add:{mk}"))
    if colors:
        kb.add(types.InlineKeyboardButton("Далее: размеры →", callback_data=f"setup:sizes:{mk}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к мерчу", callback_data="setup:merch"))
    edit(chat_id, _header_with_tree(chat_id, f"Шаг 1.1/4. <b>{item['name_ru']}</b> — выберите цвета."), kb)
    WIZ[chat_id]["stage"] = f"colors:{mk}"

def toggle_color(chat_id: int, mk: str, ck: str):
    colors = WIZ[chat_id]["data"]["merch"][mk].setdefault("colors", {})
    if ck in colors: colors.pop(ck, None)
    else: colors[ck] = {"name_ru": dict(DEFAULT_COLORS).get(ck, ck)}
    render_colors(chat_id, mk)

def ask_custom_color(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"color_add:{mk}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:colors:{mk}"))
    edit(chat_id, _header_with_tree(chat_id, "Введите <b>название цвета</b> (ключ создадим автоматически)."), kb)

def handle_custom_color(chat_id: int, mk: str, text: str):
    name = text.strip()
    colors = WIZ[chat_id]["data"]["merch"][mk].setdefault("colors", {})
    used = list(colors.keys())
    key = color_key_from_ru(name, used)
    colors[key] = {"name_ru": name}
    WIZ[chat_id]["data"].setdefault("color_names", {})[key] = name
    register_color_name(key, name)
    render_colors(chat_id, mk)

def render_sizes(chat_id: int, mk: str):
    d = WIZ[chat_id]["data"]
    item = d["merch"][mk]
    sizes = item.get("sizes", [])
    sizes_text = ", ".join(sizes) if sizes else "—"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Стандартный ряд (XS..XXL)", callback_data=f"setup:sizes_default:{mk}"))
    kb.add(types.InlineKeyboardButton("OneSize", callback_data=f"setup:sizes_one:{mk}"))
    kb.add(types.InlineKeyboardButton("➕ Свой список", callback_data=f"setup:sizes_add:{mk}"))
    if sizes:
        kb.add(types.InlineKeyboardButton("Сохранить и следующий", callback_data="setup:next_merch_or_done"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад к цветам", callback_data=f"setup:colors:{mk}"))
    kb.add(types.InlineKeyboardButton("↩️ К видам мерча", callback_data="setup:merch"))
    edit(chat_id, _header_with_tree(chat_id, f"Шаг 1.2/4. <b>{item['name_ru']}</b> — размеры.\nТекущие: {sizes_text}"), kb)
    WIZ[chat_id]["stage"] = f"sizes:{mk}"

def set_default_sizes(chat_id: int, mk: str):
    WIZ[chat_id]['data']['merch'][mk]['sizes'] = DEFAULT_SIZES[:]
    render_sizes(chat_id, mk)

def set_one_size(chat_id: int, mk: str):
    WIZ[chat_id]['data']['merch'][mk]['sizes'] = ONESIZE[:]
    render_sizes(chat_id, mk)

def ask_custom_sizes(chat_id: int, mk: str):
    WIZ[chat_id]["stage"] = f"sizes_add:{mk}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:sizes:{mk}"))
    edit(chat_id, _header_with_tree(chat_id, "Введите размеры через запятую (пример: 3XS,2XS,XS,S,M,L,XL)."), kb)

def handle_custom_sizes(chat_id: int, mk: str, text: str):
    parts = [p.strip() for p in text.replace("，", ",").replace(";", ",").split(",") if p.strip()]
    if parts:
        WIZ[chat_id]["data"]["merch"][mk]["sizes"] = parts
    render_sizes(chat_id, mk)

def next_merch_or_done(chat_id: int):
    it = WIZ[chat_id]["data"].get("_merch_iter", [])
    if it:
        mk = it.pop(0)
        render_colors(chat_id, mk)
    else:
        from .A2_Letters import render_letters_hub
        render_letters_hub(chat_id)
