# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services import audit
from services.settings import (
    is_admin,
    is_superadmin,
    add_admin,
    del_admin,
    get_admins,
    SUPERADMINS,
    add_coordinator,
    del_coordinator,
    get_coordinators,
    add_promoter,
    del_promoter,
    get_promoters,
)
from handlers.setup import A9_InventorySizes as INV
from handlers.setup.core import ensure, WIZ

import io
import csv
import json
import html


def _extract_uid(message: types.Message) -> int | None:
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    parts = (message.text or "").split()
    if len(parts) > 1:
        try:
            return int(parts[1])
        except Exception:
            return None
    return None


def _require_admin(message: types.Message) -> bool:
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав")
        return False
    return True


@bot.message_handler(commands=["stock"])
def cmd_stock(message: types.Message):
    if not _require_admin(message):
        return
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "...")
    ensure(chat_id, msg.message_id)
    WIZ[chat_id]["flow_origin"] = "stock"
    INV.open_inventory_home(chat_id)


@bot.message_handler(commands=["whoami"])
def cmd_whoami(message: types.Message):
    u = message.from_user
    bot.reply_to(
        message,
        f"ID: {u.id}\nUsername: @{u.username or '—'}\nName: {u.first_name} {u.last_name or ''}"
    )


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "🏠 Главное меню")
    ensure(chat_id, msg.message_id)
    WIZ[chat_id] = {"anchor_id": msg.message_id, "stage": "home", "data": {}, "_sig": None, "flow_origin": None}


@bot.message_handler(commands=["promo_stats"])
def cmd_promo_stats(message: types.Message):
    if not _require_admin(message):
        return
    from services.orders import get_all_user_orders

    stats = get_all_user_orders()
    if not stats:
        bot.send_message(message.chat.id, "Нет оформленных заказов")
        return
    lines = [f"{uid}: {cnt}" for uid, cnt in sorted(stats.items(), key=lambda i: i[1], reverse=True)]
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=["my_orders"])
def cmd_my_orders(message: types.Message):
    from services.orders import get_user_orders

    cnt = get_user_orders(message.from_user.id)
    bot.send_message(message.chat.id, f"Вы оформили {cnt} заказ(ов)")


@bot.message_handler(commands=["analytics"])
def cmd_analytics(message: types.Message):
    if not _require_admin(message):
        return
    bot.send_message(message.chat.id, "ℹ️ Аналитика ещё не реализована.")


@bot.message_handler(commands=["settings"])
def cmd_settings(message: types.Message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "🔧 Настройки")
    ensure(chat_id, msg.message_id)
    WIZ[chat_id] = {"anchor_id": msg.message_id, "stage": "home", "data": {}, "_sig": None, "flow_origin": None}


@bot.message_handler(commands=["admin"])
def cmd_admin(message: types.Message):
    if not get_admins():
        add_admin(message.from_user.id)
        bot.reply_to(message, "✅ Вы назначены главным администратором")
        return
    if not _require_admin(message):
        return
    bot.reply_to(
        message,
        "\n".join(
            [
                "/admin_add <id> — добавить администратора",
                "/admin_del <id> — удалить администратора",
                "/admin_list — список администраторов",
                "/coord_add <id> — добавить координатора",
                "/coord_del <id> — удалить координатора",
                "/coord_list — список координаторов",
                "/promo_add <id> — добавить промоутера",
                "/promo_del <id> — удалить промоутера",
                "/promo_list — список промоутеров",
                "/promo_stats — заказы по пользователям",
            ]
        ),
    )


