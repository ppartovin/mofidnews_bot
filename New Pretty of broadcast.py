import json
import asyncio
import bale
from bale import Bot, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton


TOKEN = "[توکن لازم]"

BROADCASTS_FILE = "broadcastVll.json"


def load_broadcasts() -> dict:
    """بارگذاری تکالیف از فایل JSON"""
    with open(BROADCASTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_keyboard(broadcasts: dict) -> InlineKeyboardMarkup:
    """ساخت دکمه‌های اینلاین بر اساس کلیدهای JSON"""
    keyboard = InlineKeyboardMarkup()
    for class_name in broadcasts.keys():
        keyboard.add(InlineKeyboardButton(class_name, callback_data=class_name))
    return keyboard


client = Bot(token=TOKEN)


@client.event
async def on_message(message: Message):
    """هندل کردن پیام‌های دریافتی"""
    if message.text == "/start":
        broadcasts = load_broadcasts()
        keyboard = build_keyboard(broadcasts)
        await message.reply(
            "سلام! 👋\nکلاس خود را انتخاب کنید تا تکالیف را مشاهده کنید:",
            components=keyboard
        )


@client.event
async def on_callback(callback: CallbackQuery):
    """هندل کردن کلیک روی دکمه‌ها"""
    selected = callback.data  # نام کلاس انتخاب‌شده

    broadcasts = load_broadcasts()

    if selected in broadcasts:
        await callback.message.reply(broadcasts[selected])
    else:
        await callback.message.reply("❌ اطلاعاتی برای این کلاس یافت نشد.")

    await callback.answer()  # بستن حالت loading دکمه


if __name__ == "__main__":
    client.run()
