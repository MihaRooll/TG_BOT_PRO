# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from .core import WIZ, ensure, edit, home_text

from . import A0_Overview as O
from . import A1_Merch    as M
from . import A2_Letters  as L
from . import A4_TextPalette as P
from . import A5_MapTextColors as MAP
from . import A6_TemplatesNumbers as TNUM
from . import A7_TemplatesColors  as TCOL
from . import A8_TemplatesCollages as TCOLL
from . import A9_InventorySizes   as INV


# ---------------------------------------------------------------------------
# Callback routing
# ---------------------------------------------------------------------------

def _bind_hint(chat_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:home"))
    edit(
        chat_id,
        "📌 Привязка общего чата:\n1) Добавьте бота в нужную группу/канал (в канале — как администратора).\n2) Выполните там команду /bind_here.\nБот запомнит чат (и тему, если есть).",
        kb,
    )


def _open_tmpls(chat_id: int):
    kb = types.InlineKeyboardMarkup(row_width=1)
    d = WIZ[chat_id]["data"]
    for mk, mi in d.get("merch", {}).items():
        kb.add(types.InlineKeyboardButton(mi['name_ru'], callback_data=f"setup:tmpl_nums_for:{mk}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:home"))
    edit(chat_id, "Шаг 3/4. Выберите вид мерча для ввода номеров макетов.", kb)
    WIZ[chat_id]["stage"] = "tmpls_pick"


CALLBACKS = {
    # home / overview
    "init":              lambda cid, r: O.render_home(cid),
    "home":              lambda cid, r: O.render_home(cid),
    "bind_hint":        lambda cid, r: _bind_hint(cid),

    # step 1: merch
    "merch":            lambda cid, r: M.render_types(cid),
    "merch_toggle":     lambda cid, r: M.toggle_type(cid, r[0]),
    "merch_add":        lambda cid, r: M.ask_custom(cid),
    "colors_sizes":     lambda cid, r: M.start_colors_iter(cid),
    "colors":           lambda cid, r: M.render_colors(cid, r[0]),
    "color_toggle":     lambda cid, r: M.toggle_color(cid, r[0], r[1]),
    "color_add":        lambda cid, r: M.ask_custom_color(cid, r[0]),
    "sizes":            lambda cid, r: M.render_sizes(cid, r[0]),
    "sizes_default":    lambda cid, r: M.set_default_sizes(cid, r[0]),
    "sizes_one":        lambda cid, r: M.set_one_size(cid, r[0]),
    "sizes_add":        lambda cid, r: M.ask_custom_sizes(cid, r[0]),
    "next_merch_or_done": lambda cid, r: M.next_merch_or_done(cid),

    # step 2: letters & limits
    "letters":          lambda cid, r: L.render_letters_hub(cid),
    "numbers":          lambda cid, r: L.render_letters_hub(cid),
    "feature_toggle":   lambda cid, r: L.toggle_feature(cid, r[0]),
    "rule_toggle":      lambda cid, r: L.toggle_rule(cid, r[0]),
    "limits":           lambda cid, r: L.render_limits_progress(cid),
    "limits_edit":      lambda cid, r: L.ask_limit_len(cid) if r[0] == "text_len" else L.ask_limit_num(cid),
    "limits_done":      lambda cid, r: L.render_letters_hub(cid),
    "palette":          lambda cid, r: P.render_palette(cid),
    "pal_toggle":       lambda cid, r: P.toggle_palette_color(cid, r[0]),
    "pal_add":          lambda cid, r: P.ask_custom_color(cid),

    # step 2.1: map text colors
    "map_text_colors":  lambda cid, r: MAP.render_next_pair(cid),
    "maptc_toggle":     lambda cid, r: MAP.toggle_map(cid, r[0], r[1], r[2]),
    "maptc_next":       lambda cid, r: MAP.next_pair(cid),

    # step 3: templates
    "tmpls":            lambda cid, r: _open_tmpls(cid),
    "tmpl_nums_for":    lambda cid, r: TNUM.start_for_merch(cid, r[0]),
    "tmpl_num_done":    lambda cid, r: TNUM.done(cid),
    "tmpl_color_toggle": lambda cid, r: TCOL.toggle_color(cid, r[0], r[1], r[2]),
    "tmpl_color_next":  lambda cid, r: TCOL.next_template(cid, r[0], r[1]),
    "tmpl_collages_done": lambda cid, r: TCOLL.collages_done(cid),

    # step 4: inventory
    "inv":              lambda cid, r: INV.open_inventory_sizes(cid),
    "inv_sizes_colors": lambda cid, r: INV.open_colors(cid, r[0]),
    "inv_sizes_sizes":  lambda cid, r: INV.open_sizes(cid, r[0], r[1]),
    "inv_sz_qty":       lambda cid, r: INV.open_qty_spinner(cid, r[0], r[1], r[2]),
    "inv_sz_adj":       lambda cid, r: INV.adjust_qty(cid, r[0], r[1], r[2], int(r[3])),
    "inv_sz_set":       lambda cid, r: INV.set_qty(cid, r[0], r[1], r[2], int(r[3])),
    "inv_sz_save":      lambda cid, r: INV.save_qty(cid, r[0], r[1], r[2]),
    "inv_sz_apply_all": lambda cid, r: INV.apply_all_sizes(cid, r[0], r[1]),
    "inv_sz_all_set":   lambda cid, r: INV.set_all_sizes(cid, r[0], r[1], int(r[2])),

    # finish
    "finish":           lambda cid, r: _finish(cid),
}


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("setup:"))
def setup_router(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    bot.answer_callback_query(c.id)
    ensure(chat_id, c.message.message_id)
    parts = c.data.split(":")
    cmd, rest = parts[1], parts[2:]
    handler = CALLBACKS.get(cmd)
    if handler:
        handler(chat_id, rest)


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

    summary = home_text(tmp)
    edit(chat_id, summary + "\n\n<b>Готово! ☑ Бот настроен и готов к приёму заказов. Нажмите /start.</b>", None)
    WIZ.pop(chat_id, None)


# ----------- удаляем пользовательские сообщения и обрабатываем ввод ----------
def _safe_del(mid_chat: int, mid: int):
    try:
        bot.delete_message(mid_chat, mid)
    except Exception:
        pass


def _handle_limit_len(chat_id: int, text: str):
    try:
        val = int(text); assert val > 0
        L.set_limit_len(chat_id, val)
    except Exception:
        L.ask_limit_len(chat_id)


def _handle_limit_num(chat_id: int, text: str):
    try:
        val = int(text); assert val >= 0
        L.set_limit_num(chat_id, val)
    except Exception:
        L.ask_limit_num(chat_id)


def _handle_inv_qty(chat_id: int, st: str, text: str):
    mk, ck, sz = st.split(":")[1:]
    try:
        val = int(text)
        INV.set_qty(chat_id, mk, ck, sz, val)
    except Exception:
        INV.open_qty_spinner(chat_id, mk, ck, sz)


def _handle_collage(chat_id: int, st: str, m: types.Message):
    mk = st.split(":")[1]
    d = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})
    f_id = m.photo[-1].file_id
    col = d.setdefault("collages", [])
    if len(col) < 10:
        col.append(f_id)
    TCOLL.render_progress(chat_id)


