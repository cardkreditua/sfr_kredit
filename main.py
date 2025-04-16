import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram import F

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Токен из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Обработчик команды /start
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Привіт! Я працюю 😉")

# Обработчик всех текстов
@dp.message()
async def echo(message: Message):
    await message.answer(f"Ти написав: {message.text}")

# Запуск бота через long polling
if __name__ == "__main__":
    import asyncio

    async def main():
        await dp.start_polling(bot)

    asyncio.run(main())


