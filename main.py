import logging
import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

# --- ENV переменные ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- OpenAI клиент ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Google Sheets ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(json.loads(GOOGLE_CREDENTIALS_JSON), scopes=scopes)
gs_client = gspread.authorize(credentials)
sheet = gs_client.open("Заявки Кредит").sheet1

# --- Бот и роутеры ---
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# --- Хендлеры ---
@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привіт! Я допоможу вам підібрати кредит. Що вас цікавить: готівковий, на товар чи картка?")

@router.message()
async def gpt_handler(message: Message):
    user_text = message.text
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                   "content": (
                        "Ти — ввічливий та професійний фінансовий менеджер. "
                        "Твоє завдання — допомогти клієнту залишити заявку на кредит або розстрочку. "
                        "Спілкуйся українською, коротко, доброзичливо. "
                        "Не повторюй одні й ті самі питання. "
                        "Задавай запитання по черзі: далі — тільки після відповіді. "
                        "Завжди веди діалог до фіналу — отримання заявки.\n\n"
                        "Алгоритм:\n"
                        "1. Запитай, яка сума кредиту цікавить клієнта.\n"
                        "2. Якщо клієнт хоче розстрочку — запитай посилання на товар.\n"
                        "3. Після цього попроси залишити ім’я та номер телефону для оформлення заявки.\n"
                        "4. Якщо клієнт надає номер — подякуй і скажи, що заявка обробляється менеджером.\n"
                        "5. Якщо номер вже був — не повторюй запит.\n\n"
                        "Мета:\n"
                        "- Отримати суму 💰\n"
                        "- Посилання на товар 🔗 (опціонально)\n"
                        "- Ім’я та телефон 📞"
                       "Після завершення діалогу — подякуй клієнту і запропонуй відвідати сайт https://financebroker.com.ua для детальнішої інформації."
                    )

                },
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )
        reply = response.choices[0].message.content
        await message.answer(reply)

        if any(char.isdigit() for char in user_text) and len(user_text) >= 10:
            sheet.append_row([message.from_user.full_name, user_text])

    except Exception as e:
        logging.exception("GPT error:")
        await message.answer("Виникла помилка при зверненні до GPT.")

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
