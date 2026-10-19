"""Client for sending user messages and application data to an AI API."""
#hello

import logging
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import jdatetime
from openai import OpenAI

from config import SYSTEM_PROMPT

from logging_config import AI_LOGGER_NAME

_API_LOGGER = logging.getLogger(AI_LOGGER_NAME)
logger = logging.getLogger(__name__)


def generate_reply(user_message: str, data: Any) -> str:
    """Generate a reply using the user's message and the application data."""
    request_payload = {
        "model": os.getenv("AI_MODEL"),
        "messages": [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{_current_date_context()}"},
            {
                "role": "user",
                "content": _build_user_prompt(user_message, data),
            },
        ],
    }
    _API_LOGGER.info(
        "%s",
        json.dumps(request_payload, ensure_ascii=False, separators=(",", ":")),
    )
    logger.info(
        "Sending AI request: model=%s message_chars=%d",
        request_payload["model"], len(user_message),
    )
    started = time.perf_counter()
    try:
        with OpenAI(
            api_key=os.getenv("AI_API_KEY"),
            base_url=os.getenv("AI_BASE_URL"),
        ) as client:
            response = client.chat.completions.create(**request_payload)
            reply = response.choices[0].message.content.strip()
    except Exception:
        logger.exception(
            "AI request failed after %.0f ms", (time.perf_counter() - started) * 1000
        )
        raise
    usage = getattr(response, "usage", None)
    logger.info(
        "AI response received in %.0f ms: reply_chars=%d prompt_tokens=%s completion_tokens=%s",
        (time.perf_counter() - started) * 1000,
        len(reply),
        getattr(usage, "prompt_tokens", "?"),
        getattr(usage, "completion_tokens", "?"),
    )
    return reply


def _current_date_context() -> str:
    """Return today's Persian calendar date and weekday in Tehran time."""
    # Iran uses UTC+03:30; a fixed offset also works on Windows without tzdata.
    today = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    persian_today = jdatetime.date.fromgregorian(date=today.date())
    weekdays = (
        "\u0634\u0646\u0628\u0647",
        "\u06cc\u06a9\u0634\u0646\u0628\u0647",
        "\u062f\u0648\u0634\u0646\u0628\u0647",
        "\u0633\u0647\u200c\u0634\u0646\u0628\u0647",
        "\u0686\u0647\u0627\u0631\u0634\u0646\u0628\u0647",
        "\u067e\u0646\u062c\u0634\u0646\u0628\u0647",
        "\u062c\u0645\u0639\u0647",
    )
    return (
        f"\u062a\u0627\u0631\u06cc\u062e \u0627\u0645\u0631\u0648\u0632: "
        f"{persian_today.day:02d}/{persian_today.month:02d}/{persian_today.year} "
        f"\u0634\u0645\u0633\u06cc\u060c {weekdays[persian_today.weekday()]}"
    )


def _build_user_prompt(user_message: str, data: Any) -> str:
    serialized_data = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        "User message:\n"
        f"{user_message}\n\n"
        "Application data (JSON):\n"
        f"{serialized_data}"
    )
