# -*- coding: utf-8 -*-
import html
from telebot import types
from telebot.apihelper import ApiTelegramException
from bot import bot
import config
from services.settings import get_settings, get_admin_bind
from services.inventory import (
    get_merch_inv, get_letters_inv, get_numbers_inv, get_templates_inv,
    dec_size, dec_letter, dec_number, dec_template
)
from services.validators import validate_text, validate_number
from utils.tg import safe_delete, safe_edit_message, color_name_ru

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

@bot.callback_query_handler(func=lambda c: c.data == "order:start")
def order_start(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    mid = c.message.message_id
    s = get_settings()
    if not s.get("configured"):
        bot.answer_callback_query(c.id)
        bot.send_message(chat_id, "Бот не настроен. Нажмите /start и пройдите мастер.")
        return
    inv = get_merch_inv()
    avail = []
    for mk, info in s.get("merch", {}).items():
        colors = s.get("merch", {}).get(mk, {}).get("colors", {})
        for ck in colors:
            sizes = inv.get(mk, {}).get(ck, {}).get("sizes", {})
            if any(q > 0 for q in sizes.values()):
                avail.append((mk, info))
                break
    ORD[chat_id] = {"mid": mid}
    if not avail:
        safe_edit_message(bot, chat_id, mid, "Нет доступного мерча. Обновите остатки.")
        return
    if len(avail) == 1:
        mk, info = avail[0]
        ORD[chat_id]["merch"] = mk
        safe_edit_message(bot, chat_id, mid,
                          f"Выбран автоматически: {info.get('name_ru', mk)} (других вариантов нет)")
        _prompt_colors(chat_id, mk)
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for mk, info in avail:
        kb.add(types.InlineKeyboardButton(info.get("name_ru", mk), callback_data=f"order:m:{mk}"))
    safe_edit_message(bot, chat_id, mid, "Выберите вид мерча:", kb)


def _prompt_colors(chat_id: int, mk: str):
    s = get_settings()
    inv = get_merch_inv()
    colors = s.get("merch", {}).get(mk, {}).get("colors", {})
    avail = []
    for ck, info in colors.items():
        sizes = inv.get(mk, {}).get(ck, {}).get("sizes", {})
        if any(q > 0 for q in sizes.values()):
            avail.append((ck, info.get("name_ru", ck)))
    mid = ORD[chat_id]["mid"]
    if not avail:
        safe_edit_message(bot, chat_id, mid, "Нет доступных цветов. ⬅️ Назад")
        return
    if len(avail) == 1:
        ck, name = avail[0]
        ORD[chat_id]["color"] = ck
        safe_edit_message(bot, chat_id, mid,
                          f"Выбран автоматически: {name} (других вариантов нет)")
        _prompt_sizes(chat_id, mk, ck)
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for ck, name in avail:
        kb.add(types.InlineKeyboardButton(name, callback_data=f"order:c:{mk}:{ck}"))
    safe_edit_message(bot, chat_id, mid, "Выберите цвет:", kb)


def _prompt_sizes(chat_id: int, mk: str, ck: str):
    inv = get_merch_inv()
    sizes = inv.get(mk, {}).get(ck, {}).get("sizes", {})
    avail = [sz for sz, q in sizes.items() if q > 0]
    mid = ORD[chat_id]["mid"]
    if not avail:
        safe_edit_message(bot, chat_id, mid, "Нет доступных размеров. ⬅️ Назад")
        return
    if len(avail) == 1:
        sz = avail[0]
        ORD[chat_id]["size"] = sz
        safe_edit_message(bot, chat_id, mid,
                          f"Выбран автоматически: {sz} (других вариантов нет)")
        _after_size(chat_id)
        return
    kb = types.InlineKeyboardMarkup(row_width=3)
    for sz in avail:
        kb.add(types.InlineKeyboardButton(sz, callback_data=f"order:s:{mk}:{ck}:{sz}"))
    safe_edit_message(bot, chat_id, mid, "Выберите размер:", kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:m:"))
def order_choose_merch(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    mk = c.data.split(":")[2]
    ORD.setdefault(chat_id, {})["merch"] = mk
    _prompt_colors(chat_id, mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:c:"))
def order_choose_color(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    _, _, mk, ck = c.data.split(":")
    ORD.setdefault(chat_id, {})["color"] = ck
    _prompt_sizes(chat_id, mk, ck)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:s:"))
def order_choose_size(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    _, _, mk, ck, sz = c.data.split(":")
    ORD.setdefault(chat_id, {})["size"] = sz
    _after_size(chat_id)
    
def _after_size(chat_id: int):
    s = get_settings()
    feats = s.get("features", {})
    if feats.get("letters"):
        _prompt_text(chat_id)
    elif feats.get("numbers"):
        _prompt_number(chat_id)
    else:
        safe_edit_message(bot, chat_id, ORD[chat_id]["mid"], "Перейдём к выбору макетов.")
        _prompt_templates(chat_id)


def _prompt_text(chat_id: int):
    mid = ORD[chat_id]["mid"]
    safe_edit_message(bot, chat_id, mid, "Введите текст (только буквы выбранных алфавитов и пробелы):")
    ORD[chat_id]["step"] = "text_wait"


@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "text_wait")
def order_text_set(m: types.Message):
    chat_id = m.chat.id
    mid = ORD.get(chat_id, {}).get("mid")
    text = m.text.strip()
    ok, msg = validate_text(text)
    if not ok:
        safe_edit_message(bot, chat_id, mid, f"⚠️ {msg}\n\nВведите текст (только буквы выбранных алфавитов и пробелы):")
        safe_delete(bot, chat_id, m.message_id)
        return
    ORD[chat_id]["text"] = text
    ORD[chat_id].pop("step", None)
    safe_delete(bot, chat_id, m.message_id)
    _prompt_text_color(chat_id)


def _prompt_text_color(chat_id: int):
    s = get_settings()
    mk = ORD[chat_id]["merch"]
    ck = ORD[chat_id]["color"]
    tcolors = s.get("text_colors", {}).get(mk, {}).get(ck, [])
    inv = get_letters_inv()
    avail = []
    for tc in tcolors:
        if any(q > 0 for q in inv.get(tc, {}).get("letters", {}).values()):
            avail.append(tc)
    mid = ORD[chat_id]["mid"]
    if not avail:
        safe_edit_message(bot, chat_id, mid, "Нет доступных цветов текста.")
        _prompt_number(chat_id)
        return
    if len(avail) == 1:
        tc = avail[0]
        ORD[chat_id]["text_color"] = tc
        safe_edit_message(bot, chat_id, mid,
                          f"Выбран автоматически: {color_name_ru(tc)} (других вариантов нет)")
        _prompt_number(chat_id)
        return
    kb = types.InlineKeyboardMarkup(row_width=3)
    for tc in avail:
        kb.add(types.InlineKeyboardButton(color_name_ru(tc), callback_data=f"order:textc:{tc}"))
    safe_edit_message(bot, chat_id, mid, "Выберите цвет текста:", kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("order:textc:"))
def order_text_color_cb(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    tc = c.data.split(":")[2]
    ORD.setdefault(chat_id, {})["text_color"] = tc
    _prompt_number(chat_id)


def _prompt_number(chat_id: int):
    s = get_settings()
    if not s.get("features", {}).get("numbers"):
        _prompt_templates(chat_id)
        return
    mid = ORD[chat_id]["mid"]
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Без номера", callback_data="order:number_skip"))
    safe_edit_message(bot, chat_id, mid, "Введите номер (0..N):", kb)
    ORD[chat_id]["step"] = "number_wait"


@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "number_wait")
def order_number_set(m: types.Message):
    chat_id = m.chat.id
    mid = ORD.get(chat_id, {}).get("mid")
    num = m.text.strip()
    ok, msg = validate_number(num)
    if not ok:
        safe_edit_message(bot, chat_id, mid, f"⚠️ {msg}\n\nВведите номер (0..N):")
        safe_delete(bot, chat_id, m.message_id)
        return
    ORD[chat_id]["number"] = num
    ORD[chat_id].pop("step", None)
    safe_delete(bot, chat_id, m.message_id)
    _prompt_number_color(chat_id)


@bot.callback_query_handler(func=lambda c: c.data == "order:number_skip")
def order_number_skip(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ORD.setdefault(chat_id, {})["number"] = "Без номера"
    mid = ORD.get(chat_id, {}).get("mid", c.message.message_id)
    safe_edit_message(bot, chat_id, mid, "Перейдём к выбору макетов.")
    _prompt_templates(chat_id)


def _prompt_number_color(chat_id: int):
    s = get_settings()
    mk = ORD[chat_id]["merch"]; ck = ORD[chat_id]["color"]
    tcolors = s.get("text_colors", {}).get(mk, {}).get(ck, [])
    inv = get_numbers_inv()
    avail = []
    for tc in tcolors:
        if any(q > 0 for q in inv.get(tc, {}).get("numbers", {}).values()):
            avail.append(tc)
    mid = ORD[chat_id]["mid"]
    if not avail:
        _prompt_templates(chat_id)
        return
    if len(avail) == 1:
        tc = avail[0]
        ORD[chat_id]["number_color"] = tc
        safe_edit_message(bot, chat_id, mid,
                          f"Выбран автоматически: {color_name_ru(tc)} (других вариантов нет)")
        _prompt_templates(chat_id)
        return
    kb = types.InlineKeyboardMarkup(row_width=3)
    for tc in avail:
        kb.add(types.InlineKeyboardButton(color_name_ru(tc), callback_data=f"order:numc:{tc}"))
    safe_edit_message(bot, chat_id, mid, "Выберите цвет цифр:", kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("order:numc:"))
def order_number_color_cb(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    tc = c.data.split(":")[2]
    ORD.setdefault(chat_id, {})["number_color"] = tc
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
    mid = ORD[chat_id]["mid"]
    if not avail:
        safe_edit_message(bot, chat_id, mid, "Доступных макетов нет.")
        _prompt_comment_phone(chat_id)
        return
    if len(avail) == 1:
        ORD[chat_id]["templates"] = avail[0]
        safe_edit_message(bot, chat_id, mid,
                          f"Выбран автоматически: {avail[0]} (других вариантов нет)")
        _prompt_comment_phone(chat_id)
        return
    kb = types.InlineKeyboardMarkup(row_width=4)
    for n in sorted(avail):
        kb.add(types.InlineKeyboardButton(n, callback_data=f"order:tpl:{n}"))
    kb.add(types.InlineKeyboardButton("Готово", callback_data="order:tpl_done"),
           types.InlineKeyboardButton("Без макета", callback_data="order:tpl_none"))
    safe_edit_message(bot, chat_id, mid, "Выберите номера макетов (можно несколько):", kb)
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
    mid = ORD[chat_id]["mid"]
    safe_edit_message(bot, chat_id, mid, "Добавить комментарий к заказу?", kb)
    ORD[chat_id]["step"] = "comment_wait"

@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "comment_wait")
def order_comment_set(m: types.Message):
    chat_id = m.chat.id
    ORD[chat_id]["comment"] = m.text.strip()
    ORD[chat_id].pop("step", None)
    safe_delete(bot, chat_id, m.message_id)
    _prompt_phone(chat_id)

@bot.callback_query_handler(func=lambda c: c.data == "order:skip_comment")
def order_skip_comment(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ORD[chat_id]["comment"] = ""
    bot.answer_callback_query(c.id)
    _prompt_phone(chat_id)

def _prompt_phone(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Пропустить", callback_data="order:skip_phone"))
    mid = ORD[chat_id]["mid"]
    safe_edit_message(bot, chat_id, mid, "Введите номер телефона (или пропустите):", kb)
    ORD[chat_id]["step"] = "phone_wait"

@bot.message_handler(func=lambda m: ORD.get(m.chat.id, {}).get("step") == "phone_wait")
def order_phone_set(m: types.Message):
    chat_id = m.chat.id
    ORD[chat_id]["phone"] = m.text.strip()
    ORD[chat_id].pop("step", None)
    safe_delete(bot, chat_id, m.message_id)
    _show_summary(chat_id)

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
        f"Текст: {html.escape(d.get('text','Без текста'))} ({html.escape(color_name_ru(d.get('text_color','-')))})",
        f"Номер: {html.escape(d.get('number','Без номера'))} ({html.escape(color_name_ru(d.get('number_color','-')))})",
        f"Макеты: {html.escape(d.get('templates','Без макета'))}",
    ]
    if d.get("phone"):
        lines.append(f"Телефон: {html.escape(d['phone'])}")
    if d.get("comment"):
        lines.append(f"Комментарий: {html.escape(d['comment'])}")
    letters_inv = get_letters_inv(); numbers_inv = get_numbers_inv()
    miss_lt = []
    if d.get("text") and d["text"] != "Без текста":
        for ch in d["text"].replace(" ", "").upper():
            if letters_inv.get(d.get("text_color"), {}).get("letters", {}).get(ch, 0) <= 0:
                miss_lt.append(ch)
    miss_nb = []
    if d.get("number") and d["number"] != "Без номера":
        for digit in d["number"]:
            if numbers_inv.get(d.get("number_color"), {}).get("numbers", {}).get(digit, 0) <= 0:
                miss_nb.append(digit)
    if miss_lt:
        lines.append(f"⚠️ Не хватает букв: {', '.join(sorted(set(miss_lt)))}")
    if miss_nb:
        lines.append(f"⚠️ Не хватает цифр: {', '.join(sorted(set(miss_nb)))}")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Отправить в печать ✅", callback_data="order:confirm_yes"),
           types.InlineKeyboardButton("Отмена", callback_data="order:confirm_no"))
    mid = ORD[chat_id]["mid"]
    safe_edit_message(bot, chat_id, mid, "\n".join(lines), kb)

@bot.callback_query_handler(func=lambda c: c.data == "order:confirm_no")
def order_confirm_no(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    mid = ORD.get(chat_id, {}).get("mid", c.message.message_id)
    safe_edit_message(bot, chat_id, mid, "🛑 Заказ отменён. /start — начать заново.")
    ORD.pop(chat_id, None)

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
        f"📝 Текст: {html.escape(d.get('text','Без текста'))} ({html.escape(color_name_ru(d.get('text_color','-')))})\n"
        f"🔢 Номер: {html.escape(d.get('number','Без номера'))} ({html.escape(color_name_ru(d.get('number_color','-')))})\n"
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

    mid = ORD.get(chat_id, {}).get("mid", c.message.message_id)
    safe_edit_message(bot, chat_id, mid, final_text)
    _send_to_admin_or_warn(chat_id, final_text)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Сделать новый заказ", callback_data="order:start"))
    bot.send_message(chat_id, "✅ Заказ оформлен!", reply_markup=kb)
    ORD.pop(chat_id, None)
