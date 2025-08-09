\
    # -*- coding: utf-8 -*-
    from __future__ import annotations
    from typing import Dict, Any, Tuple, List
    from telebot import types
    from telebot.apihelper import ApiTelegramException
    from bot import bot

    # Состояние мастера по chat_id
    WIZ: Dict[int, Dict[str, Any]] = {}  # {"anchor_id", "stage", "data", "_sig"}

    def ensure(chat_id: int, anchor_id: int | None = None):
        state = WIZ.setdefault(chat_id, {"anchor_id": None, "stage": "home", "data": {}, "_sig": None})
        if anchor_id and not state["anchor_id"]:
            state["anchor_id"] = anchor_id

    def anchor(chat_id: int) -> int:
        return WIZ[chat_id]["anchor_id"]

    def _kb_sig(kb: types.InlineKeyboardMarkup | None) -> Tuple:
        if kb is None:
            return ()
        rows = []
        keyboard = getattr(kb, "keyboard", None) or getattr(kb, "inline_keyboard", None) or []
        for row in keyboard:
            rows.append(tuple((getattr(btn, "text", None), getattr(btn, "callback_data", None), getattr(btn, "url", None)) for btn in row))
        return tuple(rows)

    def edit(chat_id: int, text: str, kb: types.InlineKeyboardMarkup | None):
        """Редактирует только якорное сообщение. Защита от 'message is not modified'."""
        sig = (text, _kb_sig(kb))
        if WIZ.get(chat_id, {}).get("_sig") == sig:
            return
        try:
            bot.edit_message_text(text, chat_id, anchor(chat_id), reply_markup=kb, parse_mode="HTML")
        except ApiTelegramException as e:
            if "message is not modified" in str(e).lower():
                WIZ[chat_id]["_sig"] = sig
                return
            raise
        WIZ[chat_id]["_sig"] = sig

    def slugify(name: str, used: List[str]) -> str:
        trans = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m',
                 'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'',
                 'ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
        s = name.strip().lower()
        s = "".join(trans.get(ch, ch) for ch in s)
        import re
        s = re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "item"
        base = s; i = 2
        while s in used:
            s = f"{base}_{i}"; i += 1
        return s

    def _on_off(ok: bool) -> str:
        return "☑️ ВКЛ" if ok else "☐ ВЫКЛ"

    def merch_tree(data: dict) -> str:
        merch = data.get("merch", {})
        if not merch:
            return "—"
        lines: List[str] = []
        for mk, mi in merch.items():
            lines.append(mi.get("name_ru", mk))
            colors = list(mi.get("colors", {}).values())
            for idx, ci in enumerate(colors):
                branch = "└─" if idx == len(colors) - 1 else "├─"
                lines.append(f"{branch}{ci.get('name_ru', '—')}")
        return "\\n".join(lines)

    def home_text(d: dict) -> str:
        merch = d.get("merch", {})
        colors_ok = bool(merch) and all(m.get("colors") for m in merch.values())
        sizes_ok  = bool(merch) and all(m.get("sizes")  for m in merch.values())
        merch_on = colors_ok and sizes_ok

        feats = d.setdefault("features", {"letters": True, "numbers": True})
        rules = d.setdefault("text_rules", {"allow_latin": True, "allow_cyrillic": False, "allow_space": True, "max_text_len": 12, "max_number": 99})
        pal   = d.setdefault("text_palette", ["white","black"])

        mapping_ok = True
        if merch and pal and (feats.get("letters") or feats.get("numbers")):
            for mk, mi in merch.items():
                for ck in mi.get("colors", {}).keys():
                    if not d.get("text_colors", {}).get(mk, {}).get(ck):
                        mapping_ok = False
        else:
            mapping_ok = False

        tmpls = d.get("templates", {})
        nums_set = any(v.get("templates") for v in tmpls.values())
        coll_count = sum(len(v.get("collages", [])) for v in tmpls.values())

        inv_merch   = d.get("_inv_merch", {})
        inv_letters = d.get("_inv_letters", {}) if feats.get("letters") else True
        inv_numbers = d.get("_inv_numbers", {}) if feats.get("numbers") else True
        inv_tmpls   = d.get("_inv_tmpls", {})   if nums_set else True

        block = []
        block.append("<pre>")
        block.append("<b>🎛 <i>МАСТЕР НАСТРОЙКИ</i></b>\\n")
        block.append(f"<b>1. 🛍 Мерч</b>  <b>[{_on_off(merch_on)}]</b>")
        block.append(f"   ├─ <b>Цвета:</b>   {'✅' if colors_ok else '❌'}")
        block.append(f"   └─ <b>Размеры:</b> {'✅' if sizes_ok  else '❌'}\\n")
        block.append(f"<b>2. 🔤 Буквы</b> <b>[{_on_off(feats.get('letters', False))}]</b>")
        alph = []
        if rules.get('allow_latin'): alph.append("LAT")
        if rules.get('allow_cyrillic'): alph.append("CYR")
        alph_str = "/".join(alph) if alph else "—"
        block.append(f"   ├─ <b>Алфавит:</b> {alph_str} ▸")
        block.append(f"   ├─ <b>Пробел:</b> {'ДА ✔️' if rules.get('allow_space') else 'НЕТ ✖️'}")
        block.append( "   ├─ <b>Пределы:</b>")
        block.append(f"   │   ├─ Текст: ≤{rules.get('max_text_len','—')} симв")
        block.append(f"   │   └─ Номер: ≤{rules.get('max_number','—')}")
        block.append(f"   └─ <b>Палитра:</b> {(' | ').join(pal) if pal else '—'}\\n")
        block.append(f"<b>3. 🔢 Цифры</b> <b>[{_on_off(feats.get('numbers', False))}]</b>")
        block.append(f"   └─ <b>Соответствия:</b>")
        block.append(f"       Мерч/Цвет → Цвет текста {'✅' if mapping_ok else '❌'}\\n")
        block.append(f"<b>4. 🖼 Макеты</b> <b>[{_on_off(nums_set)}]</b>")
        block.append(f"   ├─ <b>Номера:</b> {'✅' if nums_set else '❌'}")
        block.append(f"   └─ <b>Коллажи:</b> {coll_count} {'🟢' if coll_count else '🚫'}\\n")
        block.append(f"<b>5. 📦 Остатки</b> <b>[{_on_off(bool(inv_merch))}]</b>")
        block.append(f"   ├─ <b>Размеры:</b> {'✅' if bool(inv_merch)   else '❌'}")
        block.append(f"   ├─ <b>Буквы:</b>  {'✅' if bool(inv_letters) else '❌'}")
        block.append(f"   ├─ <b>Цифры:</b>  {'✅' if bool(inv_numbers) else '❌'}")
        block.append(f"   └─ <b>Макеты:</b> {'✅' if bool(inv_tmpls)   else '❌'}\\n")
        # дерево мерча
        block.append("<b>Структура мерча</b>")
        block.append(merch_tree(d))
        block.append("</pre>")
        return "\\n".join(block)
