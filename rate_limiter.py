"""Per-user rate limiting for incoming Bale messages."""

import os
import logging

from flask import jsonify, request
from flask_limiter import Limiter


RATE_LIMIT = os.getenv("RATE_LIMIT")
logger = logging.getLogger(__name__)
RATE_LIMIT_MESSAGE = "شما به محدودیت ارسال پیام رسیده‌اید. لطفاً ۱۲ ساعت بعد دوباره تلاش کنید."


def _message_data():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    return message if isinstance(message, dict) else None


def _is_not_user_message() -> bool:
    """Skip updates that the webhook does not handle as user messages."""
    message = _message_data()
    if not message or message.get("text") is None:
        return True

    chat = message.get("chat")
    return not isinstance(chat, dict) or not chat.get("id")


def _user_key() -> str:
    message = _message_data() or {}
    sender = message.get("from") or message.get("sender") or {}

    if isinstance(sender, dict) and sender.get("id") is not None:
        return f"bale-user:{sender['id']}"

    chat = message.get("chat") or {}
    if isinstance(chat, dict) and chat.get("id") is not None:
        return f"bale-chat:{chat['id']}"

    return f"ip:{request.remote_addr or 'unknown'}"


def configure_rate_limiter(app, send_message):
    """Attach the limiter and return its webhook decorator."""
    limiter = Limiter(
        key_func=_user_key,
        storage_uri="memory://",
        strategy="moving-window",
        default_limits=[],
    )
    limiter.init_app(app)

    def handle_rate_limit_exceeded(_request_limit):
        message = _message_data()
        chat = message.get("chat", {}) if message else {}
        chat_id = chat.get("id") if isinstance(chat, dict) else None

        logger.warning(
            "Rate limit exceeded: key=%s chat_id=%s limit=%s",
            _user_key(), chat_id, _request_limit.limit,
        )
        if chat_id:
            try:
                send_message(chat_id, RATE_LIMIT_MESSAGE)
            except Exception:
                app.logger.exception("Could not notify user about the rate limit")

        # Acknowledge the webhook update so the platform does not keep retrying it.
        return jsonify({"ok": True}), 200

    logger.info("Rate limiter configured: limit=%s", RATE_LIMIT)
    return limiter.limit(
        RATE_LIMIT,
        exempt_when=_is_not_user_message,
        error_message=RATE_LIMIT_MESSAGE,
        on_breach=handle_rate_limit_exceeded,
    )
