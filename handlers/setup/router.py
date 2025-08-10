\
# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from .core import WIZ, ensure, edit

from . import A0_Overview as O
from . import A1_Merch    as M
from . import A2_Letters  as L
from . import A4_TextPalette as P
from . import A5_MapTextColors as MAP
from . import A6_TemplatesNumbers as TNUM
from . import A7_TemplatesColors  as TCOL
from . import A8_TemplatesCollages as TCOLL
from . import A9_InventorySizes   as INV

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("setup:"))
def setup_router(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ensure(chat_id, c.message.message_id)
    parts = c.data.split(":")
    cmd, *rest = parts[1:]

    if cmd == "init":         O.render_home(chat_id); return
    if cmd == "home":         O.render_home(chat_id); return
    if cmd == "bind_hint":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:home"))
        edit(chat_id, "<pre>📌 Привязка общего чата:\n1) Добавьте бота в нужную группу/канал (в канале — как администратора).\n2) Выполните там команду /bind_here.\nБот запомнит чат (и тему, если есть).</pre>", kb)
        return

    # --- Step 1: Merch ---
    if cmd == "merch":            M.render_types(chat_id); return
    if cmd == "merch_toggle":     M.toggle_type(chat_id, rest[0]); return
    if cmd == "merch_add":        M.ask_custom(chat_id); return
    if cmd == "colors_sizes":     M.start_colors_iter(chat_id); return
    if cmd == "colors":           M.render_colors(chat_id, rest[0]); return
    if cmd == "color_toggle":     M.toggle_color(chat_id, rest[0], rest[1]); return
    if cmd == "color_add":        M.ask_custom_color(chat_id, rest[0]); return
    if cmd == "sizes":            M.render_sizes(chat_id, rest[0]); return
    if cmd == "sizes_default":    M.set_default_sizes(chat_id, rest[0]); return
    if cmd == "sizes_one":        M.set_one_size(chat_id, rest[0]); return
    if cmd == "sizes_add":        M.ask_custom_sizes(chat_id, rest[0]); return
    if cmd == "next_merch_or_done": M.next_merch_or_done(chat_id); return

    # --- Step 2: Letters & limits ---
    if cmd in ("letters", "numbers"):  L.render_letters_hub(chat_id); return
    if cmd == "feature_toggle":        L.toggle_feature(chat_id, rest[0]); return
    if cmd == "rule_toggle":           L.toggle_rule(chat_id, rest[0]); return
    if cmd == "limits":                L.render_limits_progress(chat_id); return
    if cmd == "limits_edit":
        which = rest[0]
        if which == "text_len": L.ask_limit_len(chat_id)
        else:                    L.ask_limit_num(chat_id)
        return
    if cmd == "limits_done":           L.render_letters_hub(chat_id); return
    if cmd == "palette":               P.render_palette(chat_id); return
    if cmd == "pal_toggle":            P.toggle_palette_color(chat_id, rest[0]); return
    if cmd == "pal_add":               P.ask_custom_color(chat_id); return

    # --- Step 2.1: Map text colors per merch/color ---
    if cmd == "map_text_colors":       MAP.render_next_pair(chat_id); return
    if cmd == "maptc_toggle":          MAP.toggle_map(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "maptc_next":            MAP.next_pair(chat_id); return

    # --- Step 3: Templates ---
    if cmd == "tmpls":
        kb = types.InlineKeyboardMarkup(row_width=1)
        d = WIZ[chat_id]["data"]
        for mk, mi in d.get("merch", {}).items():
            kb.add(types.InlineKeyboardButton(mi['name_ru'], callback_data=f"setup:tmpl_nums_for:{mk}"))
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:home"))
        edit(chat_id, "Шаг 3/4. Выберите вид мерча для ввода номеров макетов.", kb)
        WIZ[chat_id]["stage"] = "tmpls_pick"; return
    if cmd == "tmpl_nums_for":         TNUM.start_for_merch(chat_id, rest[0]); return
    if cmd == "tmpl_num_key":          TNUM.keypress(chat_id, rest[0]); return
    if cmd == "tmpl_num_back":         TNUM.backspace(chat_id); return
    if cmd == "tmpl_num_clear":        TNUM.clearbuf(chat_id); return
    if cmd == "tmpl_num_add":          TNUM.add_number(chat_id); return
    if cmd == "tmpl_num_done":         TNUM.done(chat_id); return
    if cmd == "tmpl_color_toggle":     TCOL.toggle_color(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "tmpl_color_next":       TCOL.next_template(chat_id, rest[0], rest[1]); return
    if cmd == "tmpl_collages_done":    TCOLL.collages_done(chat_id); return

    # --- Step 4: Inventory (sizes) ---
    if cmd == "inv":                    INV.open_inventory_sizes(chat_id); return
    if cmd == "inv_sizes_colors":       INV.open_colors(chat_id, rest[0]); return
    if cmd == "inv_sizes_sizes":        INV.open_sizes(chat_id, rest[0], rest[1]); return
    if cmd == "inv_sz_qty":             INV.open_qty_spinner(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "inv_sz_adj":             INV.adjust_qty(chat_id, rest[0], rest[1], rest[2], int(rest[3])); return
    if cmd == "inv_sz_set":             INV.set_qty(chat_id, rest[0], rest[1], rest[2], int(rest[3])); return
    if cmd == "inv_sz_save":            INV.save_qty(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "inv_sz_apply_all":       INV.apply_all_sizes(chat_id, rest[0], rest[1]); return
    if cmd == "inv_sz_all_set":         INV.set_all_sizes(chat_id, rest[0], rest[1], int(rest[2])); return

    # --- Finish ---
    if cmd == "finish":                 _finish(chat_id); return

def _finish(chat_id: int):
    tmp = WIZ[chat_id]["data"]
    from services.settings import get_settings, save_settings
    settings = get_settings()
    settings["configured"]   = True
    settings["merch"]        = tmp.get("merch", {})
    settings["features"]     = tmp.get("features", {"letters": True, "numbers": True})
    settings["text_rules"]   = tmp.get("text_rules", {"allow_latin": True, "allow_cyrillic": False, "allow_space": True, "max_text_len": 12, "max_number": 99})
    settings["text_palette"] = tmp.get("text_palette", ["white","black"])
    settings["text_colors"]  = tmp.get("text_colors", {})
    settings["templates"]    = tmp.get("templates", {})
    save_settings(settings)

    from services.inventory import save_merch_inv, save_letters_inv, save_numbers_inv, save_templates_inv
    save_merch_inv(tmp.get("_inv_merch", {}))
    save_letters_inv(tmp.get("_inv_letters", {}))
    save_numbers_inv(tmp.get("_inv_numbers", {}))
    save_templates_inv(tmp.get("_inv_tmpls", {}))

    edit(chat_id, "Готово! ☑ Бот настроен и готов к приёму заказов. Нажмите /start.", None)
    WIZ.pop(chat_id, None)

# ----------- удаляем пользовательские сообщения и обрабатываем ввод ----------
def _safe_del(mid_chat: int, mid: int):
    try:
        bot.delete_message(mid_chat, mid)
    except Exception:
        pass

@bot.message_handler(func=lambda m: m.chat.id in WIZ and True, content_types=["text","photo"])
def _during_setup(m: types.Message):
    chat_id = m.chat.id
    st = WIZ[chat_id].get("stage","")
    text = (m.text or "").strip() if m.content_type == "text" else ""
    # --- кастомные добавления (мерч/цвет/размеры/палитра) ---
    if st == "merch_add" and text:
        from .A1_Merch import handle_custom_input; handle_custom_input(chat_id, text)
    elif st.startswith("color_add:") and text:
        from .A1_Merch import handle_custom_color; mk = st.split(":")[1]; handle_custom_color(chat_id, mk, text)
    elif st.startswith("sizes_add:") and text:
        from .A1_Merch import handle_custom_sizes; mk = st.split(":")[1]; handle_custom_sizes(chat_id, mk, text)
    elif st == "pal_add" and text:
        from .A4_TextPalette import handle_custom_color; handle_custom_color(chat_id, text)
    # --- коллажи (фото) ---
    elif st.startswith("tmpl_collages:") and m.content_type == "photo":
        mk = st.split(":")[1]
        d = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})
        f_id = m.photo[-1].file_id
        col = d.setdefault("collages", [])
        if len(col) < 10: col.append(f_id)
    # --- лимиты по шагам ---
    elif st == "limits_len" and text:
        try:
            val = int(text); assert val > 0
            from .A2_Letters import set_limit_len; set_limit_len(chat_id, val)
        except Exception:
            from .A2_Letters import ask_limit_len; ask_limit_len(chat_id)
    elif st == "limits_num" and text:
        try:
            val = int(text); assert val >= 0
            from .A2_Letters import set_limit_num; set_limit_num(chat_id, val)
        except Exception:
            from .A2_Letters import ask_limit_num; ask_limit_num(chat_id)
    # --- удаляем любое пользовательское сообщение ---
    _safe_del(chat_id, m.message_id)
