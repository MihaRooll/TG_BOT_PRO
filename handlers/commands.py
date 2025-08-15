# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
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
    bot.send_message(message.chat.id, "ℹ️ Быстрая корректировка остатков пока не реализована.")


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
    bot.send_message(message.chat.id, "🔧 Настройки доступны через главное меню.")


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
    add_admin(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в ADMINS")


@bot.message_handler(commands=["admin_del"])
def cmd_admin_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    del_admin(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из ADMINS")


@bot.message_handler(commands=["admin_list"])
def cmd_admin_list(message: types.Message):
    if not _require_admin(message):
        return
    admins = ", ".join(map(str, get_admins())) or "—"
    supers = ", ".join(map(str, SUPERADMINS)) or "—"
    bot.reply_to(message, f"SUPERADMINS: {supers}\nADMINS: {admins}")


@bot.message_handler(commands=["coord_add"])
def cmd_coord_add(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    add_coordinator(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в координаторы")


@bot.message_handler(commands=["coord_del"])
def cmd_coord_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    del_coordinator(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из координаторов")


@bot.message_handler(commands=["coord_list"])
def cmd_coord_list(message: types.Message):
    if not _require_admin(message):
        return
    coords = ", ".join(map(str, get_coordinators())) or "—"
    bot.reply_to(message, f"Координаторы: {coords}")


@bot.message_handler(commands=["promo_add"])
def cmd_promo_add(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    add_promoter(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в промоутеры")


@bot.message_handler(commands=["promo_del"])
def cmd_promo_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    del_promoter(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из промоутеров")


@bot.message_handler(commands=["promo_list"])
def cmd_promo_list(message: types.Message):
    if not _require_admin(message):
        return
    promos = ", ".join(map(str, get_promoters())) or "—"
    bot.reply_to(message, f"Промоутеры: {promos}")


