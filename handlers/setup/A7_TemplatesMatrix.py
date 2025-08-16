# -*- coding: utf-8 -*-
"""Матрица соответствий макетов и цветов для массового редактирования."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple
import csv
import io

from telebot import types

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


def start_matrix(chat_id: int, mk: str, page: int = 0) -> None:
    state = MatrixState(mk=mk, page=page)
    WIZ[chat_id]["_matrix_state"] = state
    _render_matrix(chat_id)


def _render_matrix(chat_id: int) -> None:
    state: MatrixState = WIZ[chat_id]["_matrix_state"]
    d = WIZ[chat_id]["data"]
    mk = state.mk
    layouts = _layouts_for_merch(d, mk)
    colors = _colors_for_merch(d, mk)

    if state.search:
        layouts = [l for l in layouts if state.search.upper() in l.upper()]

    per_page = 25
    pages = max(1, (len(layouts) + per_page - 1) // per_page)
    page = max(0, min(state.page, pages - 1))
    state.page = page
    start = page * per_page
    subset = layouts[start:start + per_page]

    kb = types.InlineKeyboardMarkup()

    # header row for colors
    header = []
    for ck, cname in colors:
        header.append(types.InlineKeyboardButton(cname[:3], callback_data="noop"))
    kb.row(*header)

    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num in subset:
        info = tpls.setdefault(num, {"allowed_colors": []})
        row = []
        for ck, _ in colors:
            mark = "✅" if ck in info.get("allowed_colors", []) else "□"
            row.append(types.InlineKeyboardButton(mark, callback_data=f"setup:matrix_toggle:{mk}:{num}:{ck}:{page}"))
        kb.row(types.InlineKeyboardButton(num, callback_data="noop"), *row)

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("«‹", callback_data=f"setup:matrix_page:{page-1}"))
    if page < pages - 1:
        nav.append(types.InlineKeyboardButton("›»", callback_data=f"setup:matrix_page:{page+1}"))
    if nav:
        kb.row(*nav)
    kb.add(types.InlineKeyboardButton("CSV экспорт", callback_data="setup:matrix_csv_export"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))

    merch_name = d["merch"][mk]["name_ru"]
    edit(chat_id, f"Матрица макетов/цветов — {merch_name}\nСтраница {page+1}/{pages}", kb)
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


def handle_group_apply(chat_id: int, mk: str, color: str, text: str) -> None:
    tpls = WIZ[chat_id]["data"].setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    for num in _parse_tokens(text):
        info = tpls.setdefault(num, {"allowed_colors": []})
        if color not in info["allowed_colors"]:
            info["allowed_colors"].append(color)
    _render_matrix(chat_id)


# --- router integration ------------------------------------------------------

# The setup.router module should import this file and route callbacks accordingly.
