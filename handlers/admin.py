# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.roles import get_role, list_roles, set_role

# simple state storage for role assignment
_ADMIN_STATE = {}


def _ensure_admin(chat_id: int) -> bool:
    return get_role(chat_id) == "admin"


def _home(chat_id: int, message_id: int | None = None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📋 Список ролей", callback_data="admin:roles"))
    kb.add(types.InlineKeyboardButton("➕ Назначить роль", callback_data="admin:assign"))
    if message_id:
        bot.edit_message_text("Админка", chat_id, message_id, reply_markup=kb)
    else:
        bot.send_message(chat_id, "Админка", reply_markup=kb)


@bot.message_handler(commands=["admin"])
def admin_cmd(message: types.Message):
    if not _ensure_admin(message.chat.id):
        return
    _home(message.chat.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:"))
def admin_router(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    if not _ensure_admin(chat_id):
        bot.answer_callback_query(c.id)
        return
    cmd = c.data.split(":", 1)[1]
    if cmd == "roles":
        roles = list_roles()
        text = "\n".join(f"{uid}: {role}" for uid, role in roles.items()) or "Пока нет ролей"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin:home"))
        bot.edit_message_text(text, chat_id, c.message.message_id, reply_markup=kb)
    elif cmd == "assign":
        _ADMIN_STATE[chat_id] = "assign"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin:home"))
        bot.edit_message_text("Введите: <chat_id> <role>", chat_id, c.message.message_id, reply_markup=kb)
    else:
        _home(chat_id, c.message.message_id)
    bot.answer_callback_query(c.id)


@bot.message_handler(func=lambda m: _ADMIN_STATE.get(m.chat.id) == "assign")
def admin_assign(m: types.Message):
    chat_id = m.chat.id
    if not _ensure_admin(chat_id):
        return
    try:
        uid_str, role = m.text.strip().split(None, 1)
        set_role(int(uid_str), role.strip())
        bot.send_message(chat_id, "Роль назначена")
    except Exception:
        bot.send_message(chat_id, "Неверный формат")
    finally:
        _ADMIN_STATE.pop(chat_id, None)
        _home(chat_id)
