# -*- coding: utf-8 -*-
"""Редактор цветовых допусков для макетов (шаг 3.2/4)."""

from telebot import types
import regex as re

from .core import WIZ, edit


def _scheme(chat_id: int, mk: str) -> str:
    """Сформировать блок схемы «цвет → макеты» для данного мерча."""
    d = WIZ[chat_id]["data"]
    colors = d["merch"][mk]["colors"]
    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    lines = []
    for ck, info in colors.items():
        allowed = [n for n, tinf in sorted(tpls.items(), key=lambda x: (len(x[0]), x[0])) if ck in tinf.get("allowed_colors", [])]
        lst = ", ".join(allowed) if allowed else "—"
        lines.append(f"├─ {info['name_ru']} | Макеты: {lst}")
    if lines:
        lines[-1] = lines[-1].replace("├", "└", 1)
    return "\n".join(lines)


def _render(chat_id: int, mk: str, num: str) -> None:
    d = WIZ[chat_id]["data"]
    merch_name = d["merch"][mk]["name_ru"]
    tpls = d.setdefault("templates", {}).setdefault(mk, {"templates": {}, "collages": []})["templates"]
    info = tpls.setdefault(num, {"allowed_colors": []})
    scheme = _scheme(chat_id, mk)

    kb = types.InlineKeyboardMarkup(row_width=2)
    for ck, cinfo in d["merch"][mk]["colors"].items():
        mark = "✅" if ck in info.get("allowed_colors", []) else "□"
        kb.add(
            types.InlineKeyboardButton(
                f"{cinfo['name_ru']} {mark}",
                callback_data=f"setup:tmpl_color_toggle:{mk}:{num}:{ck}",
            )
        )
    kb.add(types.InlineKeyboardButton("Добавить макеты…", callback_data=f"setup:tmpl_color_add:{mk}:{num}"))
    kb.add(types.InlineKeyboardButton("Очистить всё", callback_data=f"setup:tmpl_color_clear:{mk}:{num}"))
    kb.add(types.InlineKeyboardButton("Готово", callback_data=f"setup:tmpl_color_next:{mk}:{num}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))

    edit(
        chat_id,
        (
            f"Шаг 3.2/4. Макет {num} ({merch_name}): выберите несколько цветов, где он допустим.\n\n"
            f"🎨 Цвета допуска для макета {num} — {merch_name}\n{scheme}"
        ),
        kb,
    )
    WIZ[chat_id]["stage"] = "tmpl_colors"


def _parse_layouts(text: str) -> list[str]:
    """Разобрать строки вида ``1,2 A1-A3`` в список токенов."""
    parts = re.split(r"[\s,]+", text.strip())
    out = []
    for p in parts:
        if not p:
            continue
        p = p.upper()
        m = re.fullmatch(r"(A?)(\d+)-(A?)(\d+)", p)
        if m:
            pref1, start, pref2, end = m.groups()
            if pref1 == pref2:
                a, b = int(start), int(end)
                pref = pref1
                for i in range(a, b + 1):
                    out.append(f"{pref}{i}")
            continue
        out.append(p)
    return out


def _apply_defaults(chat_id: int, token: str, mk: str, cur_colors: list[str]) -> None:
    """Добавить макет по умолчанию согласно правилам."""
    d = WIZ[chat_id]["data"]
    tpls = d.setdefault("templates", {})
    merch = d.get("merch", {})

    if re.fullmatch(r"\d+", token):
        # глобально для всех мерчей и цветов
        for mk_key, mk_info in merch.items():
            tpl = tpls.setdefault(mk_key, {"templates": {}, "collages": []})["templates"]
            info = tpl.setdefault(token, {"allowed_colors": []})
            for ck in mk_info.get("colors", {}):
                if ck not in info["allowed_colors"]:
                    info["allowed_colors"].append(ck)
        return

    if re.fullmatch(r"A\d+", token, re.I):
        mk_key = "tshirt"
        if mk_key in merch:
            tpl = tpls.setdefault(mk_key, {"templates": {}, "collages": []})["templates"]
            info = tpl.setdefault(token.upper(), {"allowed_colors": []})
            info["allowed_colors"] = []
            if "black" in merch[mk_key].get("colors", {}):
                info["allowed_colors"].append("black")
        return

    # иначе добавляем в текущий мерч с выбранными цветами
    tpl = tpls.setdefault(mk, {"templates": {}, "collages": []})["templates"]
    info = tpl.setdefault(token, {"allowed_colors": []})
    for ck in cur_colors:
        if ck not in info["allowed_colors"]:
            info["allowed_colors"].append(ck)


def ask_add_many(chat_id: int, mk: str, num: str) -> None:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"setup:tmpl_color_toggle:{mk}:{num}:__noop"))
    edit(chat_id, "Введите номера макетов (списки, диапазоны):", kb)
    WIZ[chat_id]["stage"] = f"tmpl_color_add:{mk}:{num}"


