\
# -*- coding: utf-8 -*-
from telebot import types
from .core import WIZ, edit
import html

def render_letters_hub(chat_id: int):
    d = WIZ[chat_id]["data"]
    feats = d.setdefault("features", {"letters": True, "numbers": True})
    rules = d.setdefault("text_rules", {"allow_latin": True, "allow_cyrillic": False, "allow_space": True, "max_text_len": 12, "max_number": 99})
    pal   = d.setdefault("text_palette", ["white","black"])

    letters_status = "ВКЛЮЧЕНЫ ✅" if feats.get('letters') else "ВЫКЛЮЧЕНЫ ❌"
    numbers_status = "ВКЛЮЧЕНЫ ✅" if feats.get('numbers') else "ВЫКЛЮЧЕНЫ ❌"
    alphabet_line = (("Латиница" if rules.get('allow_latin') else "") + (" / " if rules.get('allow_latin') and rules.get('allow_cyrillic') else "") + ("Кириллица" if rules.get('allow_cyrillic') else "")) or "—"
    space_line    = "Разрешен ✔️" if rules.get('allow_space') else "Запрещен ✖️"

    lines = [
        "✨ Буквы",
        f"   ├─ Статус: {letters_status}",
        f"   ├─ Алфавит: {alphabet_line} ▸ ",
        f"   ├─ Пробел: {space_line}",
        f"   └─ Макс. длина: ≤{rules.get('max_text_len','—')} симв",
        "",
        "✨ Цифры",
        f"   ├─ Статус: {numbers_status}",
        f"   └─ Макс. номер: ≤{rules.get('max_number','—')}",
        "",
        "🎨 Палитра цветов текста",
        f"   └─ {', '.join(pal) if pal else '—'}",
    ]
    body = html.escape("\n".join(lines))
    text = "<b>🔤 ШАГ 2/4: НАСТРОЙКА БУКВ И ЦИФР 🔢</b>\n\n<pre><code>" + body + "</code></pre>"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(f"Буквы: {'вкл' if feats.get('letters') else 'выкл'}", callback_data="setup:feature_toggle:letters"),
            types.InlineKeyboardButton(f"Цифры: {'вкл' if feats.get('numbers') else 'выкл'}", callback_data="setup:feature_toggle:numbers"))
    kb.add(types.InlineKeyboardButton(f"Латиница: {'да' if rules.get('allow_latin') else 'нет'}", callback_data="setup:rule_toggle:allow_latin"),
            types.InlineKeyboardButton(f"Кириллица: {'да' if rules.get('allow_cyrillic') else 'нет'}", callback_data="setup:rule_toggle:allow_cyrillic"))
    kb.add(types.InlineKeyboardButton(f"Пробел: {'да' if rules.get('allow_space') else 'нет'}", callback_data="setup:rule_toggle:allow_space"),
            types.InlineKeyboardButton("Пределы ✏️", callback_data="setup:limits"))
    kb.add(types.InlineKeyboardButton("Палитра цветов текста", callback_data="setup:palette"),
            types.InlineKeyboardButton("2.1) Соответствия →", callback_data="setup:map_text_colors"))
    kb.add(types.InlineKeyboardButton("🏠 Меню", callback_data="setup:home"))
    edit(chat_id, text, kb)
    WIZ[chat_id]["stage"] = "text_hub"

def render_limits_progress(chat_id: int):
    d = WIZ[chat_id]["data"].setdefault("text_rules", {"allow_latin": True, "allow_cyrillic": False, "allow_space": True, "max_text_len": 12, "max_number": 99})
    st = WIZ[chat_id]["data"].setdefault("_limits", {"len_ok": bool(d.get('max_text_len')), "num_ok": bool(d.get('max_number'))})
    lines = [
        "Пределы ✏️",
        f"1) Длина текста: {'☑' if st.get('len_ok') else '☐'}  (текущ.: {d.get('max_text_len', '—')})",
        f"2) Макс. номер:  {'☑' if st.get('num_ok') else '☐'}  (текущ.: {d.get('max_number', '—')})",
        "Выберите этап или укажите по порядку.",
    ]
    text = "<pre><code>" + html.escape("\n".join(lines)) + "</code></pre>"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("1) Ввести длину текста", callback_data="setup:limits_edit:text_len"),
            types.InlineKeyboardButton("2) Ввести макс. номер", callback_data="setup:limits_edit:max_num"))
    if st.get("len_ok") and st.get("num_ok"):
        kb.add(types.InlineKeyboardButton("Готово ☑", callback_data="setup:limits_done"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
    edit(chat_id, text, kb)
    WIZ[chat_id]["stage"] = "limits_progress"

def ask_limit_len(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:limits"))
    edit(chat_id, "<b>Пределы ✏️ — шаг 1/2.</b>\\nВведите <b>максимальную длину текста</b> (например, 12).", kb)
    WIZ[chat_id]["stage"] = "limits_len"

def ask_limit_num(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:limits"))
    edit(chat_id, "<b>Пределы ✏️ — шаг 2/2.</b>\\nВведите <b>максимальный номер</b> (например, 99).", kb)
    WIZ[chat_id]["stage"] = "limits_num"

def toggle_feature(chat_id: int, which: str):
    feats = WIZ[chat_id]["data"].setdefault("features", {"letters": True, "numbers": True})
    feats[which] = not feats.get(which, False)
    render_letters_hub(chat_id)

def toggle_rule(chat_id: int, rule: str):
    rules = WIZ[chat_id]["data"].setdefault("text_rules", {"allow_latin": True, "allow_cyrillic": False, "allow_space": True, "max_text_len": 12, "max_number": 99})
    rules[rule] = not rules.get(rule, False)
    render_letters_hub(chat_id)

def set_limit_len(chat_id: int, val: int):
    rules = WIZ[chat_id]["data"].setdefault("text_rules", {})
    rules["max_text_len"] = val
    WIZ[chat_id]["data"].setdefault("_limits", {})["len_ok"] = True
    render_limits_progress(chat_id)

def set_limit_num(chat_id: int, val: int):
    rules = WIZ[chat_id]["data"].setdefault("text_rules", {})
    rules["max_number"] = val
    WIZ[chat_id]["data"].setdefault("_limits", {})["num_ok"] = True
    render_limits_progress(chat_id)
