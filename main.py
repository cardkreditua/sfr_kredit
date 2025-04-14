import logging
from aiogram import Bot, Dispatcher, types, executor
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 🔐 Загрузка данных из переменной окружения
credentials_info = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])

# 🔧 Налаштування токенів
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

openai.api_key = OPENAI_API_KEY
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# 🔧 Налаштування Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(creds)
sheet = client.open("Заявки Кредит").sheet1

# ✉️ Стартове повідомлення
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добрий день! 👋\nЯ допоможу вам підібрати кредит. Що вас цікавить: кредит готівкою, розстрочка на товар чи кредитна картка?")

# 💬 Основна логіка діалогу з GPT
@dp.message_handler()
async def handle_message(message: types.Message):
    user_input = message.text

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти ввічливий українськомовний асистент, який допомагає користувачам залишити заявку на кредит. Твоє завдання — запитати про суму, місто, строк і підвести клієнта до того, щоб він залишив номер телефону."},
            {"role": "user", "content": user_input},
        ]
    )

    gpt_reply = response['choices'][0]['message']['content']
    await message.reply(gpt_reply)

    # Якщо користувач залишив номер — зберігаємо у Google Таблицю
    if any(char.isdigit() for char in user_input) and len(user_input) >= 10:
        sheet.append_row([message.from_user.full_name, user_input])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
