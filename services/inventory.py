# -*- coding: utf-8 -*-
from typing import Dict, Any
from repositories.files import load_json, save_json

INV_MERCH = "inventory_merch.json"        # {merch:{color:{sizes:{size:qty}}}}
INV_LETTERS = "inventory_letters.json"    # {text_color:{letters:{'A':qty, 'Б':qty, ...}}}
INV_NUMBERS = "inventory_numbers.json"    # {text_color:{numbers:{'0':qty, ...}}}
INV_TEMPLATES = "inventory_templates.json"# {merch:{templates:{num:{qty:int}}}}

def get_merch_inv() -> Dict[str, Any]: return load_json(INV_MERCH) or {}
def get_letters_inv() -> Dict[str, Any]: return load_json(INV_LETTERS) or {}
def get_numbers_inv() -> Dict[str, Any]: return load_json(INV_NUMBERS) or {}
def get_templates_inv() -> Dict[str, Any]: return load_json(INV_TEMPLATES) or {}

def save_merch_inv(d: Dict[str, Any]): save_json(INV_MERCH, d)
def save_letters_inv(d: Dict[str, Any]): save_json(INV_LETTERS, d)
def save_numbers_inv(d: Dict[str, Any]): save_json(INV_NUMBERS, d)
def save_templates_inv(d: Dict[str, Any]): save_json(INV_TEMPLATES, d)

# --- helpers to decrement stock on order ---
def dec_size(merch: str, color: str, size: str, qty: int=1) -> None:
    inv = get_merch_inv()
    if inv.get(merch, {}).get(color, {}).get("sizes", {}).get(size, 0) >= qty:
        inv[merch][color]["sizes"][size] -= qty
        save_merch_inv(inv)

def dec_letter(text_color: str, text: str) -> None:
    inv = get_letters_inv()
    if not text or text == "Без текста":
        return
    t = text.replace(" ", "")
    for ch in t:
        cur = inv.get(text_color, {}).get("letters", {}).get(ch.upper())
        if isinstance(cur, int) and cur > 0:
            inv[text_color]["letters"][ch.upper()] = cur - 1
    save_letters_inv(inv)

def dec_number(text_color: str, number: str) -> None:
    inv = get_numbers_inv()
    if not number or number == "Без номера":
        return
    for d in number:
        cur = inv.get(text_color, {}).get("numbers", {}).get(d)
        if isinstance(cur, int) and cur > 0:
            inv[text_color]["numbers"][d] = cur - 1
    save_numbers_inv(inv)

def dec_template(merch: str, template_num: str) -> None:
    inv = get_templates_inv()
    cur = inv.get(merch, {}).get("templates", {}).get(template_num, {}).get("qty")
    if isinstance(cur, int) and cur > 0:
        inv[merch]["templates"][template_num]["qty"] = cur - 1
        save_templates_inv(inv)
