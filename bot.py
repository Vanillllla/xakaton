import asyncio
import json
import os
from idlelib.window import add_windows_to_menu
from math import pi

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, user, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from pyexpat.errors import messages

from database import Database
from link_ai import LinkAI


class TextBot:
    """Класс бота для генерации текста с настройками"""

    keyboard_quest = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️", callback_data="back"), InlineKeyboardButton(text="➡️", callback_data="next")],
            [InlineKeyboardButton(text="🏠В меню", callback_data="menu"), InlineKeyboardButton(text="✅ Завершить", callback_data="finish")],
        ]
    )
    keyboard_quest.inline_keyboard[0][1] = InlineKeyboardButton(text="stop", callback_data="none")
    keyboard_yes_no = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes")],
            [InlineKeyboardButton(text="Нет", callback_data="no")],
            [InlineKeyboardButton(text="Наверное", callback_data="WTF??!")],
        ]
    )
    # KeyboardButton(text="Мульти чат")
    keyboard_main = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Одиночный запрос"), KeyboardButton(text="🗂️ Доп. функции")],
            [KeyboardButton(text="❓ Запрос с уточнениями"), KeyboardButton(text="🛠️ Настройки генерации")],
        ],
        resize_keyboard=True,  # Подгонка под размер
        one_time_keyboard=True  # Скрыть после нажатия
    )

    keyboard_dop_main = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Генерация изображения"), KeyboardButton(text="Мульти-чат")],
            [KeyboardButton(text="📅 Генерация контент плана"), KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,  # Подгонка под размер
        one_time_keyboard=True  # Скрыть после нажатия
    )

    keyboard_dop_main_a = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Генерация изображения"), KeyboardButton(text="Мульти-чат")],
            [KeyboardButton(text="📅 Генерация контент плана"), KeyboardButton(text="🔙 Назад"), KeyboardButton(text="⚙️ Настройки бота")],
        ],
        resize_keyboard=True,  # Подгонка под размер
        one_time_keyboard=True  # Скрыть после нажатия
    )

    keyboard_settings = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="tut_pusto")],
            [KeyboardButton(text="В меню")],
        ],
        resize_keyboard=True
    )

    # keyboard_sizes = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(
    #             text=style_name,
    #             callback_data=f"style_{style_key}"  # уникальный идентификатор
    #         )]
    #         for style_key, style_name in TEXT_STYLES.items()
    #     ]
    # )

    class PromptStates(StatesGroup):
        """Состояния для FSM"""
        waiting_for_prompt = State()
        waiting_for_text_input = State()

    class MainMenu(StatesGroup):
        mane_state = State()
        dop_state = State()
        menu_handler = State()

    class QuestState(StatesGroup):
        to_quest = State()
        to_text_answer = State()

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

        # Обработчики состояний
        self.dp.message.register(self.process_prompt, self.PromptStates.waiting_for_prompt)

        # Обработчики для вопросов
        self.dp.message.register(self.handle_quest_text, self.QuestState.to_text_answer)
        self.dp.callback_query.register(self.handle_quest_callback,StateFilter(self.QuestState.to_text_answer))

        self.dp.message.register(self.menu_handler, self.MainMenu.menu_handler)
        self.dp.message.register(self.mane_menu, self.MainMenu.mane_state)


        self.dp.message.register(self.mane_menu, F.text == "В меню")

    async def mane_menu(self, message: types.Message, state: FSMContext):
        await message.answer("Главное меню :",
                             reply_markup=self.keyboard_main)
        await state.set_state(self.MainMenu.menu_handler)

    async def dop_menu(self, message: types.Message, state: FSMContext):
        await message.delete()
        # if message.from_user.id in self.db.get_admins_id():
        #     await message.answer("Дополнительное меню : ",reply_markup=self.keyboard_dop_main_a)
        # else:
        await message.answer("Дополнительное меню : ",reply_markup=self.keyboard_dop_main)
        await state.set_state(self.MainMenu.menu_handler)

    async def menu_handler(self, message: types.Message, state: FSMContext):
        text = message.text
        if text == "🗂️ Доп. функции":
            await self.dop_menu(message, state)
        elif text == "🔙 Назад":
            await self.mane_menu(message, state)
        elif text == "📝 Одиночный запрос":
            await state.clear()
            await self.handle_solo_quest(message, state)
        elif text == "❓ Запрос с уточнениями":
            await state.clear()
            await self.handle_question_quest(message, state)

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

    async def cmd_start(self, message: types.Message, state: FSMContext):
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

        await state.set_state(self.MainMenu.menu_handler)

    async def handle_solo_quest(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки 'Одиночный запрос'"""
        await state.clear()
        await message.answer("Выбран режим: Одиночный запрос")
        await message.answer("Теперь введите ваш промт:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(self.PromptStates.waiting_for_prompt)
        # Здесь ваша логика для одиночного запроса

    async def process_prompt(self, message: types.Message, state: FSMContext):
        """Обработка промта"""
        data = await state.get_data()
        data["prompt"] = message.text

        # Вставить пользовательскую функцию обработки здесь
        settings = self.db.get_user_settings(message.from_user.id)
        system_prompt = self.ai.prompt_from_settings(settings)
        result = self.ai.prompt_with_system_context(message.text, system_prompt)

        await state.clear()
        await message.answer(result.output_text)
        await self.mane_menu(message, state)
        return

    async def handle_question_quest(self, message : types.Message, state: FSMContext):
        data = await state.get_data()

        if "quest" not in data:
            await state.clear()
            await message.answer("Выбран режим: Запрос с уточнениями")
            await state.update_data(quest=1)
            data["quest"] = 1
            await state.update_data(finish=0)
            data["finish"] = 0
            await state.update_data(quest_data={})
            with open('settings.json', 'r', encoding='utf-8') as file:
                quests_0 = json.load(file)
            quests = quests_0['questions']
            await state.update_data(quests=quests)
            data["quests"] = quests
            await state.update_data(quests_count=len(quests))
            data["quests_count"] = len(quests)

        quests = data["quests"]
        print(data)

        if data["finish"] == 1:
            resp = self.ai.dialogue(data["quest_data"]) #".output_text
            await message.answer(resp)
            await state.clear()
            await self.mane_menu(message, state)
            return None
        new_keyboard = self.keyboard_quest.copy
        if data["quest"] >= data["quests_count"]:
            self.keyboard_quest.inline_keyboard[0] = [InlineKeyboardButton(text="⬅️", callback_data="back")]
        elif data["quest"] <= 1:
            self.keyboard_quest.inline_keyboard[0] = [InlineKeyboardButton(text="➡️", callback_data="next")]
        else:
            self.keyboard_quest.inline_keyboard[0] = [InlineKeyboardButton(text="⬅️", callback_data="back"), InlineKeyboardButton(text="➡️", callback_data="next")]
        await message.answer(quests[str(data["quest"])]["text"], reply_markup=self.keyboard_quest)

        await state.set_state(self.QuestState.to_text_answer)
        return None

    async def handle_quest_callback(self, callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        print("button pressed")
        await callback.answer()
        if callback.data == "next":
            await self.bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            await state.update_data(quest=data["quest"]+1)
        elif callback.data == "back":
            await self.bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            await state.update_data(quest=data["quest"]-1)
        elif callback.data == "finish":
            await self.bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            await state.update_data(finish=1)
        elif callback.data == "menu":
            await self.bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            await state.clear()
            await self.mane_menu(callback.message, state)
            return None


        await self.handle_question_quest(callback.message, state)

    async def handle_quest_text(self, message: types.Message, state: FSMContext):
        data = await state.get_data()

        print("Типа сохранилось:", message.text)

        quest_data = data.get("quest_data", {})
        quest_data[str(data["quest"])] = message.text

        await state.update_data(quest_data=quest_data)
        await state.update_data(quest=data["quest"] + 1)

        await self.handle_question_quest(message, state)

    async def handle_multi_quest(self, message: types.Message):
        """Обработчик кнопки 'Мульти чат'"""
        await message.answer("Выбран режим: Мульти чат")
        # Здесь ваша логика для мульти чата

    async def handle_settings(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки 'Настройки'"""
        await message.answer("Открыты настройки", reply_markup=self.keyboard_settings)
        # Здесь ваша логика для настроек
        # Например, показать клавиатуру с настройками

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