def handle_add_many(chat_id: int, mk: str, num: str, text: str) -> None:
    d = WIZ[chat_id]["data"]
    cur_colors = d["templates"][mk]["templates"].setdefault(num, {"allowed_colors": []})["allowed_colors"]
    for token in _parse_layouts(text):
        _apply_defaults(chat_id, token, mk, cur_colors)
    _render(chat_id, mk, num)


def clear_all(chat_id: int, mk: str, num: str) -> None:
    d = WIZ[chat_id]["data"]
    d["templates"][mk]["templates"].setdefault(num, {"allowed_colors": []})["allowed_colors"] = []
    _render(chat_id, mk, num)


def start_for_merchs(chat_id: int, mks: list[str], done_cb=None) -> None:
    d = WIZ[chat_id]["data"]
    d["_tmpl_color_mks"] = mks
    d["_tmpl_color_done"] = done_cb
    render_for_next_template(chat_id)


def render_for_next_template(chat_id: int) -> None:
    d = WIZ[chat_id]["data"]
    scope = d.get("_tmpl_color_mks")
    if scope is None:
        scope = list(d.get("templates", {}).keys())
    for mk in scope:
        tinfo = d.get("templates", {}).get(mk, {})
        nums = sorted(tinfo.get("templates", {}).keys(), key=lambda x: (len(x), x))
        if nums:
            _render(chat_id, mk, nums[0])
            return
    done = d.pop("_tmpl_color_done", None)
    if callable(done):
        done(chat_id)
    else:
        from .A8_TemplatesCollages import start_for_merchs
        mks = list(d.get("merch", {}).keys())
        start_for_merchs(chat_id, mks)


def toggle_color(chat_id: int, mk: str, num: str, ck: str) -> None:
    if ck == "__noop":
        _render(chat_id, mk, num)
        return
    info = WIZ[chat_id]["data"]["templates"][mk]["templates"].setdefault(num, {"allowed_colors": []})
    if ck in info["allowed_colors"]:
        info["allowed_colors"].remove(ck)
    else:
        info["allowed_colors"].append(ck)
    _render(chat_id, mk, num)


def next_template(chat_id: int, mk: str, num: str) -> None:
    d = WIZ[chat_id]["data"]
    scope = d.get("_tmpl_color_mks")
    nums_sorted = sorted(d["templates"][mk]["templates"].keys(), key=lambda x: (len(x), x))
    found = False
    for n in nums_sorted:
        if found:
            _render(chat_id, mk, n)
            return
        if n == num:
            found = True
    if scope is None:
        scope = list(d.get("templates", {}).keys())
    for mk2 in scope:
        if mk2 == mk:
            continue
        nums2 = sorted(d.get("templates", {}).get(mk2, {}).get("templates", {}).keys(), key=lambda x: (len(x), x))
        if nums2:
            _render(chat_id, mk2, nums2[0])
            return
    done = d.pop("_tmpl_color_done", None)
    if callable(done):
        done(chat_id)
    else:
        from .A8_TemplatesCollages import start_for_merchs
        mks = list(d.get("merch", {}).keys())
        start_for_merchs(chat_id, mks)


