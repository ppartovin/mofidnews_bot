import json
import bale

TOKEN = "TOKEN_خودت_رو_اینجا_بذار"

client = bale.Bot(token=TOKEN)


def load_broadcasts():
    with open("broadcasts.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_keyboard():
    data = load_broadcasts()
    buttons = []
    for class_name in data:
        buttons.append([bale.InlineKeyboardButton(class_name, callback_data=class_name)])
    return bale.InlineKeyboardMarkup(buttons)


@client.event
async def on_message(message: bale.Message):
    if message.content == "/start":
        keyboard = build_keyboard()
        await message.reply("کلاس خودت رو انتخاب کن:", components=keyboard)


@client.event
async def on_callback(callback: bale.CallbackQuery):
    data = load_broadcasts()
    class_name = callback.data
    if class_name in data:
        await callback.message.reply(data[class_name])
    await callback.answer()


client.run()
