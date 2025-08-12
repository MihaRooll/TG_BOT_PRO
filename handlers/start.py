# -*- coding: utf-8 -*-
from telebot import types
from bot import bot
from services.settings import get_settings
from utils.tg import set_chat_commands

@bot.message_handler(commands=["start","help"])
def start_cmd(message: types.Message):
    chat_id = message.chat.id
    set_chat_commands(bot, chat_id)

    # сбрасываем незавершённые заказы
    try:
        from handlers.order_flow import ORD  # локальный импорт, чтобы избежать цикла
        ORD.pop(chat_id, None)
    except Exception:
        pass

    s = get_settings()
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not s.get("configured"):
        kb.add(types.InlineKeyboardButton("🔧 Запустить мастер настройки", callback_data="setup:init"))
        kb.add(types.InlineKeyboardButton("ℹ️ Привязка общего чата", callback_data="setup:bind_hint"))
        bot.send_message(chat_id, "<b>Мастер настройки</b> — нажмите кнопку ниже 👇", reply_markup=kb, parse_mode="HTML")
    else:
        kb.add(types.InlineKeyboardButton("🛒 Сделать заказ", callback_data="order:start"))
        kb.add(types.InlineKeyboardButton("🔧 Настройки", callback_data="settings_open"))
        bot.send_message(chat_id, "Бот настроен. Выберите действие:", reply_markup=kb)


@bot.message_handler(commands=["order"])
def order_cmd(message: types.Message):
    chat_id = message.chat.id
    s = get_settings()
    if not s.get("configured"):
        bot.send_message(chat_id, "Бот не настроен. Нажмите /start и пройдите мастер.")
        return
    from handlers.order_flow import ORD, _prompt_merch
    msg = bot.send_message(chat_id, "...")
    ORD[chat_id] = {"mid": msg.message_id}
    _prompt_merch(chat_id)
