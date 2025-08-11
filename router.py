# -*- coding: utf-8 -*-
# Регистрация всех хэндлеров (импорты регистрируют декораторы)
from handlers import start, bind, order_flow, settings, errors, debug  # noqa: F401
from bot import bot  # если уже есть — оставьте как было            # noqa: F401
from modules.router import register_module_routes

def register_routes():
    # Базовые обработчики
    from handlers import start, bind  # noqa: F401

    # Мастер настройки: достаточно импортировать модуль,
    # его декораторы сами зарегистрируют хэндлеры.
    from handlers.setup import router as setup_router  # noqa: F401

    # Опционально: если у вас есть другие хэндлеры (например, оформление заказов),
    # импортируйте их здесь. Если модуля нет — просто пропускаем.
    try:
        from handlers import order_flow  # noqa: F401
    except ImportError:
        pass
