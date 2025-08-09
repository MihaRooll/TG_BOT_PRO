\
    # -*- coding: utf-8 -*-
    from telebot import types
    from .core import WIZ, edit, slugify

    DEFAULT_TEXT_PALETTE = ["white","black","gold","red","blue"]

    def render_palette(chat_id: int):
        pal = WIZ[chat_id]["data"].setdefault("text_palette", ["white","black"])
        kb = types.InlineKeyboardMarkup(row_width=3)
        for tc in DEFAULT_TEXT_PALETTE:
            mark = "✓" if tc in pal else "·"
            kb.add(types.InlineKeyboardButton(f"{tc} {mark}", callback_data=f"setup:pal_toggle:{tc}"))
        kb.add(types.InlineKeyboardButton("➕ Свой цвет текста", callback_data="setup:pal_add"))
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:letters"))
        edit(chat_id, "<b>Выберите цвета текста</b> (палитра для букв/цифр).", kb)
        WIZ[chat_id]["stage"] = "palette"

    def toggle_palette_color(chat_id: int, tc: str):
        pal = WIZ[chat_id]["data"].setdefault("text_palette", ["white","black"])
        if tc in pal: pal.remove(tc)
        else: pal.append(tc)
        render_palette(chat_id)

    def ask_custom_color(chat_id: int):
        WIZ[chat_id]["stage"] = "pal_add"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:palette"))
        edit(chat_id, "Введите <b>название</b> цвета текста (ключ создадим автоматически).", kb)

    def handle_custom_color(chat_id: int, text: str):
        pal = WIZ[chat_id]["data"].setdefault("text_palette", [])
        key = slugify(text.strip(), used=pal)
        if key not in pal:
            pal.append(key)
        render_palette(chat_id)
