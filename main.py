# -*- coding: utf-8 -*-
import time, logging, sys
from requests.exceptions import ReadTimeout, ConnectionError
from bot import bot
from router import register_routes

log = logging.getLogger("runner")

def run_bot() -> None:
    register_routes()
    try:
        bot.get_me()
    except Exception:
        print("❌ Telegram auth failed. Check TG_Token.")
        sys.exit(1)
    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=20,
                long_polling_timeout=40
            )
        except (ReadTimeout, ConnectionError) as net_err:
            log.warning("🌐 Сетевой тайм-аут (%s). Повтор через 10 c…", net_err)
            time.sleep(10)
        except Exception as e:
            log.exception("💥 Необработанное исключение polling: %s", e)
            time.sleep(10)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("Bot started.")
    run_bot()
