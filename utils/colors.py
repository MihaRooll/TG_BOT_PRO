# -*- coding: utf-8 -*-
"""Utility helpers for color name mapping."""

COLOR_MAP_RU = {
    "white": "Белый",
    "black": "Чёрный",
    "red": "Красный",
    "blue": "Синий",
    "green": "Зелёный",
    "yellow": "Жёлтый",
    "purple": "Фиолетовый",
    "orange": "Оранжевый",
    "pink": "Розовый",
    "gray": "Серый",
    "brown": "Коричневый",
}


def color_ru(code: str) -> str:
    """Return Russian display name for a color code."""
    return COLOR_MAP_RU.get((code or "").lower(), code)
