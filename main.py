import logging
import os
import json
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold

from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

# --- Настройки окружения ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# --- Настройка логов ---
logging.basicConfig(level=logging.INFO)

# --- Инициализация бота ---
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- OpenAI (GPT) ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Google Sheets ---
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
gc = gspread.authorize(credentials)
sheet = gc.open("Заявки Кредит").sheet1

# --- Хендлеры ---
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привіт! Я допоможу вам підібрати кредит. Що вас цікавить: готівковий, на товар чи кредитна картка?")

@dp.message()
async def gpt_handler(message: Message):
    user_text = message.text

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти ввічливий українськомовний асистент, який допомагає залишити заявку на кредит. Запитай про суму, місто, строк і підведи клієнта до того, щоб він залишив номер телефону."},
                {"role": "user", "content": user_text},
            ]
        )
        reply = response.choices[0].message.content
        await message.answer(reply)

        # Зберігаємо, якщо є номер телефону
        if any(char.isdigit() for char in user_text) and len(user_text) >= 10:
            sheet.append_row([message.from_user.full_name, user_text])

    except Exception as e:
        await message.answer("Виникла помилка під час відповіді GPT.")
        logging.error(e)

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

