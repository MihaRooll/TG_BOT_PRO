# -*- coding: utf-8 -*-
"""Регистрирует все хэндлеры бота."""

from bot import bot  # noqa: F401  # ensure bot is created
from modules.router import register_module_routes


def register_routes() -> None:
    """Импортирует модули с декораторами хэндлеров."""
    from handlers import start, errors  # noqa: F401

    # Мастер настройки
    from handlers.setup import router as setup_router  # noqa: F401

    # Дополнительные обработчики (опционально)
    try:  # pragma: no cover - зависит от наличия модулей
        from handlers import order_flow  # noqa: F401
    except ImportError:
        pass

    register_module_routes()


# Автоматически регистрируем при импорте модуля
register_routes()

