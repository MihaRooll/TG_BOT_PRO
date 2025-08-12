# -*- coding: utf-8 -*-
from telebot import types
from bot import bot

try:
    from handlers.order_flow import ORD
except Exception:
    ORD = {}
try:
    from handlers.setup.core import WIZ
except Exception:
    WIZ = {}


@bot.message_handler(func=lambda m: True, content_types=['text','photo','document','sticker','video','voice','location','contact'])
def _log_unhandled_message(m: types.Message):
    state = ORD.get(m.chat.id, {}).get('step') or WIZ.get(m.chat.id, {}).get('stage')
    payload = m.text if m.content_type == 'text' else m.content_type
    reason = "unknown command" if isinstance(payload, str) and payload.startswith('/') else "no handler"
    print(f"[unhandled message] chat={m.chat.id} state={state} payload={payload} reason={reason}")


@bot.callback_query_handler(func=lambda c: True)
def _log_unhandled_callback(c: types.CallbackQuery):
    state = ORD.get(c.message.chat.id, {}).get('step') or WIZ.get(c.message.chat.id, {}).get('stage')
    print(f"[unhandled callback] chat={c.message.chat.id} state={state} data={c.data} reason=no handler")
