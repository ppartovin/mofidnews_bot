import asyncio
import json
from bale import Bot, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "your-token-here"
bot = Bot(token=TOKEN)

def load_broadcasts() -> dict:
    with open("broadcasts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def build_keyboard() -> InlineKeyboardMarkup:
    broadcasts = load_broadcasts()
    keyboard = InlineKeyboardMarkup()
    for class_name in broadcasts.keys():
        keyboard.add(InlineKeyboardButton(class_name, callback_data=class_name))
    return keyboard

@bot.event
async def on_message(message: Message):
    if message.content == "/start":
        await message.reply(
            "سلام! 👋\nلطفاً کلاس خود را انتخاب کنید:",
            components=build_keyboard()
        )

@bot.event
@bot.event
async def on_callback(callback: CallbackQuery):
    broadcasts = load_broadcasts()
    selected = callback.data

    if selected in broadcasts:
        await callback.message.reply(broadcasts[selected])
    else:
        await callback.message.reply("کلاس یافت نشد.")

    await callback.answer()



#without input
#async def on_callback(callback: CallbackQuery):
 #   broadcasts = load_broadcasts()
  #  selected = callback.data

  #  if selected in broadcasts:
 #       await callback.message.reply(broadcasts[input])
 #   else:
  #      await callback.message.reply("کلاس یافت نشد.")

  #  await callback.answer()

asyncio.run(bot.run())

#توکن نیاز