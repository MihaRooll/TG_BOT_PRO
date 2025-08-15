# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from telebot import types
from .core import WIZ, edit

RULES = [
    (re.compile(r'^\d+$'), lambda d, token: [(mk, 'all') for mk in d.get('merch', {}).keys()]),
    (re.compile(r'^A\d+$'), lambda d, token: [('tshirt', ['black'])] if 'tshirt' in d.get('merch', {}) else []),
]


def start_for_merchs(chat_id: int, mks: list[str]):
    data = WIZ[chat_id]["data"].setdefault("templates", {})
    for mk in mks:
        data.setdefault(mk, {"templates": {}, "collages": []})
    WIZ[chat_id]["data"]["_tmpl_current_mks"] = mks
    render_prompt(chat_id)


def _sort_tokens(tokens: set[str]) -> list[str]:
    def key(tok: str):
        m = re.match(r'([A-Z]*)(\d+)', tok)
        prefix, num = m.group(1), int(m.group(2))
        if prefix:
            return (0, prefix, num)
        return (1, '', num)
    return sorted(tokens, key=key)


def render_prompt(chat_id: int, skipped: list[str] | None = None):
    mks = WIZ[chat_id]["data"].get("_tmpl_current_mks", [])
    data = WIZ[chat_id]["data"].get("templates", {})
    union = set()
    for mk in mks:
        union.update(data.get(mk, {}).get("templates", {}).keys())
    existing = ", ".join(_sort_tokens(union)) or "—"
    title = ", ".join(mks)
    msg = f"Шаг 3/4. Введите номера макетов ({title}) через запятую.\nСписок: {existing}"
    if skipped:
        msg += f"\nПропущено: {', '.join(skipped)}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="setup:tmpl_num_done"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
    edit(chat_id, msg, kb)
    WIZ[chat_id]["stage"] = "tmpl_nums_enter"


def _parse(text: str) -> tuple[list[str], list[str]]:
    parts = re.split(r'[\s,]+', text.replace('\n', ' ').upper())
    tokens: list[str] = []
    skipped: list[str] = []
    for p in parts:
        if not p:
            continue
        m = re.fullmatch(r'([A-Z]*)(\d+)-([A-Z]*)(\d+)', p)
        if m:
            pre1, n1, pre2, n2 = m.groups()
            if pre1 == pre2:
                a, b = int(n1), int(n2)
                step = 1 if a <= b else -1
                for i in range(a, b + step, step):
                    tokens.append(f"{pre1}{i}")
            else:
                skipped.append(p)
            continue
        m = re.fullmatch(r'([A-Z]*)(\d+)', p)
        if m:
            tokens.append(f"{m.group(1)}{int(m.group(2))}")
        else:
            skipped.append(p)
    seen = set()
    ordered: list[str] = []
    for t in tokens:
        if t not in seen:
            ordered.append(t)
            seen.add(t)
    return ordered, skipped


def handle_input(chat_id: int, text: str):
    tokens, skipped = _parse(text)
    d = WIZ[chat_id]["data"]
    templates = d.setdefault("templates", {})
    mks = d.get("_tmpl_current_mks", [])
    merch = d.get("merch", {})

    for tok in tokens:
        applied = False
        for pat, fn in RULES:
            if pat.match(tok):
                targets = fn(d, tok)
                for mk, colors in targets:
                    tmpl = templates.setdefault(mk, {"templates": {}, "collages": []})
                    tinfo = tmpl.setdefault("templates", {}).setdefault(tok, {"allowed_colors": []})
                    if tinfo["allowed_colors"] == []:
                        if colors == 'all':
                            tinfo["allowed_colors"] = list(merch.get(mk, {}).get("colors", {}).keys())
                        elif isinstance(colors, list):
                            tinfo["allowed_colors"] = colors
                applied = True
                break
        if not applied:
            for mk in mks:
                tmpl = templates.setdefault(mk, {"templates": {}, "collages": []})
                tmpl.setdefault("templates", {}).setdefault(tok, {"allowed_colors": []})
    render_prompt(chat_id, skipped)
