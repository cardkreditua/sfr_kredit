import os
import logging
import json
import openai
import gspread
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)

# ENV переменные
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Бот и диспетчер
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# GPT ключ
openai.api_key = OPENAI_API_KEY

# Google Sheets подключение
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(
    json.loads(GOOGLE_CREDENTIALS_JSON), scopes=scopes
)
gs_client = gspread.authorize(creds)
sheet = gs_client.open("Заявки Кредит").sheet1

@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привіт! Я допоможу вам підібрати кредит. Що вас цікавить: готівковий, на товар чи кредитна картка?")

@router.message()
async def gpt_handler(message: Message):
    user_text = message.text

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти ввічливий українськомовний асистент, який допомагає залишити заявку на кредит. Запитай про суму, місто, строк і підведи клієнта до того, щоб він залишив номер телефону."},
            {"role": "user", "content": user_text},
        ]
    )

    reply = response["choices"][0]["message"]["content"]

    # Зберігаємо, якщо є цифри (номер телефона, сума і т.д.)
    if any(char.isdigit() for char in user_text) and len(user_text) >= 10:
        sheet.append_row([message.from_user.full_name, user_text])

    await message.answer(reply)

if __name__ == "__main__":
    import asyncio

    async def main():
        await dp.start_polling(bot)

    asyncio.run(main())


