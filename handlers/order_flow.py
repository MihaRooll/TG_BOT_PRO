# -*- coding: utf-8 -*-
import html
from telebot import types
from telebot.apihelper import ApiTelegramException
from bot import bot
import config
from services.settings import get_settings, get_admin_bind
from services.orders import next_order_no
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

def _prompt_merch(chat_id: int):
    s = get_settings()
    inv = get_merch_inv()
    avail = []
    for mk, info in s.get("merch", {}).items():
        colors = s.get("merch", {}).get(mk, {}).get("colors", {})
        for ck in colors:
            sizes = inv.get(mk, {}).get(ck, {}).get("sizes", {})
            if any(q > 0 for q in sizes.values()):
                avail.append((mk, info))
                break
    mid = ORD[chat_id]["mid"]
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


@bot.callback_query_handler(func=lambda c: c.data == "order:start")
def order_start(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    mid = c.message.message_id
    s = get_settings()
    if not s.get("configured"):
        bot.answer_callback_query(c.id)
        bot.send_message(chat_id, "Бот не настроен. Нажмите /start и пройдите мастер.")
        return
    ORD[chat_id] = {"mid": mid}
    _prompt_merch(chat_id)


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
    letters_inv = get_letters_inv()
    counts = {}
    for ch in ORD[chat_id]["text"].replace(" ", "").upper():
        counts[ch] = counts.get(ch, 0) + 1
    miss = {ch: cnt for ch, cnt in counts.items()
            if letters_inv.get(tc, {}).get("letters", {}).get(ch, 0) < cnt}
    if miss:
        msg_lines = ["⚠️ Недостаточно символов:"]
        msg_lines.append("• Буквы: " + ", ".join(f"{k} ×{v}" for k, v in miss.items()))
        safe_edit_message(bot, chat_id, ORD[chat_id]["mid"], "\n".join(msg_lines))
        _prompt_text(chat_id)
        return
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
    ORD.setdefault(chat_id, {})["number"] = "Без номера (-)"
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
    numbers_inv = get_numbers_inv()
    counts = {}
    for dg in ORD[chat_id]["number"]:
        counts[dg] = counts.get(dg, 0) + 1
    miss = {dg: cnt for dg, cnt in counts.items()
            if numbers_inv.get(tc, {}).get("numbers", {}).get(dg, 0) < cnt}
    if miss:
        msg_lines = ["⚠️ Недостаточно символов:"]
        msg_lines.append("• Цифры: " + ", ".join(f"{k} ×{v}" for k, v in miss.items()))
        safe_edit_message(bot, chat_id, ORD[chat_id]["mid"], "\n".join(msg_lines))
        _prompt_number(chat_id)
        return
    _prompt_templates(chat_id)

def _render_tpl_step(chat_id: int):
    avail = ORD[chat_id]["avail_tpls"]
    sel = ORD[chat_id].get("selected_tpls", [])
    limit = ORD[chat_id].get("tpl_limit", len(avail))
    kb = types.InlineKeyboardMarkup(row_width=4)
    for n in sorted(avail):
        label = f"🟩 {n}" if n in sel else n
        kb.add(types.InlineKeyboardButton(label, callback_data=f"order:tpl:{n}"))
    kb.add(types.InlineKeyboardButton("Дальше", callback_data="order:tpl_done"))
    kb.add(types.InlineKeyboardButton("Очистить выбор макетов", callback_data="order:tpl_clear"))
    joined = "·".join(sorted(sel)) if sel else "—"
    text = f"🖼 Макеты ({len(sel)}/{limit}): {joined}"
    safe_edit_message(bot, chat_id, ORD[chat_id]["mid"], text, kb)


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
    # remove old summary
    safe_delete(bot, chat_id, ORD[chat_id]["mid"])
    # send collages above summary
    img_ids = []
    colls = tmpl_def.get("collages", [])
    if colls:
        media = [types.InputMediaPhoto(fid) for fid in colls[:5]]
        try:
            if len(media) > 1:
                msgs = bot.send_media_group(chat_id, media)
            else:
                msgs = [bot.send_photo(chat_id, media[0].media)]
            img_ids = [m.message_id for m in msgs]
        except Exception:
            pass
    ORD[chat_id]["tpl_img_ids"] = img_ids
    if not avail:
        msg = bot.send_message(chat_id, "Доступных макетов нет.")
        ORD[chat_id]["mid"] = msg.message_id
        _prompt_comment_phone(chat_id)
        return
    if len(avail) == 1:
        ORD[chat_id]["templates"] = avail[0]
        msg = bot.send_message(chat_id, f"Выбран автоматически: {avail[0]} (других вариантов нет)")
        ORD[chat_id]["mid"] = msg.message_id
        _prompt_comment_phone(chat_id)
        return
    msg = bot.send_message(chat_id, "...")
    ORD[chat_id]["mid"] = msg.message_id
    ORD[chat_id]["avail_tpls"] = avail
    ORD[chat_id]["selected_tpls"] = []
    ORD[chat_id]["tpl_limit"] = tmpl_def.get("limit", len(avail))
    _render_tpl_step(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order:tpl"))
def order_tpl_cb(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    if c.data == "order:tpl_done":
        ORD[chat_id]["templates"] = ", ".join(sorted(set(ORD[chat_id].get("selected_tpls", [])))) or "Без макета"
        _prompt_comment_phone(chat_id)
        return
    if c.data == "order:tpl_clear":
        ORD[chat_id]["selected_tpls"] = []
        bot.answer_callback_query(c.id, "Очищено")
        _render_tpl_step(chat_id)
        return
    n = c.data.split(":")[2]
    lst = ORD[chat_id].setdefault("selected_tpls", [])
    if n in lst:
        lst.remove(n); bot.answer_callback_query(c.id, f"Убрано: {n}")
    else:
        lim = ORD[chat_id].get("tpl_limit", len(ORD[chat_id].get("avail_tpls", [])))
        if len(lst) < lim:
            lst.append(n); bot.answer_callback_query(c.id, f"Добавлено: {n}")
        else:
            bot.answer_callback_query(c.id, "Достигнут лимит")
    _render_tpl_step(chat_id)

def _prompt_comment_phone(chat_id: int):
    for mid_old in ORD[chat_id].pop("tpl_img_ids", []):
        safe_delete(bot, chat_id, mid_old)
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

def _final_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="order:final"))
    kb.add(types.InlineKeyboardButton("✍️ Редактировать", callback_data="order:edit"))
    kb.add(types.InlineKeyboardButton("⛔️ Отменить", callback_data="order:confirm_no"))
    return kb


def _build_summary(d: dict, deficits: dict | None = None) -> str:
    s = get_settings()
    merch_name = s["merch"][d["merch"]]["name_ru"]
    color_name = s["merch"][d["merch"]]["colors"][d["color"]]["name_ru"]
    lines = ["Информация о заказе:"]
    line = f"Мерч: {merch_name}"
    if deficits and deficits.get("merch"):
        line += f" ⚠️ {deficits['merch']}"
    lines.append(line)
    line = f"Цвет: {color_name}"
    if deficits and deficits.get("color"):
        line += f" ⚠️ {deficits['color']}"
    lines.append(line)
    line = f"Размер: {d['size']}"
    if deficits and deficits.get("size"):
        line += f" ⚠️ {deficits['size']}"
    lines.append(line)
    text_val = d.get("text") or "Без текста (-)"
    line = f"Текст: {text_val}"
    if deficits and deficits.get("letters"):
        miss = ", ".join(deficits["letters"])
        word = "закончилась буква" if len(deficits["letters"]) == 1 else "закончились буквы"
        line += f" ⚠️ {word}: {miss}"
    lines.append(line)
    num_val = d.get("number") or "Без номера (-)"
    line = f"Номер: {num_val}"
    if deficits and deficits.get("digits"):
        miss = ", ".join(deficits["digits"])
        word = "закончилась цифра" if len(deficits["digits"]) == 1 else "закончились цифры"
        line += f" ⚠️ {word}: {miss}"
    lines.append(line)
    tpl_val = d.get("templates") or "Без макета"
    line = f"Макеты: {tpl_val}"
    if deficits and deficits.get("templates"):
        miss = ", ".join(deficits["templates"])
        word = "закончился макет" if len(deficits["templates"]) == 1 else "закончились макеты"
        line += f" ⚠️ {word}: {miss}"
    lines.append(line)
    if d.get("phone"):
        lines.append(f"Телефон: {d['phone']}")
    if d.get("comment"):
        lines.append(f"Комментарий: {d['comment']}")
    return "\n".join(lines)


def _show_summary(chat_id: int, deficits: dict | None = None):
    d = ORD[chat_id]
    mid = d["mid"]
    text = _build_summary(d, deficits)
    safe_edit_message(bot, chat_id, mid, text, _final_kb())


@bot.callback_query_handler(func=lambda c: c.data == "order:edit")
def order_edit_menu(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("Изменить мерч", callback_data="order:edit:merch"))
    kb.add(types.InlineKeyboardButton("Изменить цвет мерча", callback_data="order:edit:color"))
    kb.add(types.InlineKeyboardButton("Изменить размер", callback_data="order:edit:size"))
    kb.add(types.InlineKeyboardButton("Изменить текст", callback_data="order:edit:text"))
    kb.add(types.InlineKeyboardButton("Изменить цвет текста", callback_data="order:edit:textc"))
    kb.add(types.InlineKeyboardButton("Изменить номер", callback_data="order:edit:number"))
    kb.add(types.InlineKeyboardButton("Изменить цвет цифр", callback_data="order:edit:numberc"))
    kb.add(types.InlineKeyboardButton("Изменить макеты", callback_data="order:edit:tpl"))
    kb.add(types.InlineKeyboardButton("Очистить макеты", callback_data="order:edit:tplclear"))
    kb.add(types.InlineKeyboardButton("Вернуться к подтверждению", callback_data="order:edit:back"))
    kb.add(types.InlineKeyboardButton("Отменить заказ", callback_data="order:confirm_no"))
    safe_edit_message(bot, chat_id, ORD[chat_id]["mid"], "Редактирование заказа", kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("order:edit:"))
def order_edit_action(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    action = c.data.split(":")[2]
    d = ORD.setdefault(chat_id, {})
    if action == "merch":
        for key in ["merch", "color", "size", "text", "text_color", "number", "number_color", "templates"]:
            d.pop(key, None)
        _prompt_merch(chat_id)
    elif action == "color":
        for key in ["color", "size", "text", "text_color", "number", "number_color", "templates"]:
            d.pop(key, None)
        _prompt_colors(chat_id, d.get("merch"))
    elif action == "size":
        for key in ["size", "text", "text_color", "number", "number_color", "templates"]:
            d.pop(key, None)
        _prompt_sizes(chat_id, d.get("merch"), d.get("color"))
    elif action == "text":
        for key in ["text", "text_color", "number", "number_color", "templates"]:
            d.pop(key, None)
        _prompt_text(chat_id)
    elif action == "textc":
        d.pop("text_color", None)
        _prompt_text_color(chat_id)
    elif action == "number":
        for key in ["number", "number_color", "templates"]:
            d.pop(key, None)
        _prompt_number(chat_id)
    elif action == "numberc":
        d.pop("number_color", None)
        _prompt_number_color(chat_id)
    elif action == "tpl":
        d.pop("templates", None)
        _prompt_templates(chat_id)
    elif action == "tplclear":
        d["templates"] = "Без макета"
        _prompt_templates(chat_id)
    elif action == "back":
        _show_summary(chat_id)

@bot.callback_query_handler(func=lambda c: c.data == "order:confirm_no")
def order_confirm_no(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    mid = ORD.get(chat_id, {}).get("mid", c.message.message_id)
    safe_edit_message(bot, chat_id, mid, "🛑 Заказ отменён. /start — начать заново.")
    ORD.pop(chat_id, None)

def _check_deficits(d: dict) -> dict:
    deficits = {}
    inv = get_merch_inv()
    size_q = inv.get(d["merch"], {}).get(d["color"], {}).get("sizes", {}).get(d["size"], 0)
    if size_q <= 0:
        deficits["size"] = f"закончился {d['size']}"
        color_sizes = inv.get(d["merch"], {}).get(d["color"], {}).get("sizes", {})
        if not any(q > 0 for q in color_sizes.values()):
            deficits["color"] = f"закончился цвет: {get_settings()['merch'][d['merch']]['colors'][d['color']]['name_ru']}"
        merch_colors = inv.get(d["merch"], {})
        if not any(any(q > 0 for q in merch_colors.get(ck, {}).get("sizes", {}).values()) for ck in merch_colors):
            deficits["merch"] = f"закончился мерч: {get_settings()['merch'][d['merch']]['name_ru']}"
    letters_inv = get_letters_inv()
    if d.get("text") and d["text"] != "Без текста (-)":
        counts = {}
        for ch in d["text"].replace(" ", "").upper():
            counts[ch] = counts.get(ch, 0) + 1
        miss = [ch for ch, cnt in counts.items()
                if letters_inv.get(d.get("text_color"), {}).get("letters", {}).get(ch, 0) < cnt]
        if miss:
            deficits["letters"] = sorted(set(miss))
    numbers_inv = get_numbers_inv()
    if d.get("number") and d["number"] != "Без номера (-)":
        counts = {}
        for ch in d["number"]:
            counts[ch] = counts.get(ch, 0) + 1
        miss = [ch for ch, cnt in counts.items()
                if numbers_inv.get(d.get("number_color"), {}).get("numbers", {}).get(ch, 0) < cnt]
        if miss:
            deficits["digits"] = sorted(set(miss))
    tpl_inv = get_templates_inv()
    if d.get("templates") and d["templates"] != "Без макета":
        miss = []
        for num in d["templates"].split(","):
            q = tpl_inv.get(d["merch"], {}).get("templates", {}).get(num.strip(), {}).get("qty", 0)
            if q <= 0:
                miss.append(num.strip())
        if miss:
            deficits["templates"] = sorted(set(miss))
    return deficits


@bot.callback_query_handler(func=lambda c: c.data == "order:final")
def order_finalize(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    d = ORD.get(chat_id, {})
    deficits = _check_deficits(d)
    if deficits:
        _show_summary(chat_id, deficits)
        return
    s = get_settings()
    merch_name = s["merch"][d["merch"]]["name_ru"]
    color_name = s["merch"][d["merch"]]["colors"][d["color"]]["name_ru"]
    order_no = next_order_no()
    username = bot.get_me().username
    text_val = d.get("text")
    if text_val in (None, "Без текста (-)"):
        text_val = ""
    number_val = d.get("number")
    if number_val in (None, "Без номера (-)"):
        number_val = ""
    text_color = color_name_ru(d.get("text_color", "-"))
    number_color = color_name_ru(d.get("number_color", "-"))
    tpl_disp = (
        "·".join(d.get("templates", "").replace(",", " ").split())
        if d.get("templates") and d["templates"] != "Без макета"
        else "—"
    )
    phone = d.get("phone") or ""
    comment = d.get("comment") or ""

    parts = [
        f"🚀<a href=\"tg://user?id={chat_id}\">🛒</a> <b>ВАШ ЗАКАЗ #{order_no}</b> "
        f"<a href=\"https://t.me/{username}\">🤖</a>🌟",
        f"🛍 {html.escape(merch_name)} | Цвет: {html.escape(color_name)} | {html.escape(d['size'])}",
    ]

    if text_val or number_val:
        if text_val and number_val:
            color_disp = text_color if text_color == number_color else f"{text_color}/{number_color}"
            parts.append(
                f"📝 {html.escape(text_val)} | {html.escape(number_val)} | Цвет: {html.escape(color_disp)}"
            )
        elif text_val:
            parts.append(
                f"📝 {html.escape(text_val)} | Цвет: {html.escape(text_color)}"
            )
        elif number_val:
            parts.append(
                f"📝 {html.escape(number_val)} | Цвет: {html.escape(number_color)}"
            )

    parts.append(f"🖼 Макеты: {html.escape(tpl_disp)}")
    if phone:
        parts.append(f"📞 {html.escape(phone)}")
    if comment:
        parts.append(f"💬 ❗{html.escape(comment)}❗")

    final_text = "\n".join(parts)

    # Списание остатков
    dec_size(d["merch"], d["color"], d["size"], 1)
    if d.get("text") and d["text"] not in (None, "Без текста (-)"):
        dec_letter(d.get("text_color", ""), d["text"])
    if d.get("number") and d["number"] not in (None, "Без номера (-)"):
        dec_number(d.get("number_color", ""), d["number"])
    if d.get("templates") and d["templates"] != "Без макета":
        for num in d["templates"].split(","):
            dec_template(d["merch"], num.strip())

    mid = ORD.get(chat_id, {}).get("mid", c.message.message_id)
    safe_edit_message(bot, chat_id, mid, final_text, parse_mode="HTML")
    _send_to_admin_or_warn(chat_id, final_text)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Сделать новый заказ", callback_data="order:start"))
    bot.send_message(chat_id, "✅ Заказ оформлен!", reply_markup=kb)
    ORD.pop(chat_id, None)
