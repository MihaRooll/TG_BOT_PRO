# -*- coding: utf-8 -*-
import os
import sys

def get_bot_token() -> str:
    """Return bot token from environment and ensure it's present."""
    token = os.getenv("TG_Token") or os.getenv("TG_TOKEN")
    if not token:
        print("❌ Bot token is missing. Provide env TG_Token (GitHub Secret).")
        sys.exit(1)
    print("✅ Token loaded from environment")
    return token
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
