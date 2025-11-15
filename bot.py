import asyncio
import os
from math import pi

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, user
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from database import Database
from link_ai import LinkAI

class TextBot:
    """Класс бота для генерации текста с настройками"""

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

    keyboard_yes_no = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes")],
            [InlineKeyboardButton(text="Нет", callback_data="no")],
            [InlineKeyboardButton(text="Наверное", callback_data="WTF??!")],
        ]
    )

    keyboard_main = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Одиночный запрос"), KeyboardButton(text="Запрос с уточнениями")],
            [KeyboardButton(text="Мульти чат"), KeyboardButton(text="Настройки")],
        ],
        resize_keyboard=True,  # Подгонка под размер
        one_time_keyboard=False  # Скрыть после нажатия
    )

    keyboard_settings = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="tut_pusto")],
            [KeyboardButton(text="В меню")],
        ],
        resize_keyboard=True
    )

    keyboard_sizes = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text=style_name,
            callback_data=f"style_{style_key}"  # уникальный идентификатор
        )]
        for style_key, style_name in TEXT_STYLES.items()
    ]
)







    class PromptStates(StatesGroup):
        """Состояния для FSM"""
        waiting_for_prompt = State()
        waiting_for_text_input = State()

    class MainMenu(StatesGroup):
        mane_state = State()
        settings = State()
        admin = State()
        solo_quest = State()

    def __init__(self):
        """Инициализация бота и БД"""
        load_dotenv()

        self.bot = Bot(token=os.getenv('BOT_TOKEN'))
        self.dp = Dispatcher()

        # Храним последние message_id для удаления
        self.user_last_messages = {}

        # Конфигурация БД из .env
        DB_CONFIG = {
            "host": os.getenv('DB_HOST'),
            "user": os.getenv('DB_USER'),
            "password": os.getenv('DB_PASSWORD'),
            "database": os.getenv('DB_NAME')
        }

        self.ai = LinkAI()

        self.db = Database(DB_CONFIG)
        # self.db.create_users_table()

        # Регистрация обработчиков
        self._register_handlers()

    def _register_handlers(self):
        """Регистрация всех обработчиков сообщений"""
        # Обработчики команд
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_admin, Command("admin"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.test, Command("test"))

        # Обработчики состояний
        self.dp.message.register(self.process_prompt, self.PromptStates.waiting_for_prompt)
        self.dp.message.register(self.texst_input, self.PromptStates.waiting_for_text_input)


        self.dp.message.register(self.handle_solo_quest, F.text == "Одиночный запрос")
        self.dp.message.register(self.handle_question_quest, F.text == "Запрос с уточнениями")
        self.dp.message.register(self.handle_multi_quest, F.text == "Мульти чат")
        self.dp.message.register(self.handle_settings, F.text == "Настройки")
        self.dp.message.register(self.mane_menu, self.MainMenu.mane_state)

        self.dp.message.register(self.mane_menu , F.text == "В меню")



    async def test(self, message: types.Message):
        pass

    async def notify_admins_on_startup(self):
        """Уведомить администраторов о запуске бота"""
        admins = self.db.get_admins_id()

        for admin_id in admins:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text="✅ Бот запущен и готов к работе! /start"
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    async def cmd_admin(self, message: types.Message):
        """Команда для администраторов"""
        if not self.db.is_admin(message.from_user.id):
            await message.answer("Доступ запрещен")
            return

        # Вставить административные функции здесь
        await message.answer("Панель администратора")

    async def cmd_help(self, message: types.Message):
        await message.answer(f"Доступные команды :\n"
                             f"/start\n"
                             f"/help\n"
                             f"/admin\n")

    async def mane_menu(self, message: types.Message):
        await message.answer("Выберите режим для продолжения работы:",
                             reply_markup=self.keyboard_main)

    async def cmd_start(self, message: types.Message):
        """Команда старта с регистрацией"""
        user = message.from_user
        if not self.db.user_exists(user.id):
            self.db.register_user(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                is_admin=False
            )

        await message.answer(f"Добро пожаловать {user.full_name}! Выберите режим для начала работы:",
                             reply_markup=self.keyboard_main)

    async def handle_solo_quest(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки 'Одиночный запрос'"""
        await state.clear()
        await message.answer("Выбран режим: Одиночный запрос")
        await message.answer("Теперь введите ваш промт:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(self.PromptStates.waiting_for_prompt)
        # Здесь ваша логика для одиночного запроса
        # Например, установка состояния или вызов другой функции

    async def handle_question_quest(self, message: types.Message, state: FSMContext ):
        """Обработчик кнопки 'Запрос с уточнениями'"""
        await state.clear()
        await message.answer("Выбран режим: Запрос с уточнениями")
        # await message.answer("Хотите подключить системные данные?", reply_markup=self.keyboard_yes_no)
        await message.answer("Теперь введите ваш промт:")
        await state.update_data()
        await state.set_state(self.PromptStates.waiting_for_text_input)










        # Здесь ваша логика для запроса с уточнениями

    async def handle_multi_quest(self, message: types.Message):
        """Обработчик кнопки 'Мульти чат'"""
        await message.answer("Выбран режим: Мульти чат")
        # Здесь ваша логика для мульти чата

    async def handle_settings(self, message: types.Message):
        """Обработчик кнопки 'Настройки'"""
        await message.answer("Открыты настройки", reply_markup=self.keyboard_settings)
        # Здесь ваша логика для настроек
        # Например, показать клавиатуру с настройками

    async def texst_input(self, message: types.Message, state: FSMContext):
        pass

    async def process_prompt(self, message: types.Message, state: FSMContext):
        """Обработка промта"""
        data = await state.get_data()
        data["prompt"] = message.text

        # Вставить пользовательскую функцию обработки здесь


        result = await self.ai.your_func(data.items().mapping, self.db.get_user_settings(message.from_user.id))
        # --------------------------------/\/\/\/\/\/\/\/\/\-----------/\/\/\/\/\/\/\----------------
        # ---------------------------------------dict---------------------dict-----------------------

        await state.clear()
        await message.answer(result)
        await self.mane_menu(message)

    async def run(self):
        """Запуск бота"""
        # Уведомляем администраторов о запуске
        await self.notify_admins_on_startup()

        # Запускаем поллинг
        await self.dp.start_polling(self.bot)


async def main():
    bot_instance = TextBot()
    await bot_instance.run()


if __name__ == "__main__":
    asyncio.run(main())