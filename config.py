# -*- coding: utf-8 -*-
import os

# === ВНИМАНИЕ: По просьбе пользователя ключи и токены захардкожены в проекте ===
BOT_TOKEN = "6808182455:AAHbqvbj37m2x8Yu_N4MapqRk0gqlj7_EfY"
# Бэкапный ID общего чата (если не выполнен /bind_here). Может быть None — тогда попросим привязать.
ADMIN_CHAT_ID = -1002076884561

# Сетевые таймауты к Telegram Bot API
CONNECT_TIMEOUT = 15
READ_TIMEOUT = 90
SESSION_TTL = 300

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
MAKET_DIR = os.path.join(BASE_DIR, "Maket")
