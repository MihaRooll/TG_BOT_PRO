# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from telebot import types
from services import audit
from .core import WIZ, edit


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

    for tok in tokens:
        for mk in mks:
            tmpl = templates.setdefault(mk, {"templates": {}, "collages": []})
            tmpl.setdefault("templates", {}).setdefault(tok, {"allowed_colors": []})
    render_prompt(chat_id, skipped)


# ---- scope linter -----------------------------------------------------------
RULES = {
    r"^A\d+$": {"merch_ru": "Футболки"},
    r"^D\d+$": {"merch_ru": "Шопперы"},
}


def scope_lint(chat_id: int):
    d = WIZ[chat_id]["data"]
    g = d.get("templates", {}).get("__global__", {}).get("templates", {})
    misplaced: dict[str, list[str]] = {}
    for tok in g.keys():
        for rx, target in RULES.items():
            if re.match(rx, tok):
                mk = _find_merch_key(d, target["merch_ru"])
                if mk:
                    misplaced.setdefault(mk, []).append(tok)
                break
    if not misplaced:
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpl_nums")
        )
        edit(chat_id, "Линтер: проблем не найдено.", kb)
        return
    mk, tokens = next(iter(misplaced.items()))
    tokens_str = ", ".join(tokens)
    merch_name = d["merch"][mk]["name_ru"]
    d["_lint_move"] = {"target": mk, "tokens": tokens}
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Перенести", callback_data="setup:tmpl_scope_lint_move"),
        types.InlineKeyboardButton("Оставить", callback_data="setup:tmpl_nums"),
    )
    edit(
        chat_id,
        f"Найдено: {tokens_str} в «Глобально». Предложение: перенести → {merch_name}.\nПереместим {len(tokens)} записей.",
        kb,
    )


def apply_lint_move(chat_id: int):
    d = WIZ[chat_id]["data"]
    info = d.pop("_lint_move", {})
    tokens = info.get("tokens", [])
    target = info.get("target")
    if not tokens or not target:
        from .router import render_templates_home
        render_templates_home(chat_id)
        return
    src = d.setdefault("templates", {}).setdefault("__global__", {}).setdefault("templates", {})
    dst = d.setdefault("templates", {}).setdefault(target, {"templates": {}, "collages": []}).setdefault("templates", {})
    for t in tokens:
        dst[t] = src.pop(t)
    audit.add_event(section="layouts.numbers", action="move", scope=f"global->{target}", entity=",".join(tokens))
    from .router import render_templates_home
    render_templates_home(chat_id)


def _find_merch_key(d: dict, name_ru: str) -> str | None:
    for mk, info in d.get("merch", {}).items():
        if info.get("name_ru") == name_ru:
            return mk
    return None
