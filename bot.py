import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from database import Database

# Загрузка переменных из .env
load_dotenv()

# Инициализация бота и БД
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Конфигурация БД из .env
DB_CONFIG = {
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_NAME')
}

db = Database(DB_CONFIG)

# Создание таблицы при запуске
db.create_users_table()


# Состояния для FSM
class PromptStates(StatesGroup):
    waiting_for_size = State()
    waiting_for_style = State()
    waiting_for_tone = State()
    waiting_for_prompt = State()


# Шаблонные параметры (легко редактировать)
TEXT_SIZES = {
    "small": "Короткий",
    "medium": "Средний",
    "large": "Длинный"
}

TEXT_STYLES = {
    "formal": "Формальный",
    "casual": "Неформальный",
    "technical": "Технический"
}

TEXT_TONES = {
    "neutral": "Нейтральный",
    "friendly": "Дружелюбный",
    "professional": "Профессиональный"
}


# Команда старта с регистрацией
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    if not db.user_exists(user.id):
        db.register_user(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            is_admin=False  # Задать True для администраторов
        )
    await message.answer("Добро пожаловать! Используйте /prompt для начала работы")


# Команда для администраторов
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not db.is_admin(message.from_user.id):
        await message.answer("Доступ запрещен")
        return

    # Вставить административные функции здесь
    await message.answer("Панель администратора")


# Начало диалога
@dp.message(Command("prompt"))
async def cmd_prompt(message: types.Message, state: FSMContext):
    # Проверка регистрации
    if not db.user_exists(message.from_user.id):
        await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start")
        return

    # Сброс состояния и начало опроса
    await state.clear()
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=size)] for size in TEXT_SIZES.values()],
        resize_keyboard=True
    )
    await message.answer("Выберите размер текста:", reply_markup=keyboard)
    await state.set_state(PromptStates.waiting_for_size)


# Обработка размера текста
@dp.message(PromptStates.waiting_for_size)
async def process_size(message: types.Message, state: FSMContext):
    if message.text not in TEXT_SIZES.values():
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(size=message.text)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=style)] for style in TEXT_STYLES.values()],
        resize_keyboard=True
    )
    await message.answer("Выберите стиль текста:", reply_markup=keyboard)
    await state.set_state(PromptStates.waiting_for_style)


# Обработка стиля
@dp.message(PromptStates.waiting_for_style)
async def process_style(message: types.Message, state: FSMContext):
    if message.text not in TEXT_STYLES.values():
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(style=message.text)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=tone)] for tone in TEXT_TONES.values()],
        resize_keyboard=True
    )
    await message.answer("Выберите тон текста:", reply_markup=keyboard)
    await state.set_state(PromptStates.waiting_for_tone)


# Обработка тона
@dp.message(PromptStates.waiting_for_tone)
async def process_tone(message: types.Message, state: FSMContext):
    if message.text not in TEXT_TONES.values():
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(tone=message.text)
    await message.answer("Теперь введите ваш промт:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(PromptStates.waiting_for_prompt)


# Обработка промта
@dp.message(PromptStates.waiting_for_prompt)
async def process_prompt(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_data["prompt"] = message.text

    # Вставить пользовательскую функцию обработки здесь
    result = await process_user_request(user_data)

    await message.answer(f"Результат:\n{result}")
    await state.clear()


# Пользовательская функция обработки (заменить на свою)
async def process_user_request(data: dict) -> str:
    # Пример обработки данных
    return (
        f"Параметры:\n"
        f"Размер: {data['size']}\n"
        f"Стиль: {data['style']}\n"
        f"Тон: {data['tone']}\n"
        f"Промт: {data['prompt']}"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())