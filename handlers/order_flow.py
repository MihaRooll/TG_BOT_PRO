# -*- coding: utf-8 -*-
import html
from telebot import types
from telebot.apihelper import ApiTelegramException
from bot import bot
import config
from services.settings import get_settings, get_admin_bind
from services.roles import is_admin, is_employee
from services.inventory import (
    get_merch_inv, get_letters_inv, get_numbers_inv, get_templates_inv,
    dec_size, dec_letter, dec_number, dec_template
)
from services.validators import validate_text, validate_number
from utils.tg import safe_delete, safe_edit_message

# Временные заказы (по chat_id)
ORD: dict[int, dict] = {}

def _admin_target():
    chat_id, thread_id = get_admin_bind()
    if chat_id:
        return chat_id, thread_id
    return getattr(config, "ADMIN_CHAT_ID", None), None

def _send_to_admin_or_warn(user_chat_id: int, text: str) -> None:
    target, thread_id = _admin_target()
    if not target:
        bot.send_message(user_chat_id, "⚠️ Не задан общий чат. Выполните /bind_here в нужном чате.")
        return
    try:
        if thread_id:
            bot.send_message(target, text, parse_mode="HTML", message_thread_id=thread_id)
        else:
            bot.send_message(target, text, parse_mode="HTML")
    except ApiTelegramException as e:
        if "chat not found" in str(e).lower():
            bot.send_message(user_chat_id, "⚠️ Бот не добавлен в общий чат или нет прав. Выполните /bind_here в том чате.")
        else:
            raise


@bot.message_handler(commands=["order"])
def order_cmd(m: types.Message):
    if not (is_admin(m.from_user.id) or is_employee(m.from_user.id)):
        bot.reply_to(m, "Нет доступа.")
        return
    s = get_settings()
    if not s.get("configured"):
        bot.reply_to(m, "Бот не настроен. Нажмите /start и пройдите мастер.")
        return
    merch = s.get("merch", {})
    kb = types.InlineKeyboardMarkup(row_width=2)
    for mk, info in merch.items():
        kb.add(types.InlineKeyboardButton(info.get("name_ru", mk), callback_data=f"order:m:{mk}"))
    bot.send_message(m.chat.id, "Выберите вид мерча:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "order:start")
def order_start(c: types.CallbackQuery):
    if not (is_admin(c.from_user.id) or is_employee(c.from_user.id)):
        bot.answer_callback_query(c.id, "Нет доступа", show_alert=True)
        return
    s = get_settings()
    if not s.get("configured"):
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "Бот не настроен. Нажмите /start и пройдите мастер.")
        return
    merch = s.get("merch", {})
    kb = types.InlineKeyboardMarkup(row_width=2)
    for mk, info in merch.items():
        kb.add(types.InlineKeyboardButton(info.get("name_ru", mk), callback_data=f"order:m:{mk}"))
    bot.edit_message_text("Выберите вид мерча:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:m:"))
def order_choose_merch(c: types.CallbackQuery):
    mk = c.data.split(":")[2]
    s = get_settings()
    inv = get_merch_inv()
    # показать только цвета, у которых есть доступные размеры (>0)
    kb = types.InlineKeyboardMarkup(row_width=2)
    added = False
    for ck, info in s.get("merch", {}).get(mk, {}).get("colors", {}).items():
        sizes = inv.get(mk, {}).get(ck, {}).get("sizes", {})
        if any(q > 0 for q in sizes.values()):
            kb.add(types.InlineKeyboardButton(info.get("name_ru", ck), callback_data=f"order:c:{mk}:{ck}"))
            added = True
    if not added:
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "К сожалению, нет доступных цветов/размеров. Обновите остатки.")
        return
    ORD[c.message.chat.id] = {"merch": mk}
    bot.edit_message_text("Выберите цвет:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:c:"))
