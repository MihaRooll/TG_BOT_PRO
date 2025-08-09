# -*- coding: utf-8 -*-
import logging
from telebot import TeleBot, apihelper
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s"
)
logger = logging.getLogger("fon_bot_setup")

apihelper.CONNECT_TIMEOUT = config.CONNECT_TIMEOUT
apihelper.READ_TIMEOUT = config.READ_TIMEOUT
apihelper.SESSION_TIME_TO_LIVE = config.SESSION_TTL

bot = TeleBot(config.BOT_TOKEN, parse_mode="HTML")
