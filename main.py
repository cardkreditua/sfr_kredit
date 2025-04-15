# main.py
import logging
import os
import openai
import json
import gspread
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- ENV ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # https://your-app.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 10000))

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Bot Setup ---
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- GPT ---
openai.api_key = OPENAI_API_KEY

# --- Google Sheets ---
creds = Credentials.from_service_account_info(
    json.loads(GOOGLE_CREDENTIALS_JSON),
    scopes=scopes
)
gs_client = gspread.authorize(creds)
sheet = gs_client.open("Заявки Кредит").sheet1

# --- Handlers ---
@dp.message(commands=["start"])
async def start_cmd(message: Message):
    await message.answer("Доброго дня! 👋\nЯ допоможу вам підібрати кредит. Що вас цікавить: кредит готівкою, розстрочка чи картка?")

@dp.message()
async def handle_message(message: Message):
    user_text = message.text

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти ввічливий українськомовний асистент, який допомагає залишити заявку на кредит. Запитай про суму, місто, строк і підведи клієнта до того, щоб він залишив номер телефону."},
            {"role": "user", "content": user_text},
        ]
    )
    reply = response["choices"][0]["message"]["content"]

    # Якщо є номер — зберігаємо
    if any(char.isdigit() for char in user_text) and len(user_text) >= 10:
        sheet.append_row([message.from_user.full_name, user_text])

    await message.answer(reply)

# --- Web Server & Webhook ---
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

async def create_app():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    return app

if __name__ == '__main__':
    web.run_app(create_app(), host="0.0.0.0", port=PORT)
