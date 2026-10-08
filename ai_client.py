"""Client for sending user messages and application data to an AI API."""
#hello

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jdatetime
from openai import OpenAI

from config import SYSTEM_PROMPT

_API_LOGGER = logging.getLogger("ai_api_requests")
_API_LOGGER.setLevel(logging.INFO)
_API_LOGGER.propagate = False
if not _API_LOGGER.handlers:
    _log_file = os.path.join(os.path.dirname(__file__), "logs.txt")
    _handler = logging.FileHandler(_log_file, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _API_LOGGER.addHandler(_handler)


def generate_reply(user_message: str, data: Any) -> str:
    """Generate a reply using the user's message and the application data."""
    client = OpenAI(
        api_key=os.getenv("AI_API_KEY"),
        base_url=os.getenv("AI_BASE_URL"),
    )
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
    response = client.chat.completions.create(**request_payload)
    return response.choices[0].message.content.strip()


def _current_date_context() -> str:
    """Return today's Persian calendar date and weekday in Tehran time."""
    # Iran uses UTC+03:30; a fixed offset also works on Windows without tzdata.
    today = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    persian_today = jdatetime.date.fromgregorian(date=today.date())
    weekdays = (
        "\u062f\u0648\u0634\u0646\u0628\u0647",
        "\u0633\u0647\u200c\u0634\u0646\u0628\u0647",
        "\u0686\u0647\u0627\u0631\u0634\u0646\u0628\u0647",
        "\u067e\u0646\u062c\u0634\u0646\u0628\u0647",
        "\u062c\u0645\u0639\u0647",
        "\u0634\u0646\u0628\u0647",
        "\u06cc\u06a9\u0634\u0646\u0628\u0647",
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
