import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Конфигурация
TOKEN = "7790844065:AAGx0X-aWrDm-EoMBPkwULKBSAz0X25qLBA"


# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создание клавиатуры
def get_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔌 Выключить компьютер"))
    return builder.as_markup(resize_keyboard=True)

# Проверка прав пользователя
def is_user_allowed(user_id):
    return user_id in ALLOWED_USERS

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🖥️ Управление компьютером",
        reply_markup=get_keyboard()
    )

# Обработчик кнопки выключения
@dp.message(lambda message: message.text == "🔌 Выключить компьютер")
async def shutdown_computer(message: types.Message):
    try:
        await message.answer("🔄 Начинаю выключение компьютера...")
        if sys.platform == "win32":
            os.system("shutdown /s /t 1")
        else:
            os.system("sudo shutdown -h now")
    except Exception as e:
        logging.error(f"Ошибка выключения: {e}")
        await message.answer("❌ Ошибка при выключении!")

# Обработчик неправильных команд
@dp.message()
async def wrong_command(message: types.Message):
    await message.answer("⚠️ Неизвестная команда! 🔔")
    # Дополнительные действия для сигнала (например, вибрация)
    await bot.send_chat_action(message.chat.id, "typing")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())