TEXT_STAGES = {
    "merch_add":      lambda cid, st, text: M.handle_custom_input(cid, text),
    "color_add":      lambda cid, st, text: M.handle_custom_color(cid, st.split(":")[1], text),
    "sizes_add":      lambda cid, st, text: M.handle_custom_sizes(cid, st.split(":")[1], text),
    "pal_add":        lambda cid, st, text: P.handle_custom_color(cid, text),
    "tmpl_nums_input": lambda cid, st, text: TNUM.handle_text(cid, st.split(":")[1], text),
    "limits_len":     lambda cid, st, text: _handle_limit_len(cid, text),
    "limits_num":     lambda cid, st, text: _handle_limit_num(cid, text),
    "inv_sz_qty":     lambda cid, st, text: _handle_inv_qty(cid, st, text),
}


@bot.message_handler(func=lambda m: m.chat.id in WIZ, content_types=["text","photo"])
def _during_setup(m: types.Message):
    chat_id = m.chat.id
    st = WIZ[chat_id].get("stage", "")
    if m.content_type == "photo" and st.startswith("tmpl_collages:"):
        _handle_collage(chat_id, st, m)
    elif m.content_type == "text":
        text = (m.text or "").strip()
        for key, fn in TEXT_STAGES.items():
            if st == key or st.startswith(key + ":"):
                fn(chat_id, st, text)
                break
    _safe_del(chat_id, m.message_id)

