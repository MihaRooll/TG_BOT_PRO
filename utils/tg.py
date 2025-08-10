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
    from services.settings import get_admin_bind
    import config

    base_cmds = [
        types.BotCommand("start", "Запуск"),
        types.BotCommand("help", "Помощь"),
        types.BotCommand("number", "Цвет цифр"),
    ]

    admin_chat, _ = get_admin_bind()
    if chat_id in (admin_chat, getattr(config, "ADMIN_CHAT_ID", None)):
        base_cmds.extend([
            types.BotCommand("stock", "Остатки"),
            types.BotCommand("bind_here", "Привязать чат"),
        ])

    bot.set_my_commands(base_cmds, scope=types.BotCommandScopeChat(chat_id))
