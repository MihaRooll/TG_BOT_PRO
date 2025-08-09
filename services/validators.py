# -*- coding: utf-8 -*-
import re
from typing import Tuple
from services.settings import get_settings

# Возвращает regex-паттерн для текста с учётом правил настроек
def get_text_pattern() -> re.Pattern:
    s = get_settings()
    rules = s.get("text_rules", {})
    allow_lat = rules.get("allow_latin", True)
    allow_cyr = rules.get("allow_cyrillic", False)
    allow_space = rules.get("allow_space", True)

    parts = []
    if allow_lat:
        parts.append("A-Za-z")
    if allow_cyr:
        # Добавляем Ёё
        parts.append("А-Яа-яЁё")
    if allow_space:
        parts.append(" ")

    if not parts:
        # если по ошибке все запрещено — разрешим только латиницу
        parts = ["A-Za-z"]
    charclass = "".join(parts)
    return re.compile(rf"^[{charclass}]+$")

def validate_text(text: str) -> Tuple[bool, str]:
    s = get_settings()
    max_len = s.get("text_rules", {}).get("max_text_len", 12)
    if len(text) == 0 or len(text) > max_len:
        return False, f"Длина текста должна быть от 1 до {max_len}."
    if not get_text_pattern().fullmatch(text):
        return False, "Текст допускает только буквы выбранных алфавитов и пробелы."
    return True, ""

def validate_number(num: str) -> Tuple[bool, str]:
    s = get_settings()
    max_num = s.get("text_rules", {}).get("max_number", 99)
    if not num.isdigit():
        return False, "Номер должен состоять только из цифр."
    if int(num) < 0 or int(num) > max_num:
        return False, f"Номер должен быть в диапазоне 0..{max_num}."
    return True, ""
