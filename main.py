import logging
import os
import openai
import json
import gspread
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from google.oauth2.service_account import Credentials

# --- ENV ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Bot Setup ---
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- GPT ---
openai.api_key = OPENAI_API_KEY

# --- Google Sheets ---
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(
    json.loads(GOOGLE_CREDENTIALS_JSON),
    scopes=scopes
)
gs_client = gspread.authorize(creds)
sheet = gs_client.open("Заявки Кредит").sheet1

# --- Handlers ---
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Доброго дня! 👋\nЯ допоможу вам підібрати кредит. Що вас цікавить: кредит готівкою, розстрочка чи картка?")

@dp.message()
async def handle_message(message: Message):
    user_input = message.text

    # GPT-відповідь
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти ввічливий українськомовний асистент, який допомагає залишити заявку на кредит. Запитай про суму, місто, строк і підведи клієнта до того, щоб він залишив номер телефону."},
            {"role": "user", "content": user_input},
        ]
    )

    reply = response["choices"][0]["message"]["content"]

    # Якщо є номер — зберігаємо
    if any(char.isdigit() for char in user_input) and len(user_input) >= 10:
        sheet.append_row([message.from_user.full_name, user_input])

    await message.answer(reply)

# --- Run bot ---
if __name__ == "__main__":
    import asyncio

    async def main():
        await dp.start_polling(bot)

    asyncio.run(main())



