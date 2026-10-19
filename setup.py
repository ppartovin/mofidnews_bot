import os
import requests
from flask import Flask, request

from ai_client import generate_reply
from data_loader import load_data
from error_handling import ERROR_REPLY, deliver_reply, register_error_handlers, safe_call
from rate_limiter import configure_rate_limiter

app = Flask(__name__)
register_error_handlers(app)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN is not set")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

def send_message(chat_id: int, text: str) -> dict:
    """Send a text message to a Bale chat."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json().get("result", {})


def edit_message(chat_id: int, message_id: int, text: str) -> None:
    """Edit a previously sent text message in a Bale chat."""
    url = f"{BASE_URL}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


rate_limit_messages = configure_rate_limiter(app, send_message)


@app.route("/webhook", methods=["POST"])
@rate_limit_messages
def webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message")
    if isinstance(message, dict):
        chat = message.get("chat", {})
        chat_id = chat.get("id") if isinstance(chat, dict) else None
        text = message.get("text")

        if chat_id and text is not None:
            processing_message = safe_call(send_message, chat_id, "در حال پردازش...", default={})
            processing_message_id = processing_message.get("message_id")

            try:
                application_data = load_data()
                reply = generate_reply(text, application_data)
            except Exception:
                app.logger.exception("Could not generate a reply")
                reply = ERROR_REPLY

            deliver_reply(send_message, edit_message, chat_id, processing_message_id, reply)

    return "OK", 200


@app.route("/", methods=["GET"])
def checkrun():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
