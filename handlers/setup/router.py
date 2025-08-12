\
# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from .core import WIZ, ensure, edit, anchor

from . import A0_Overview as O
from . import A1_Merch    as M
from . import A2_Letters  as L
from . import A4_TextPalette as P
from . import A5_MapTextColors as MAP
from . import A6_TemplatesNumbers as TNUM
from . import A7_TemplatesColors  as TCOL
from . import A8_TemplatesCollages as TCOLL
from . import A9_InventorySizes   as INV
from services.settings import get_settings


def render_templates_home(chat_id: int) -> None:
    data = WIZ[chat_id]["data"]
    tmpl = data.get("templates", {})
    inv_tmpls = data.get("_inv_tmpls", {})
    def _pr(flag: bool) -> str:
        return "✅ — внесли" if flag else "— не внесли"
    has_nums = any(v.get("templates") for v in tmpl.values())
    has_colors = any(
        any(t.get("allowed_colors") for t in v.get("templates", {}).values())
        for v in tmpl.values()
    )
    has_qty = bool(inv_tmpls)
    has_imgs = any(v.get("collages") for v in tmpl.values())
    layouts = data.setdefault("layouts", get_settings().get("layouts", {"max_per_order":3,"selected_indicator":"🟩"}))
    max_per = layouts.get("max_per_order", 3)
    indicator = layouts.get("selected_indicator", "🟩")
    lines = [
        f"├─ Добавить номера макетов: {_pr(has_nums)}",
        f"├─ Настроить соответствие цветов: {_pr(has_colors)}",
        f"├─ Настроить количество: {_pr(has_qty)}",
        f"├─ Загрузить изображения с макетами: {_pr(has_imgs)}",
        f"├─ Ограничение макетов на заказ: {max_per}",
        f"└─ Смайлик выбранного макета: {indicator}",
    ]
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("Добавить номера макетов", callback_data="setup:tmpl_nums"))
    kb.add(types.InlineKeyboardButton("Настроить соответствие цветов", callback_data="setup:tmpl_map"))
    kb.add(types.InlineKeyboardButton("Настроить количество", callback_data="setup:tmpl_qty"))
    kb.add(types.InlineKeyboardButton("Загрузить изображения с макетами", callback_data="setup:tmpl_collages"))
    kb.add(types.InlineKeyboardButton("Ограничение макетов на заказ", callback_data="setup:tmpl_limit"))
    kb.add(types.InlineKeyboardButton("Смайлик выбранного макета", callback_data="setup:tmpl_indicator"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:home"))
    edit(chat_id, "🧩 Шаг 3/4 — Макеты\n" + "\n".join(lines), kb)
    WIZ[chat_id]["stage"] = "tmpls_home"

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("setup:"))
def setup_router(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    ensure(chat_id, c.message.message_id)
    if anchor(chat_id) != c.message.message_id:
        bot.answer_callback_query(c.id)
        return
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
    if cmd == "maptc_reset":           MAP.reset_map(chat_id, rest[0], rest[1]); return
    if cmd == "maptc_next":            MAP.next_pair(chat_id); return
    if cmd == "maptc_edit":            MAP.edit_all(chat_id); return

    # --- Step 3: Templates ---
    if cmd == "tmpls":                 render_templates_home(chat_id); return
    if cmd == "tmpl_nums":
        kb = types.InlineKeyboardMarkup(row_width=1)
        d = WIZ[chat_id]["data"]
        for mk, mi in d.get("merch", {}).items():
            kb.add(types.InlineKeyboardButton(mi['name_ru'], callback_data=f"setup:tmpl_nums_for:{mk}"))
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
        edit(chat_id, "Шаг 3/4. Выберите вид мерча для ввода номеров макетов.", kb)
        WIZ[chat_id]["stage"] = "tmpls_pick"; return
    if cmd == "tmpl_nums_for":         TNUM.start_for_merch(chat_id, rest[0]); return
    if cmd == "tmpl_num_done":         render_templates_home(chat_id); return
    if cmd == "tmpl_map":              TCOL.render_for_next_template(chat_id); return
    if cmd == "tmpl_color_toggle":     TCOL.toggle_color(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "tmpl_color_next":       TCOL.next_template(chat_id, rest[0], rest[1]); return
    if cmd == "tmpl_qty":              INV.open_inventory_templates(chat_id); return
    if cmd == "tmpl_collages":         TCOLL.ask_collages_or_next(chat_id); return
    if cmd == "tmpl_collages_done":    render_templates_home(chat_id); return
    if cmd == "tmpl_limit":
        cur = WIZ[chat_id]["data"].setdefault("layouts", get_settings().get("layouts", {})).get("max_per_order", 3)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
        edit(chat_id, f"Текущее ограничение макетов на заказ: {cur}\nВведите новое значение (≥1):", kb)
        WIZ[chat_id]["stage"] = "tmpl_limit"; return
    if cmd == "tmpl_indicator":
        cur = WIZ[chat_id]["data"].setdefault("layouts", get_settings().get("layouts", {})).get("selected_indicator", "🟩")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
        edit(chat_id, f"Текущий смайлик выбранного макета: {cur}\nПришлите новый символ:", kb)
        WIZ[chat_id]["stage"] = "tmpl_indicator"; return

    # --- Step 4: Inventory ---
    if cmd == "inv":                    INV.open_inventory_home(chat_id); return
    if cmd == "inv_merch":              INV.open_merch_list(chat_id); return
    if cmd == "inv_sizes_colors":       INV.open_colors(chat_id, rest[0]); return
    if cmd == "inv_sizes_sizes":        INV.open_sizes(chat_id, rest[0], rest[1]); return
    if cmd == "inv_sz_qty":             INV.open_qty_spinner(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "inv_sz_apply_all":       INV.apply_all_sizes(chat_id, rest[0], rest[1]); return
    if cmd == "inv_sz_adj":             INV.adjust_size_qty(chat_id, rest[0], rest[1], rest[2], int(rest[3])); return
    if cmd == "inv_sz_set":             INV.set_size_qty(chat_id, rest[0], rest[1], rest[2], int(rest[3])); return
    if cmd == "inv_sz_save":            INV.save_size_qty(chat_id, rest[0], rest[1], rest[2]); return
    if cmd == "inv_letters":            INV.open_inventory_letters(chat_id); return
    if cmd == "inv_letters_chars":      INV.open_letters_chars(chat_id, rest[0]); return
    if cmd == "inv_lt_qty":             INV.open_letter_qty_spinner(chat_id, rest[0], rest[1]); return
    if cmd == "inv_lt_adj":             INV.adjust_letter_qty(chat_id, rest[0], rest[1], int(rest[2])); return
    if cmd == "inv_lt_set":             INV.set_letter_qty(chat_id, rest[0], rest[1], int(rest[2])); return
    if cmd == "inv_lt_save":            INV.save_letter_qty(chat_id, rest[0], rest[1]); return
    if cmd == "inv_lt_apply_all":       INV.apply_all_letters(chat_id, rest[0]); return
    if cmd == "inv_numbers":            INV.open_inventory_numbers(chat_id); return
    if cmd == "inv_numbers_digits":     INV.open_numbers_digits(chat_id, rest[0]); return
    if cmd == "inv_nb_qty":             INV.open_number_qty_spinner(chat_id, rest[0], rest[1]); return
    if cmd == "inv_nb_adj":             INV.adjust_number_qty(chat_id, rest[0], rest[1], int(rest[2])); return
    if cmd == "inv_nb_set":             INV.set_number_qty(chat_id, rest[0], rest[1], int(rest[2])); return
    if cmd == "inv_nb_save":            INV.save_number_qty(chat_id, rest[0], rest[1]); return
    if cmd == "inv_nb_apply_all":       INV.apply_all_numbers(chat_id, rest[0]); return
    if cmd == "inv_templates":          INV.open_inventory_templates(chat_id); return
    if cmd == "inv_tmpl_nums":          INV.open_template_numbers(chat_id, rest[0]); return
    if cmd == "inv_tmpl_qty":           INV.open_template_qty_spinner(chat_id, rest[0], rest[1]); return
    if cmd == "inv_tmpl_adj":           INV.adjust_template_qty(chat_id, rest[0], rest[1], int(rest[2])); return
    if cmd == "inv_tmpl_set":           INV.set_template_qty(chat_id, rest[0], rest[1], int(rest[2])); return
    if cmd == "inv_tmpl_save":          INV.save_template_qty(chat_id, rest[0], rest[1]); return
    if cmd == "inv_tmpl_apply_all":     INV.apply_all_templates(chat_id, rest[0]); return

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
    settings["color_names"]  = tmp.get("color_names", {})
    settings["layouts"]      = tmp.get("layouts", settings.get("layouts", {}))
    save_settings(settings)

    from services.inventory import save_merch_inv, save_letters_inv, save_numbers_inv, save_templates_inv
    save_merch_inv(tmp.get("_inv_merch", {}))
    save_letters_inv(tmp.get("_inv_letters", {}))
    save_numbers_inv(tmp.get("_inv_numbers", {}))
    save_templates_inv(tmp.get("_inv_tmpls", {}))

    edit(chat_id,
         "✅ Готово!\nБот настроен и готов к приёму заказов. \n\nЧто дальше?\n• Нажмите /start, чтобы открыть главное меню.\n• Используйте «Сделать заказ» — процесс быстрый и пошаговый.\n• Настройки можно менять в любой момент — они сохраняются.",
         None)
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
    elif st == "tmpl_nums_enter" and text:
        from .A6_TemplatesNumbers import handle_input; handle_input(chat_id, text)
    # --- коллажи (фото) ---
    elif st.startswith("tmpl_collages:") and m.content_type == "photo":
        mk = st.split(":")[1]
        d = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})
        f_id = m.photo[-1].file_id
        col = d.setdefault("collages", [])
        col.append(f_id)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Готово ✅", callback_data="setup:tmpl_collages_done"))
        kb.add(types.InlineKeyboardButton("Пропустить", callback_data="setup:tmpl_collages_done"))
        edit(chat_id,
             f"Шаг 3.3/4. Пришлите 1–5 изображений‑коллажей (со списком макетов).\nЗагружено коллажей: {len(col)}",
             kb)
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
    elif st.startswith("inv_sz_all:") and text:
        mk, ck = st.split(":")[1:3]
        try:
            val = int(text); assert val >= 0
            inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
            for sz in WIZ[chat_id]["data"]["merch"][mk]["sizes"]:
                inv[sz] = val
            INV.open_sizes(chat_id, mk, ck)
        except Exception:
            INV.apply_all_sizes(chat_id, mk, ck)
    elif st.startswith("inv_sz_qty:") and text:
        mk, ck, sz = st.split(":")[1:4]
        try:
            val = int(text); assert val >= 0
            inv = WIZ[chat_id]["data"].setdefault("_inv_merch", {}).setdefault(mk, {}).setdefault(ck, {}).setdefault("sizes", {})
            inv[sz] = val
            INV.open_sizes(chat_id, mk, ck)
        except Exception:
            INV.open_qty_spinner(chat_id, mk, ck, sz)
    elif st.startswith("inv_lt_all:") and text:
        tc = st.split(":")[1]
        try:
            val = int(text); assert val >= 0
            INV.set_all_letters(chat_id, tc, val)
        except Exception:
            INV.apply_all_letters(chat_id, tc)
    elif st.startswith("inv_lt_qty:") and text:
        tc, ch = st.split(":")[1:3]
        try:
            val = int(text); assert val >= 0
            inv = WIZ[chat_id]["data"].setdefault("_inv_letters", {}).setdefault(tc, {}).setdefault("letters", {})
            inv[ch] = val
            INV.open_letters_chars(chat_id, tc)
        except Exception:
            INV.open_letter_qty_spinner(chat_id, tc, ch)
    elif st.startswith("inv_nb_all:") and text:
        tc = st.split(":")[1]
        try:
            val = int(text); assert val >= 0
            INV.set_all_numbers(chat_id, tc, val)
        except Exception:
            INV.apply_all_numbers(chat_id, tc)
    elif st.startswith("inv_nb_qty:") and text:
        tc, dg = st.split(":")[1:3]
        try:
            val = int(text); assert val >= 0
            inv = WIZ[chat_id]["data"].setdefault("_inv_numbers", {}).setdefault(tc, {}).setdefault("numbers", {})
            inv[dg] = val
            INV.open_numbers_digits(chat_id, tc)
        except Exception:
            INV.open_number_qty_spinner(chat_id, tc, dg)
    elif st.startswith("inv_tmpl_all:") and text:
        mk = st.split(":")[1]
        try:
            val = int(text); assert val >= 0
            INV.set_all_templates(chat_id, mk, val)
        except Exception:
            INV.apply_all_templates(chat_id, mk)
    elif st.startswith("inv_tmpl_qty:") and text:
        mk, num = st.split(":")[1:3]
        try:
            val = int(text); assert val >= 0
            inv = WIZ[chat_id]["data"].setdefault("_inv_tmpls", {}).setdefault(mk, {}).setdefault("templates", {})
            inv.setdefault(num, {})["qty"] = val
            INV.open_template_numbers(chat_id, mk)
        except Exception:
            INV.open_template_qty_spinner(chat_id, mk, num)
    elif st == "tmpl_limit" and text:
        try:
            val = int(text); assert val >= 1
            WIZ[chat_id]["data"].setdefault("layouts", {}).update({"max_per_order": val})
            render_templates_home(chat_id)
        except Exception:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
            edit(chat_id, "Введите целое число ≥1:", kb)
    elif st == "tmpl_indicator" and text:
        WIZ[chat_id]["data"].setdefault("layouts", {}).update({"selected_indicator": text.strip() or "🟩"})
        render_templates_home(chat_id)
    # --- удаляем любое пользовательское сообщение ---
    _safe_del(chat_id, m.message_id)
