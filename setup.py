import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.getenv("Token")
if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN is not set")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message")
    if message:
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        text = message.get("text")

        if chat_id and text is not None:
            send_message(chat_id, text)

    return "OK", 200

@app.route("/", methods=["GET"])
def checkrun():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