@bot.message_handler(commands=["admin_add"])
def cmd_admin_add(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    before = get_admins()
    add_admin(uid)
    after = get_admins()
    audit.add_event(
        user=message.from_user,
        section="roles.admin",
        action="add",
        entity=f"user:{uid}",
        before={"admins": before},
        after={"admins": after},
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в ADMINS")


@bot.message_handler(commands=["admin_del"])
def cmd_admin_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    before = get_admins()
    del_admin(uid)
    after = get_admins()
    audit.add_event(
        user=message.from_user,
        section="roles.admin",
        action="delete",
        entity=f"user:{uid}",
        before={"admins": before},
        after={"admins": after},
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из ADMINS")


@bot.message_handler(commands=["admin_list"])
def cmd_admin_list(message: types.Message):
    if not _require_admin(message):
        return
    admins = ", ".join(map(str, get_admins())) or "—"
    supers = ", ".join(map(str, SUPERADMINS)) or "—"
    audit.add_event(
        user=message.from_user,
        section="roles.admin",
        action="list",
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"SUPERADMINS: {supers}\nADMINS: {admins}")


@bot.message_handler(commands=["coord_add"])
def cmd_coord_add(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    before = get_coordinators()
    add_coordinator(uid)
    after = get_coordinators()
    audit.add_event(
        user=message.from_user,
        section="roles.coordinator",
        action="add",
        entity=f"user:{uid}",
        before={"coordinators": before},
        after={"coordinators": after},
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в координаторы")


@bot.message_handler(commands=["coord_del"])
def cmd_coord_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    before = get_coordinators()
    del_coordinator(uid)
    after = get_coordinators()
    audit.add_event(
        user=message.from_user,
        section="roles.coordinator",
        action="delete",
        entity=f"user:{uid}",
        before={"coordinators": before},
        after={"coordinators": after},
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из координаторов")


@bot.message_handler(commands=["coord_list"])
def cmd_coord_list(message: types.Message):
    if not _require_admin(message):
        return
    coords = ", ".join(map(str, get_coordinators())) or "—"
    audit.add_event(
        user=message.from_user,
        section="roles.coordinator",
        action="list",
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"Координаторы: {coords}")


@bot.message_handler(commands=["promo_add"])
def cmd_promo_add(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    before = get_promoters()
    add_promoter(uid)
    after = get_promoters()
    audit.add_event(
        user=message.from_user,
        section="roles.promoter",
        action="add",
        entity=f"user:{uid}",
        before={"promoters": before},
        after={"promoters": after},
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в промоутеры")


@bot.message_handler(commands=["promo_del"])
def cmd_promo_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    before = get_promoters()
    del_promoter(uid)
    after = get_promoters()
    audit.add_event(
        user=message.from_user,
        section="roles.promoter",
        action="delete",
        entity=f"user:{uid}",
        before={"promoters": before},
        after={"promoters": after},
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из промоутеров")


@bot.message_handler(commands=["promo_list"])
def cmd_promo_list(message: types.Message):
    if not _require_admin(message):
        return
    promos = ", ".join(map(str, get_promoters())) or "—"
    audit.add_event(
        user=message.from_user,
        section="roles.promoter",
        action="list",
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    bot.reply_to(message, f"Промоутеры: {promos}")


def _render_audit(period: str = "24h", page: int = 0):
    events = audit.query_events(period=period, limit=1000)
    per_page = 20
    total_pages = max(1, (len(events) + per_page - 1) // per_page)
    start = page * per_page
    slice_events = events[start:start + per_page]
    lines = []
    for idx, e in enumerate(slice_events, start=start + 1):
        ts = e.get("ts", "")[:16].replace("T", " ")
        user = e.get("actor_username") or e.get("actor_name") or str(e.get("actor_id"))
        section = e.get("section", "")
        action = e.get("action", "")
        entity = e.get("entity", "") or ""
        scope = f" scope:{e['scope']}" if e.get("scope") else ""
        lines.append(f"#{idx:04d} {ts} @{user} {section}{scope} {action} {entity}")
    body = "\n".join(lines) or "(пусто)"
    text = f"Журнал аудита\n<pre>{html.escape(body)}</pre>"
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Сегодня", callback_data="logroll:p:today:0"),
        types.InlineKeyboardButton("24ч", callback_data="logroll:p:24h:0"),
        types.InlineKeyboardButton("7д", callback_data="logroll:p:7d:0"),
        types.InlineKeyboardButton("Всё", callback_data="logroll:p:all:0"),
    )
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("‹ Назад", callback_data=f"logroll:p:{period}:{page-1}"))
    if page + 1 < total_pages:
        nav.append(types.InlineKeyboardButton("Далее ›", callback_data=f"logroll:p:{period}:{page+1}"))
    if nav:
        markup.row(*nav)
    markup.row(
        types.InlineKeyboardButton("Экспорт CSV", callback_data=f"logroll:export:csv:{period}"),
        types.InlineKeyboardButton("Экспорт JSON", callback_data=f"logroll:export:json:{period}"),
    )
    markup.row(
        types.InlineKeyboardButton("Обновить", callback_data=f"logroll:p:{period}:{page}"),
        types.InlineKeyboardButton("Закрыть", callback_data="logroll:close"),
    )
    return text, markup


@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ("\\log_roll", "/log_roll"))
def cmd_log_roll(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    text, markup = _render_audit()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("logroll:"))
def cb_log_roll(c: types.CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    bot.answer_callback_query(c.id)
    parts = c.data.split(":")
    if parts[1] == "p":
        period = parts[2]
        page = int(parts[3])
        text, markup = _render_audit(period, page)
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="HTML")
    elif parts[1] == "export":
        fmt = parts[2]
        period = parts[3]
        events = audit.query_events(period=period, limit=1000)
        if fmt == "json":
            data = json.dumps(events, ensure_ascii=False, indent=2)
            buf = io.BytesIO(data.encode("utf-8"))
            buf.name = f"audit_{period}.json"
        else:
            buf_txt = io.StringIO()
            writer = csv.writer(buf_txt)
            writer.writerow(["ts", "actor_id", "actor_username", "section", "action", "scope", "entity", "before", "after", "notes", "request_id"])
            for e in events:
                writer.writerow([
                    e.get("ts"),
                    e.get("actor_id"),
                    e.get("actor_username"),
                    e.get("section"),
                    e.get("action"),
                    e.get("scope"),
                    e.get("entity"),
                    json.dumps(e.get("before"), ensure_ascii=False),
                    json.dumps(e.get("after"), ensure_ascii=False),
                    e.get("notes"),
                    e.get("request_id"),
                ])
            buf = io.BytesIO(buf_txt.getvalue().encode("utf-8"))
            buf.name = f"audit_{period}.csv"
        bot.send_document(c.message.chat.id, buf)
    elif parts[1] == "close":
        bot.delete_message(c.message.chat.id, c.message.message_id)


