import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.dispatcher.webhook import SendMessage
from aiohttp import web
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Например: https://sfr-kredit.onrender.com
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# GPT
openai.api_key = OPENAI_API_KEY

# Google Sheets
credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(creds)
sheet = client.open("Заявки Кредит").sheet1

# Команда /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    return SendMessage(message.chat.id, "Добрий день! 👋\nЯ допоможу вам підібрати кредит. Що вас цікавить: кредит готівкою, розстрочка на товар чи кредитна картка?")

# Ответ GPT
@dp.message_handler()
async def gpt_answer(message: types.Message):
    user_input = message.text

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти ввічливий українськомовний асистент, який допомагає залишити заявку на кредит. Запитай про суму, місто, строк і підведи клієнта до того, щоб він залишив номер телефону."},
            {"role": "user", "content": user_input},
        ]
    )

    reply = response['choices'][0]['message']['content']

    # Сохраняем номер, если есть
    if any(char.isdigit() for char in user_input) and len(user_input) >= 10:
        sheet.append_row([message.from_user.full_name, user_input])

    return SendMessage(message.chat.id, reply)

# Инициализация webhook
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, dp.dispatch)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, port=10000)
