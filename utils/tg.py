# -*- coding: utf-8 -*-
from telebot import TeleBot, types

def safe_delete(bot: TeleBot, chat_id: int, message_id: int | None) -> None:
    if not message_id:
        return
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def safe_edit_message(bot: TeleBot, chat_id: int, message_id: int, text: str,
                      markup: types.InlineKeyboardMarkup | None = None) -> None:
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        pass


def set_chat_commands(bot: TeleBot, chat_id: int) -> None:
    """Configure the command menu for a specific chat based on its rights."""
    from services.roles import get_role

    role = get_role(chat_id)
    cmds = [types.BotCommand("start", "Старт")]
    if role in ("promo", "coord", "admin"):
        cmds.append(types.BotCommand("order", "Заказ"))
    if role in ("coord", "admin"):
        cmds.append(types.BotCommand("setup", "Настройка"))
    if role == "admin":
        cmds.append(types.BotCommand("admin", "Админка"))

    bot.set_my_commands(cmds, scope=types.BotCommandScopeChat(chat_id))
