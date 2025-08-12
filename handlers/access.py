# -*- coding: utf-8 -*-
"""Catch-all handlers that silently ignore users without access.

The project uses role based gating: only SUPERADMIN, ADMIN, COORDINATOR or
PROMO members may interact with the bot.  Any other user messages or callback
queries are ignored and logged for diagnostics.  The /whoami command is
explicitly excluded so that users can check their roles.
"""

from telebot import types

from bot import bot
from services import settings


@bot.message_handler(func=lambda m: not settings.has_access(m.from_user.id) and not (m.text or "").startswith("/whoami"))
def _ignore_messages(m: types.Message) -> None:
    """Silently swallow messages from unauthorised users."""

    settings.log_rejected(m.from_user.id, (m.text or "")[:64], "no_access")


@bot.callback_query_handler(func=lambda c: not settings.has_access(c.from_user.id))
def _ignore_callbacks(c: types.CallbackQuery) -> None:
    """Silently swallow callback queries from unauthorised users."""

    settings.log_rejected(c.from_user.id, (c.data or "")[:64], "no_access")
    try:
        bot.answer_callback_query(c.id)
    except Exception:
        pass

