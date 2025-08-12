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


@bot.message_handler(commands=["promo_test"])
def cmd_promo(message: types.Message):
    if not _require_admin(message):
        return
    bot.send_message(message.chat.id, "ℹ️ Топ пользователей по заказам недоступен.")


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
    if not _require_admin(message):
        return
    bot.send_message(message.chat.id, "Админка в разработке.")


@bot.message_handler(commands=["admin_add"])
def cmd_admin_add(message: types.Message):
    if not is_superadmin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав")
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    add_admin(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в ADMINS")


@bot.message_handler(commands=["admin_del"])
def cmd_admin_del(message: types.Message):
    if not is_superadmin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав")
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    del_admin(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из ADMINS")


@bot.message_handler(commands=["admin_list"])
def cmd_admin_list(message: types.Message):
    if not is_superadmin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав")
        return
    admins = ", ".join(map(str, get_admins())) or "—"
    supers = ", ".join(map(str, SUPERADMINS))
    bot.reply_to(message, f"SUPERADMINS: {supers}\nADMINS: {admins}")


@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def cmd_unknown(message: types.Message):
    bot.reply_to(message, "❔ Команда недоступна на этом проекте")
