"""Error handling helpers for the Bale webhook."""

import logging

from flask import request
from werkzeug.exceptions import HTTPException


ERROR_REPLY = "متأسفانه در پردازش پیام شما خطایی رخ داد. لطفاً دوباره تلاش کنید."

logger = logging.getLogger(__name__)


def safe_call(func, *args, default=None, **kwargs):
    """Call ``func`` and return ``default`` instead of raising on failure."""
    try:
        return func(*args, **kwargs)
    except Exception:
        logger.exception("Error while calling %s", getattr(func, "__name__", func))
        return default


def deliver_reply(send_message, edit_message, chat_id, message_id, text) -> None:
    """Edit the processing message, falling back to sending a new message."""
    if message_id is not None:
        try:
            edit_message(chat_id, message_id, text)
            return
        except Exception:
            logger.exception("Could not edit the processing message; sending a new one")

    if safe_call(send_message, chat_id, text) is None:
        logger.error("Reply could not be delivered: chat_id=%s", chat_id)


def register_error_handlers(app) -> None:
    """Log unexpected errors and acknowledge webhook updates to avoid retries."""

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error

        app.logger.exception("Unhandled error while processing %s", request.path)
        if request.path == "/webhook":
            return "OK", 200
        return "Internal Server Error", 500
