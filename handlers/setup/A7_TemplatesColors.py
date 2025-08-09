\
    # -*- coding: utf-8 -*-
    from telebot import types
    from .core import WIZ, edit

    def _render_specific(chat_id: int, mk: str, num: str):
        colors = WIZ[chat_id]["data"]["merch"][mk]["colors"]
        allowed = set(WIZ[chat_id]["data"]["templates"][mk]["templates"].setdefault(num, {"allowed_colors": []}).get("allowed_colors", []))
        kb = types.InlineKeyboardMarkup(row_width=3)
        for ck, info in colors.items():
            mark = "✓" if ck in allowed else "·"
            kb.add(types.InlineKeyboardButton(f"{info['name_ru']} {mark}", callback_data=f"setup:tmpl_color_toggle:{mk}:{num}:{ck}"))
        kb.add(types.InlineKeyboardButton("Далее →", callback_data=f"setup:tmpl_color_next:{mk}:{num}"))
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="setup:tmpls"))
        edit(chat_id, f"Шаг 3.2/4. Макет <b>{num}</b> ({WIZ[chat_id]['data']['merch'][mk]['name_ru']}): выберите <b>несколько цветов</b>, где он допустим.", kb)
        WIZ[chat_id]["stage"] = "tmpl_colors"

    def _find_first(chat_id: int):
        d = WIZ[chat_id]["data"]
        for mk, tinfo in d.get("templates", {}).items():
            for num, _ in tinfo.get("templates", {}).items():
                return mk, num
        return None, None

    def render_for_next_template(chat_id: int):
        mk, num = _find_first(chat_id)
        if not mk:
            from .A8_TemplatesCollages import ask_collages_or_next
            ask_collages_or_next(chat_id); return
        _render_specific(chat_id, mk, num)

    def toggle_color(chat_id: int, mk: str, num: str, ck: str):
        info = WIZ[chat_id]["data"]["templates"][mk]["templates"].setdefault(num, {"allowed_colors": []})
        if ck in info["allowed_colors"]:
            info["allowed_colors"].remove(ck)
        else:
            info["allowed_colors"].append(ck)
        _render_specific(chat_id, mk, num)

    def next_template(chat_id: int, mk: str, num: str):
        d = WIZ[chat_id]["data"]
        nums_sorted = sorted(d["templates"][mk]["templates"].keys(), key=lambda x: (len(x), x))
        # найти следующий номер в этом мерче
        found_cur = False
        for n in nums_sorted:
            if found_cur:
                _render_specific(chat_id, mk, n); return
            if n == num:
                found_cur = True
        # перейти к первому номеру следующего мерча
        for mk2, tinfo in d.get("templates", {}).items():
            if mk2 == mk: continue
            nums2 = sorted(tinfo.get("templates", {}).keys(), key=lambda x: (len(x), x))
            if nums2:
                _render_specific(chat_id, mk2, nums2[0]); return
        from .A8_TemplatesCollages import ask_collages_or_next
        ask_collages_or_next(chat_id)
