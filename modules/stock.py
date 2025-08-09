# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import get_settings
from services.inventory import get_merch_inv, save_merch_inv

@bot.message_handler(commands=["stock"])
def cmd_stock(message: types.Message) -> None:
    s = get_settings()
    inv = get_merch_inv()
    kb = types.InlineKeyboardMarkup(row_width=2)
    for mk, info in s.get("merch", {}).items():
        kb.add(types.InlineKeyboardButton(info.get("name_ru", mk), callback_data=f"stk:mk:{mk}"))
    bot.send_message(message.chat.id, "Выберите мерч для редактирования остатков:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("stk:mk:"))
def stk_choose_mk(c: types.CallbackQuery):
    mk = c.data.split(":")[2]
    s = get_settings()
    kb = types.InlineKeyboardMarkup(row_width=2)
    for ck, info in s.get("merch", {}).get(mk, {}).get("colors", {}).items():
        kb.add(types.InlineKeyboardButton(info.get("name_ru", ck), callback_data=f"stk:ck:{mk}:{ck}"))
    bot.edit_message_text("Выберите цвет:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("stk:ck:"))
def stk_choose_ck(c: types.CallbackQuery):
    _, _, mk, ck = c.data.split(":")
    inv = get_merch_inv()
    sizes = list(get_settings()["merch"][mk]["sizes"])
    cur = inv.get(mk, {}).get(ck, {}).get("sizes", {})
    kb = types.InlineKeyboardMarkup(row_width=2)
    for sz in sizes:
        qty = cur.get(sz, 0)
        kb.add(types.InlineKeyboardButton(f"{sz}: {qty}", callback_data=f"stk:sz:{mk}:{ck}:{sz}"))
    bot.edit_message_text("Выберите размер для изменения:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("stk:sz:"))
def stk_edit_sz(c: types.CallbackQuery):
    _, _, mk, ck, sz = c.data.split(":")
    bot.edit_message_text(f"Введите новое количество для {mk}/{ck}/{sz}:", c.message.chat.id, c.message.message_id)
    bot.register_next_step_handler(c.message, lambda m: _apply_qty(m, mk, ck, sz))

def _apply_qty(m: types.Message, mk: str, ck: str, sz: str):
    try:
        q = int(m.text.strip())
        if q < 0: raise ValueError
    except Exception:
        bot.reply_to(m, "Введите неотрицательное число."); return
    inv = get_merch_inv()
    inv.setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
    inv[mk][ck]["sizes"][sz] = q
    save_merch_inv(inv)
    bot.reply_to(m, "✅ Сохранено.")
