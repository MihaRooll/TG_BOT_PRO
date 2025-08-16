# -*- coding: utf-8 -*-
"""Матрица соответствий макетов и цветов для массового редактирования."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple
import csv
import io

from telebot import types

from services import audit
from .core import WIZ, edit


# --- helpers -----------------------------------------------------------------

def _parse_tokens(text: str) -> List[str]:
    """Разобрать списки и диапазоны вида ``A1,A3-A5,7`` в список идентификаторов.

    Диапазоны поддерживают одинаковый префикс (A1-A5, 1-9).
    """
    out: List[str] = []
    for raw in filter(None, [t.strip() for t in text.split(",")]):
        token = raw.upper()
        if "-" in token:
            left, right = token.split("-", 1)
            pref_l = ''.join(filter(str.isalpha, left))
            pref_r = ''.join(filter(str.isalpha, right))
            num_l = ''.join(filter(str.isdigit, left))
            num_r = ''.join(filter(str.isdigit, right))
            if pref_l == pref_r and num_l.isdigit() and num_r.isdigit():
                a, b = int(num_l), int(num_r)
                step = 1 if a <= b else -1
                for i in range(a, b + step, step):
                    out.append(f"{pref_l}{i}" if pref_l else str(i))
                continue
        out.append(token)
    # dedupe preserving order
    seen = set()
    uniq = []
    for t in out:
        if t not in seen:
            uniq.append(t)
            seen.add(t)
    return uniq


def _layouts_for_merch(data: Dict, mk: str) -> List[str]:
    tmpls = data.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    return sorted(tmpls.keys(), key=lambda x: (len(x), x))


def _colors_for_merch(data: Dict, mk: str) -> List[Tuple[str, str]]:
    """Return list of (color_key, color_name_ru)."""
    merch = data["merch"][mk]
    return [(ck, info["name_ru"]) for ck, info in merch["colors"].items()]


# --- matrix rendering ---------------------------------------------------------

@dataclass
class MatrixState:
    mk: str
    page: int = 0
    search: str = ""


def _matrix_key(chat_id: int) -> MatrixState:
    return WIZ[chat_id].setdefault("_matrix_state", MatrixState(mk=""))


def start_matrix(chat_id: int, mk: str, user=None, page: int = 0) -> None:
    state = MatrixState(mk=mk, page=page)
    WIZ[chat_id]["_matrix_state"] = state
    # skeleton to avoid perceived freeze
    edit(chat_id, "⏳ Загрузка…", types.InlineKeyboardMarkup())
    _preflight(chat_id, mk, user)


def _preflight(chat_id: int, mk: str, user=None) -> None:
    d = WIZ[chat_id]["data"]
    g_tmpls = d.get("templates", {}).get("__global__", {}).get("templates", {})
    l_tmpls = d.get("templates", {}).get(mk, {}).get("templates", {})
    union = set(g_tmpls.keys()) | set(l_tmpls.keys())
    merch_name = d["merch"][mk]["name_ru"]
    if not union:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(
            f"Применить глобальные макеты к «{merch_name}»",
            callback_data=f"setup:matrix_apply_global:{mk}"
        ))
        kb.add(types.InlineKeyboardButton("Добавить номера макетов (Глобально)", callback_data="setup:tmpl_nums_global"))
        kb.add(types.InlineKeyboardButton(
            f"Добавить номера макетов (Для «{merch_name}»)",
            callback_data=f"setup:tmpl_nums_for:{mk}"
        ))
        kb.add(types.InlineKeyboardButton("Сменить область / мерч", callback_data="setup:tmpl_map"))
        edit(chat_id, f"⚠️ Для «{merch_name}» пока нет макетов.\nЧто сделать?", kb)
        audit.add_event(user=user, section="layouts.colors", action="preflight", scope=f"merch:{mk}", notes="no_layouts")
        WIZ[chat_id]["stage"] = "matrix_empty"
        return
    if g_tmpls and mk in d.get("templates", {}) and not l_tmpls:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("Сбросить до глобальных", callback_data=f"setup:matrix_reset_global:{mk}"))
        kb.add(types.InlineKeyboardButton("Оставить как есть", callback_data="setup:tmpl_map"))
        edit(chat_id,
             f"🚫 У «{merch_name}» есть локальное переопределение, которое отключает глобальные макеты.\nСбросить до глобальных?",
             kb)
        audit.add_event(user=user, section="layouts.colors", action="preflight", scope=f"merch:{mk}", notes="override_blocks_global")
        WIZ[chat_id]["stage"] = "matrix_empty"
        return
    if not _colors_for_merch(d, mk):
        edit(chat_id, "ℹ️ В этой области пока нечего показывать. Добавьте номера макетов или примените глобальные.")
        audit.add_event(user=user, section="layouts.colors", action="preflight", scope=f"merch:{mk}", notes="no_colors")
        WIZ[chat_id]["stage"] = "matrix_empty"
        return
    if all(not info.get("allowed_colors") for info in l_tmpls.values()) and not any(
        g_tmpls.get(num, {}).get("allowed_colors") for num in union
    ):
        note = "no_colors_configured"
        audit.add_event(user=user, section="layouts.colors", action="preflight", scope=f"merch:{mk}", notes=note)
        _render_matrix(chat_id, info="⚠️ Макеты есть, но цвета не настроены.\nВыберите цвета ниже или нажмите «Наследовать глобальные»."
        )
        return
    _render_matrix(chat_id)


def _render_matrix(chat_id: int, info: str | None = None) -> None:
    state: MatrixState = WIZ[chat_id]["_matrix_state"]
    d = WIZ[chat_id]["data"]
    mk = state.mk
    layouts = _layouts_for_merch(d, mk)
    colors = _colors_for_merch(d, mk)

    if not layouts or not colors:
        edit(chat_id, "ℹ️ В этой области пока нечего показывать. Добавьте номера макетов или примените глобальные.")
        return

    if state.search:
        layouts = [l for l in layouts if state.search.upper() in l.upper()]

    per_page = 25
    pages = max(1, (len(layouts) + per_page - 1) // per_page)
    page = max(0, min(state.page, pages - 1))
    state.page = page
    start = page * per_page
    subset = layouts[start:start + per_page]

    kb = types.InlineKeyboardMarkup()

    # header row with placeholder
    header = [types.InlineKeyboardButton("№", callback_data="noop")]
    for ck, cname in colors:
        header.append(
            types.InlineKeyboardButton(cname[:3], callback_data=f"setup:matrix_col:{mk}:{ck}:{page}")
        )
    kb.row(*header)

    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num in subset:
        info = tpls.setdefault(num, {"allowed_colors": []})
        row = []
        for ck, _ in colors:
            mark = "✅" if ck in info.get("allowed_colors", []) else "⬜"
            row.append(types.InlineKeyboardButton(mark, callback_data=f"setup:matrix_toggle:{mk}:{num}:{ck}:{page}"))
        kb.row(types.InlineKeyboardButton(num, callback_data="noop"), *row)

    kb.row(
        types.InlineKeyboardButton("Выбрать все", callback_data=f"setup:matrix_page_all:{mk}:{page}"),
        types.InlineKeyboardButton("Снять все", callback_data=f"setup:matrix_page_none:{mk}:{page}")
    )

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("«‹", callback_data=f"setup:matrix_page:{page-1}"))
    if page < pages - 1:
        nav.append(types.InlineKeyboardButton("›»", callback_data=f"setup:matrix_page:{page+1}"))
    if nav:
        kb.row(*nav)

    kb.row(
        types.InlineKeyboardButton("Наследовать глобальные", callback_data=f"setup:matrix_inherit:{mk}"),
        types.InlineKeyboardButton("Сбросить до глобальных", callback_data=f"setup:matrix_reset:{mk}")
    )
    kb.add(types.InlineKeyboardButton("CSV экспорт", callback_data="setup:matrix_csv_export"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))

    merch_name = d["merch"][mk]["name_ru"]
    legend = "✅ — разрешён, ⬜ — выключен."
    msg = f"{legend}\nМатрица макетов/цветов — {merch_name}\nСтраница {page+1}/{pages}"
    if info:
        msg = f"{info}\n{msg}"
    edit(chat_id, msg, kb)
    WIZ[chat_id]["stage"] = "matrix"


def toggle_cell(chat_id: int, mk: str, num: str, ck: str, page: int) -> None:
    tpls = WIZ[chat_id]["data"]["templates"].setdefault(mk, {"templates": {}, "collages": []})["templates"]
    info = tpls.setdefault(num, {"allowed_colors": []})
    allowed = info.setdefault("allowed_colors", [])
    if ck in allowed:
        allowed.remove(ck)
    else:
        allowed.append(ck)
    _render_matrix(chat_id)


def toggle_column(chat_id: int, mk: str, ck: str, page: int) -> None:
    d = WIZ[chat_id]["data"]
    layouts = _layouts_for_merch(d, mk)
    per_page = 25
    start = page * per_page
    subset = layouts[start:start + per_page]
    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    all_on = all(ck in tpls.setdefault(num, {"allowed_colors": []}).get("allowed_colors", []) for num in subset)
    for num in subset:
        info = tpls.setdefault(num, {"allowed_colors": []})
        allowed = info.setdefault("allowed_colors", [])
        if all_on:
            if ck in allowed:
                allowed.remove(ck)
        else:
            if ck not in allowed:
                allowed.append(ck)
    _render_matrix(chat_id)


def page_select(chat_id: int, mk: str, page: int, allow: bool) -> None:
    d = WIZ[chat_id]["data"]
    layouts = _layouts_for_merch(d, mk)
    colors = [ck for ck, _ in _colors_for_merch(d, mk)]
    per_page = 25
    start = page * per_page
    subset = layouts[start:start + per_page]
    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num in subset:
        info = tpls.setdefault(num, {"allowed_colors": []})
        if allow:
            for ck in colors:
                if ck not in info["allowed_colors"]:
                    info["allowed_colors"].append(ck)
        else:
            info["allowed_colors"] = [ck for ck in info.get("allowed_colors", []) if ck not in colors]
    _render_matrix(chat_id)


def change_page(chat_id: int, page: int) -> None:
    WIZ[chat_id]["_matrix_state"].page = page
    _render_matrix(chat_id)


# --- copy / paste -------------------------------------------------------------

def copy_layout(chat_id: int, mk: str, num: str) -> None:
    tpls = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    info = tpls.get(num, {"allowed_colors": []})
    WIZ[chat_id]["_matrix_copy"] = list(info.get("allowed_colors", []))


def paste_layout(chat_id: int, mk: str, nums: List[str]) -> None:
    colors = WIZ[chat_id].get("_matrix_copy")
    if colors is None:
        return
    tpls = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num in nums:
        info = tpls.setdefault(num, {"allowed_colors": []})
        info["allowed_colors"] = list(colors)
    _render_matrix(chat_id)


# --- CSV export/import -------------------------------------------------------

def export_csv(chat_id: int, mk: str) -> None:
    d = WIZ[chat_id]["data"]
    tpls = d.get("templates", {}).get(mk, {}).get("templates", {})
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["layout", "color", "allowed"])
    for num, info in tpls.items():
        allowed = set(info.get("allowed_colors", []))
        for ck, _ in _colors_for_merch(d, mk):
            writer.writerow([num, ck, ck in allowed])
    output.seek(0)
    from bot import bot
    bot.send_document(chat_id, (f"matrix_{mk}.csv", output.getvalue()))


def import_csv(chat_id: int, mk: str, content: bytes) -> None:
    d = WIZ[chat_id]["data"]
    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    reader = csv.reader(io.StringIO(content.decode("utf-8")))
    next(reader, None)
    for layout, color, allowed in reader:
        info = tpls.setdefault(layout, {"allowed_colors": []})
        if allowed.lower() in ("1", "true", "yes", "y"):   # enabled
            if color not in info["allowed_colors"]:
                info["allowed_colors"].append(color)
        else:
            if color in info["allowed_colors"]:
                info["allowed_colors"].remove(color)
    _render_matrix(chat_id)


# --- group apply -------------------------------------------------------------

def ask_group_apply(chat_id: int, mk: str, color: str) -> None:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:matrix_back:{mk}"))
    edit(chat_id, "Введите список макетов или диапазоны (A1-A5,1-9):", kb)
    WIZ[chat_id]["stage"] = f"matrix_group:{mk}:{color}"


def apply_global_to_merch(chat_id: int, mk: str) -> None:
    d = WIZ[chat_id]["data"]
    g = d.get("templates", {}).get("__global__", {}).get("templates", {})
    if not g:
        edit(chat_id, "ℹ️ В этой области пока нечего показывать. Добавьте номера макетов или примените глобальные.")
        return
    local = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num, meta in g.items():
        local[num] = {"allowed_colors": list(meta.get("allowed_colors", []))}
    start_matrix(chat_id, mk)


def inherit_global(chat_id: int, mk: str) -> None:
    d = WIZ[chat_id]["data"]
    g = d.get("templates", {}).get("__global__", {}).get("templates", {})
    local = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num, meta in g.items():
        info = local.setdefault(num, {"allowed_colors": []})
        for ck in meta.get("allowed_colors", []):
            if ck not in info["allowed_colors"]:
                info["allowed_colors"].append(ck)
    _render_matrix(chat_id)


def reset_to_global(chat_id: int, mk: str) -> None:
    d = WIZ[chat_id]["data"]
    g = d.get("templates", {}).get("__global__", {}).get("templates", {})
    d.setdefault("templates", {})[mk] = {"templates": {}, "collages": []}
    local = d["templates"][mk]["templates"]
    for num, meta in g.items():
        local[num] = {"allowed_colors": list(meta.get("allowed_colors", []))}
    _render_matrix(chat_id)


def handle_group_apply(chat_id: int, mk: str, color: str, text: str) -> None:
    tpls = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num in _parse_tokens(text):
        info = tpls.setdefault(num, {"allowed_colors": []})
        if color not in info["allowed_colors"]:
            info["allowed_colors"].append(color)
    _render_matrix(chat_id)


# --- router integration ------------------------------------------------------

# The setup.router module should import this file and route callbacks accordingly.
