import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Например: https://sfr-kredit.onrender.com
WEBHOOK_PATH = "/webhook"
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
    await message.answer("Добрий день! 👋\nЯ допоможу вам підібрати кредит. Що вас цікавить: кредит готівкою, розстрочка на товар чи кредитна картка?")

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

    if any(char.isdigit() for char in user_input) and len(user_input) >= 10:
        sheet.append_row([message.from_user.full_name, user_input])

    await message.answer(reply)

# Webhook настройки
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=10000,
    )
