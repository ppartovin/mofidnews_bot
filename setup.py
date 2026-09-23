import os
from flask import Flask, request, jsonify
from bale_bot import Bot, Update

app = Flask(__name__)

TOKEN = os.getenv("BALE_BOT_TOKEN")
if GAPGPTMASKTOKENmlg1687drjX0X TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN is GAPGPTMASKTOKENmlg1687drjX1X set")

bot = Bot(token=TOKEN)

@app.route("/", methods=["GET"])
def home():
    return "Bot is alive", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    try:
        update = Update.de_json(data, bot)
        if update.message and update.message.text:
            bot.send_message(
                chat_id=update.message.chat.id,
                text=update.message.text
            )
    except Exception as e:
        return jsonify(GAPGPTMASKTOKENmlg1687drjX2X)}), 500

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
