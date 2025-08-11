# -*- coding: utf-8 -*-
from telebot import TeleBot, types
from typing import List

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


COLOR_NAMES_RU = {
    "white": "Белый",
    "black": "Чёрный",
    "gold": "Золотой",
    "silver": "Серебряный",
    "red": "Красный",
    "blue": "Синий",
    "green": "Зелёный",
    "yellow": "Жёлтый",
    "purple": "Фиолетовый",
    "orange": "Оранжевый",
    "pink": "Розовый",
    "turquoise": "Бирюзовый",
    "maroon": "Бордовый",
    "gray": "Серый",
    "brown": "Коричневый",
}

COLOR_RU_TO_EN = {v: k for k, v in COLOR_NAMES_RU.items()}

def _slugify(name: str, used: List[str]) -> str:
    trans = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
        'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    s = name.strip().lower()
    s = "".join(trans.get(ch, ch) for ch in s)
    import re
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "item"
    base = s
    i = 2
    while s in used:
        s = f"{base}-{i}"
        i += 1
    return s


def color_key_from_ru(name_ru: str, used: List[str]) -> str:
    """Generate an english key for a russian color name, ensuring uniqueness."""
    key = COLOR_RU_TO_EN.get(name_ru.strip())
    if not key:
        key = _slugify(name_ru, used)
    base = key
    i = 2
    while key in used:
        key = f"{base}-{i}"
        i += 1
    return key


def register_color_name(key: str, name_ru: str) -> None:
    COLOR_NAMES_RU.setdefault(key, name_ru)


def color_name_ru(key: str) -> str:
    """Return Russian human-friendly name for a color key."""
    from services.settings import get_settings
    if key in COLOR_NAMES_RU:
        return COLOR_NAMES_RU[key]
    return get_settings().get("color_names", {}).get(key, key)


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
