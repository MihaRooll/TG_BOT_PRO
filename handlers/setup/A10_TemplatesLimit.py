# -*- coding: utf-8 -*-
"""Редактор лимитов макетов."""

import re
from telebot import types
from .core import WIZ, edit
from services.settings import get_settings


def ask_limits(chat_id: int, mks: list[str]):
    d = WIZ[chat_id]["data"]
    d["_limit_scope"] = mks
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpl_limit"))
    edit(chat_id, "Введите пары «макеты:лимит», напр. A1,A2:2;1-5:4", kb)
    WIZ[chat_id]["stage"] = f"tmpl_limit_edit"


def _parse_tokens(toks: str):
    parts = re.split(r"[\s,]+", toks.strip().upper())
    tokens = []
    bad = []
    for p in parts:
        if not p:
            continue
        m = re.fullmatch(r"([A-Z]*)(\d+)-([A-Z]*)(\d+)", p)
        if m:
            pre1, n1, pre2, n2 = m.groups()
            if pre1 == pre2:
                a, b = int(n1), int(n2)
                step = 1 if a <= b else -1
                for i in range(a, b + step, step):
                    tokens.append(f"{pre1}{i}")
            else:
                bad.append(p)
            continue
        m = re.fullmatch(r"([A-Z]*)(\d+)", p)
        if m:
            tokens.append(f"{m.group(1)}{int(m.group(2))}")
        else:
            bad.append(p)
    seen = set()
    ordered = []
    for t in tokens:
        if t not in seen:
            ordered.append(t)
            seen.add(t)
    return ordered, bad


def _parse_pairs(text: str):
    pairs = {}
    skipped = []
    for part in text.split(';'):
        part = part.strip()
        if not part:
            continue
        if ':' not in part:
            skipped.append(part)
            continue
        tokens_part, lim_part = part.split(':', 1)
        try:
            lim = int(lim_part.strip())
        except ValueError:
            skipped.append(part)
            continue
        tokens, bad = _parse_tokens(tokens_part)
        for b in bad:
            skipped.append(b)
        for t in tokens:
            pairs[t] = lim
    return pairs, skipped


def handle_input(chat_id: int, text: str):
    d = WIZ[chat_id]["data"]
    layouts = d.setdefault("layouts", get_settings().get("layouts", {}))
    limits = layouts.setdefault("per_template_limits", {})
    scope = d.get("_limit_scope", [])
    pairs, skipped = _parse_pairs(text)
    for mk in scope:
        lm = limits.setdefault(mk, {})
        lm.update(pairs)
    msg = "Лимиты обновлены."
    if skipped:
        msg += "\nПропущено: " + ", ".join(skipped)
    d.pop("_limit_scope", None)
    from .router import render_templates_home
    render_templates_home(chat_id)
