# -*- coding: utf-8 -*-
"""Command handlers and role management utilities."""

from telebot import types

from bot import bot
from services.settings import (
    is_admin,
    is_superadmin,
    add_admin,
    del_admin,
    get_admins,
    add_coordinator,
    del_coordinator,
    get_coordinators,
    refresh_promo_cache,
    user_roles,
    has_access,
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


def _require_super(message: types.Message) -> bool:
    if not is_superadmin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав")
        return False
    return True


# ---------------------------------------------------------------------------
# Basic commands

@bot.message_handler(commands=["stock"], func=has_access)
def cmd_stock(message: types.Message):
    if not _require_admin(message):
        return
    bot.send_message(
        message.chat.id,
        "ℹ️ Быстрая корректировка остатков пока не реализована.",
    )


@bot.message_handler(commands=["promo_test"], func=has_access)
def cmd_promo(message: types.Message):
    if not _require_admin(message):
        return
    bot.send_message(message.chat.id, "ℹ️ Топ пользователей по заказам недоступен.")


@bot.message_handler(commands=["analytics"], func=has_access)
def cmd_analytics(message: types.Message):
    if not _require_admin(message):
        return
    bot.send_message(message.chat.id, "ℹ️ Аналитика ещё не реализована.")


@bot.message_handler(commands=["settings"], func=has_access)
def cmd_settings(message: types.Message):
    bot.send_message(message.chat.id, "🔧 Настройки доступны через главное меню.")


@bot.message_handler(commands=["admin"], func=has_access)
def cmd_admin(message: types.Message):
    if not _require_admin(message):
        return
    bot.send_message(message.chat.id, "Админка в разработке.")


# ---------------------------------------------------------------------------
# Admin management

@bot.message_handler(commands=["admin_add"], func=has_access)
def cmd_admin_add(message: types.Message):
    if not _require_super(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    add_admin(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в ADMINS")


@bot.message_handler(commands=["admin_del"], func=has_access)
def cmd_admin_del(message: types.Message):
    if not _require_super(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    del_admin(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из ADMINS")


@bot.message_handler(commands=["admin_list"], func=has_access)
def cmd_admin_list(message: types.Message):
    if not _require_super(message):
        return
    admins = ", ".join(map(str, get_admins())) or "—"
    supers = ", ".join(map(str, SUPERADMINS))
    bot.reply_to(message, f"SUPERADMINS: {supers}\nADMINS: {admins}")


# ---------------------------------------------------------------------------
# Coordinator management

@bot.message_handler(commands=["coord_add"], func=has_access)
def cmd_coord_add(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    add_coordinator(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} добавлен в COORDINATORS")


@bot.message_handler(commands=["coord_del"], func=has_access)
def cmd_coord_del(message: types.Message):
    if not _require_admin(message):
        return
    uid = _extract_uid(message)
    if uid is None:
        bot.reply_to(message, "Укажите user_id")
        return
    del_coordinator(uid)
    bot.reply_to(message, f"✅ Пользователь {uid} удалён из COORDINATORS")


@bot.message_handler(commands=["coord_list"], func=has_access)
def cmd_coord_list(message: types.Message):
    if not _require_admin(message):
        return
    coords = ", ".join(map(str, get_coordinators())) or "—"
    bot.reply_to(message, f"COORDINATORS: {coords}")


# ---------------------------------------------------------------------------
# Promo cache and diagnostics

@bot.message_handler(commands=["promo_refresh"], func=has_access)
def cmd_promo_refresh(message: types.Message):
    if not _require_admin(message):
        return
    refresh_promo_cache()
    bot.reply_to(message, "🔄 PROMO обновлён")


@bot.message_handler(commands=["whoami"])
def cmd_whoami(message: types.Message):
    uid = message.from_user.id
    roles = user_roles(uid)
    gated = bool(roles)
    bot.reply_to(message, str({"id": uid, "roles": roles, "gated": gated}))


# ---------------------------------------------------------------------------

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/") and has_access(m.from_user.id))
def cmd_unknown(message: types.Message):
    bot.reply_to(message, "❔ Команда недоступна на этом проекте")