def order_choose_color(c: types.CallbackQuery):
    _, _, mk, ck = c.data.split(":")
    inv = get_merch_inv()
    sizes = inv.get(mk, {}).get(ck, {}).get("sizes", {})
    kb = types.InlineKeyboardMarkup(row_width=3)
    for sz, q in sizes.items():
        if q > 0:
            kb.add(types.InlineKeyboardButton(f"{sz}", callback_data=f"order:s:{mk}:{ck}:{sz}"))
    ORD[c.message.chat.id].update({"color": ck})
    bot.edit_message_text("Выберите размер:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:s:"))
def order_choose_size(c: types.CallbackQuery):
    _, _, mk, ck, sz = c.data.split(":")
    ORD[c.message.chat.id].update({"size": sz})
    # спросим: нужен текст и/или номер?
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Текст", callback_data=f"order:text:{mk}:{ck}:{sz}"),
           types.InlineKeyboardButton("Номер", callback_data=f"order:number:{mk}:{ck}:{sz}"))
    kb.add(types.InlineKeyboardButton("Без текста/номера", callback_data=f"order:skiptn:{mk}:{ck}:{sz}"))
    bot.edit_message_text("Добавить надпись и/или номер?", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:text:"))
def order_text_choose_color(c: types.CallbackQuery):
    _, _, mk, ck, sz = c.data.split(":")
    s = get_settings()
    tcolors = s.get("text_colors", {}).get(mk, {}).get(ck, [])
    if not tcolors:
        bot.answer_callback_query(c.id, "Нет допустимых цветов текста для этого цвета мерча.", show_alert=True)
        return
    kb = types.InlineKeyboardMarkup(row_width=3)
    for tc in tcolors:
        kb.add(types.InlineKeyboardButton(tc, callback_data=f"order:textc:{mk}:{ck}:{sz}:{tc}"))
    bot.edit_message_text("Выберите цвет текста:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:textc:"))
def order_text_input(c: types.CallbackQuery):
    _, _, mk, ck, sz, tc = c.data.split(":")
    chat_id = c.message.chat.id
    ORD[chat_id]["text_color"] = tc
    bot.edit_message_text("Введите текст (только буквы выбранных алфавитов и пробелы):", chat_id, c.message.message_id)
    ORD[chat_id]["step"] = "text_wait"

@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "text_wait")
def order_text_set(m: types.Message):
    ok, msg = validate_text(m.text.strip())
    if not ok:
        bot.reply_to(m, "⚠️ " + msg); return
    ORD[m.chat.id]["text"] = m.text.strip()
    ORD[m.chat.id].pop("step", None)
    bot.reply_to(m, "Текст принят. Использовать номер? /number или /skip")

@bot.message_handler(commands=["number"])
def cmd_number(m: types.Message):
    chat_id = m.chat.id
    if chat_id not in ORD: return
    s = get_settings()
    mk = ORD[chat_id]["merch"]; ck = ORD[chat_id]["color"]
    tcolors = s.get("text_colors", {}).get(mk, {}).get(ck, [])
    if not tcolors:
        bot.reply_to(m, "Для выбранного цвета мерча нет допустимых цветов цифр."); return
    kb = types.InlineKeyboardMarkup(row_width=3)
    for tc in tcolors:
        kb.add(types.InlineKeyboardButton(tc, callback_data=f"order:numc:{mk}:{ck}:{ORD[chat_id]['size']}:{tc}"))
    bot.send_message(chat_id, "Выберите цвет цифр:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:number:"))
def order_number_choose_color(c: types.CallbackQuery):
    _, _, mk, ck, sz = c.data.split(":")
    s = get_settings()
    tcolors = s.get("text_colors", {}).get(mk, {}).get(ck, [])
    kb = types.InlineKeyboardMarkup(row_width=3)
    for tc in tcolors:
        kb.add(types.InlineKeyboardButton(tc, callback_data=f"order:numc:{mk}:{ck}:{sz}:{tc}"))
    bot.edit_message_text("Выберите цвет цифр:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:numc:"))
