"""Client for sending user messages and application data to an AI API."""

import json
import os
from typing import Any

from openai import OpenAI

from config import SYSTEM_PROMPT


def generate_reply(user_message: str, data: Any) -> str:
    """Generate a reply using the user's message and the application data."""
    client = OpenAI(
        api_key=os.getenv("AI_API_KEY"),
        base_url=os.getenv("AI_BASE_URL"),
    )
    response = client.chat.completions.create(
        model=os.getenv("AI_MODEL"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(user_message, data),
            },
        ],
    )
    return response.choices[0].message.content.strip()


def _build_user_prompt(user_message: str, data: Any) -> str:
    serialized_data = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        "User message:\n"
        f"{user_message}\n\n"
        "Application data (JSON):\n"
        f"{serialized_data}"
    )
