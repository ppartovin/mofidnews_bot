import os
from bale_bot import Bot, Update

TOKEN = os.getenv("BALE_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN is not set")

bot = Bot(token=TOKEN)

@bot.message_handler(commands=None)
def echo(update: Update):
    if update.message and update.message.text:
        bot.send_message(
            chat_id=update.message.chat.id,
            text=update.message.text
        )

bot.polling()