def order_number_input(c: types.CallbackQuery):
    _, _, mk, ck, sz, tc = c.data.split(":")
    chat_id = c.message.chat.id
    ORD[chat_id]["number_color"] = tc
    bot.edit_message_text("Введите номер (0..N):", chat_id, c.message.message_id)
    ORD[chat_id]["step"] = "number_wait"

@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "number_wait")
def order_number_set(m: types.Message):
    ok, msg = validate_number(m.text.strip())
    if not ok:
        bot.reply_to(m, "⚠️ " + msg); return
    ORD[m.chat.id]["number"] = m.text.strip()
    ORD[m.chat.id].pop("step", None)
    _prompt_templates(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:skiptn:"))
def order_skip_text_number(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ORD[chat_id]["text"] = "Без текста"
    ORD[chat_id]["number"] = "Без номера"
    bot.edit_message_text("Перейдём к выбору макетов.", chat_id, c.message.message_id)
    _prompt_templates(chat_id)

def _prompt_templates(chat_id: int):
    s = get_settings(); invt = get_templates_inv()
    mk = ORD[chat_id]["merch"]; ck = ORD[chat_id]["color"]
    tmpl_def = s.get("templates", {}).get(mk, {})
    tpls = tmpl_def.get("templates", {})
    avail = []
    for num, meta in tpls.items():
        if ck in meta.get("allowed_colors", []):
            qty = invt.get(mk, {}).get("templates", {}).get(num, {}).get("qty", 0)
            if qty > 0:
                avail.append(num)
    if tmpl_def.get("collages"):
        for fid in tmpl_def["collages"][:5]:
            try: bot.send_photo(chat_id, fid)
            except Exception: pass
    if not avail:
        _prompt_comment_phone(chat_id)
        return
    kb = types.InlineKeyboardMarkup(row_width=4)
    for n in sorted(avail):
        kb.add(types.InlineKeyboardButton(n, callback_data=f"order:tpl:{n}"))
    kb.add(types.InlineKeyboardButton("Готово", callback_data="order:tpl_done"),
           types.InlineKeyboardButton("Без макета", callback_data="order:tpl_none"))
    bot.send_message(chat_id, "Выберите номера макетов (можно несколько):", reply_markup=kb)
    ORD[chat_id]["selected_tpls"] = []

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:tpl"))
def order_tpl_cb(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    if c.data == "order:tpl_none":
        ORD[chat_id]["templates"] = "Без макета"
        bot.answer_callback_query(c.id, "Без макета")
        _prompt_comment_phone(chat_id)
        return
    if c.data == "order:tpl_done":
        ORD[chat_id]["templates"] = ", ".join(sorted(set(ORD[chat_id].get("selected_tpls", [])))) or "Без макета"
        _prompt_comment_phone(chat_id)
        return
    n = c.data.split(":")[2]
    lst = ORD[chat_id].setdefault("selected_tpls", [])
    if n in lst:
        lst.remove(n); bot.answer_callback_query(c.id, f"Убрано: {n}")
    else:
        lst.append(n); bot.answer_callback_query(c.id, f"Добавлено: {n}")

def _prompt_comment_phone(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Пропустить", callback_data="order:skip_comment"))
    bot.send_message(chat_id, "Добавить комментарий к заказу?", reply_markup=kb)
    ORD[chat_id]["step"] = "comment_wait"

@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "comment_wait")
def order_comment_set(m: types.Message):
    ORD[m.chat.id]["comment"] = m.text.strip()
    ORD[m.chat.id].pop("step", None)
    _prompt_phone(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "order:skip_comment")
def order_skip_comment(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ORD[chat_id]["comment"] = ""
    bot.answer_callback_query(c.id)
    _prompt_phone(chat_id)

def _prompt_phone(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Пропустить", callback_data="order:skip_phone"))
    bot.send_message(chat_id, "Введите номер телефона (или пропустите):", reply_markup=kb)
    ORD[chat_id]["step"] = "phone_wait"

@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "phone_wait")
def order_phone_set(m: types.Message):
    ORD[m.chat.id]["phone"] = m.text.strip()
    ORD[m.chat.id].pop("step", None)
    _show_summary(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "order:skip_phone")
def order_skip_phone(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ORD[chat_id]["phone"] = ""
    bot.answer_callback_query(c.id)
    _show_summary(chat_id)

def _show_summary(chat_id: int):
    s = get_settings(); invm = get_merch_inv()
    d = ORD[chat_id]
    merch_name = s["merch"][d["merch"]]["name_ru"]
    color_name = s["merch"][d["merch"]]["colors"][d["color"]]["name_ru"]
    lines = [
        "<b>Информация о заказе:</b>",
        f"Мерч: {html.escape(merch_name)}",
        f"Цвет: {html.escape(color_name)}",
        f"Размер: {html.escape(d['size'])}",
        f"Текст: {html.escape(d.get('text','Без текста'))} ({html.escape(d.get('text_color','-'))})",
        f"Номер: {html.escape(d.get('number','Без номера'))} ({html.escape(d.get('number_color','-'))})",
        f"Макеты: {html.escape(d.get('templates','Без макета'))}",
    ]
    if d.get("phone"):
        lines.append(f"Телефон: {html.escape(d['phone'])}")
    if d.get("comment"):
        lines.append(f"Комментарий: {html.escape(d['comment'])}")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Отправить в печать ✅", callback_data="order:confirm_yes"),
           types.InlineKeyboardButton("Отмена", callback_data="order:confirm_no"))
    bot.send_message(chat_id, "\n".join(lines), reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "order:confirm_no")
def order_confirm_no(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    bot.edit_message_text("🛑 Заказ отменён. /start — начать заново.", chat_id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "order:confirm_yes")
def order_confirm_yes(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    d = ORD.get(chat_id, {})
    s = get_settings()
    merch_name = s["merch"][d["merch"]]["name_ru"]
    color_name = s["merch"][d["merch"]]["colors"][d["color"]]["name_ru"]

    final_text = (
        f"✉️ <b>Заказ</b>\n"
        "---------------------------\n"
        f"🛍 Мерч: {html.escape(merch_name)}\n"
        f"🎨 Цвет: {html.escape(color_name)}\n"
        f"📐 Размер: {html.escape(d['size'])}\n"
        f"📝 Текст: {html.escape(d.get('text','Без текста'))} ({html.escape(d.get('text_color','-'))})\n"
        f"🔢 Номер: {html.escape(d.get('number','Без номера'))} ({html.escape(d.get('number_color','-'))})\n"
        f"🖼 Макеты: {html.escape(d.get('templates','Без макета'))}\n"
    )
    if d.get("comment"):
        final_text += f"❗️ Комментарий: {html.escape(d['comment'])}\n"
    if d.get("phone"):
        final_text += f"📞 Телефон: {html.escape(d['phone'])}\n"

    # Списание остатков
    dec_size(d["merch"], d["color"], d["size"], 1)
    if d.get("text") and d["text"] != "Без текста":
        dec_letter(d.get("text_color",""), d["text"])
    if d.get("number") and d["number"] != "Без номера":
        dec_number(d.get("number_color",""), d["number"])
    if d.get("templates") and d["templates"] != "Без макета":
        for num in d["templates"].split(","):
            dec_template(d["merch"], num.strip())

    bot.edit_message_text(final_text, chat_id, c.message.message_id, parse_mode="HTML")
    _send_to_admin_or_warn(chat_id, final_text)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Сделать новый заказ", callback_data="order:start"))
    bot.send_message(chat_id, "✅ Заказ оформлен!", reply_markup=kb)
