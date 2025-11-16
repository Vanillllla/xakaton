import asyncio
import json
import os
import pathlib


from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

from database import Database
from link_ai import LinkAI


class TextBot:
    """Класс бота для генерации текста с настройками"""

    keyboard_quest = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️", callback_data="back"),
             InlineKeyboardButton(text="➡️", callback_data="next")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu"),
             InlineKeyboardButton(text="✅ Завершить", callback_data="finish")],
        ]
    )
    keyboard_admin = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Внести информацию от организации", callback_data="input_org_info"),
             InlineKeyboardButton(text="Показать информацию о вашей организации", callback_data="get_org_info")],
            [InlineKeyboardButton(text="Добавить администраторов", callback_data="add_admin")]
        ]
    )
    keyboard_settings_mane = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Информация об организации", callback_data="org_info_use")],
            [InlineKeyboardButton(text="🎨 Стиль", callback_data="stile")],
            [InlineKeyboardButton(text="🗣️ Тон", callback_data="tone")],
            [InlineKeyboardButton(text="📐 Размер", callback_data="size")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
        ]
    )
    keyboard_param_upgrader = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=" Красиво", callback_data="up_1")],
            [InlineKeyboardButton(text=" Другими словами", callback_data="up_2")],
            [InlineKeyboardButton(text=" Кратко", callback_data="up_3")],
            [InlineKeyboardButton(text=" Проще", callback_data="up_4")]
        ]
    )
    keyboard_main = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 Разовый запрос"), KeyboardButton(text="🗂️ Доп. функции")],
            [KeyboardButton(text="❓ Запрос с уточнениями"), KeyboardButton(text="🛠️ Настройки генерации")],
        ],
        resize_keyboard=True,  # Подгонка под размер
        one_time_keyboard=True  # Скрыть после нажатия
    )
    keyboard_dop_main = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏞️ Генерация изображения"), KeyboardButton(text="📝 Улучшение текста")],
            [KeyboardButton(text="📅 Генерация контент плана"), KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,  # Подгонка под размер
        one_time_keyboard=True  # Скрыть после нажатия
    )

    class PromptStates(StatesGroup):
        """Состояния для FSM"""
        waiting_for_prompt = State()
        waiting_for_picture_prompt = State()
        waiting_for_content_plane_prompt = State()

    class MainMenu(StatesGroup):
        mane_state = State()
        dop_state = State()
        menu_handler = State()

        adm_settings = State()
        rec_settings_org = State()
        rec_settings_info = State()
        rec_settings_adm = State()

    class SettingsMenu(StatesGroup):
        settings_menu = State()

    class QuestState(StatesGroup):
        to_quest = State()
        to_text_answer = State()

    class UpGradeState(StatesGroup):
        to_settings = State()

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
        self.dp.message.register(self.picture_generator, self.PromptStates.waiting_for_picture_prompt)
        self.dp.message.register(self.content_plane_generator, self.PromptStates.waiting_for_content_plane_prompt)

        # Обработчики для вопросов
        self.dp.message.register(self.handle_quest_text, self.QuestState.to_text_answer)
        self.dp.callback_query.register(self.handle_quest_callback, StateFilter(self.QuestState.to_text_answer))

        # Обработчики для админов
        self.dp.callback_query.register(self.org_info_add, F.data == "input_org_info",
                                        StateFilter(self.MainMenu.adm_settings))
        self.dp.callback_query.register(self.adm_add, F.data == "add_admin", StateFilter(self.MainMenu.adm_settings))
        self.dp.callback_query.register(self.org_info, F.data == "get_org_info",
                                        StateFilter(self.MainMenu.adm_settings))

        # Обработчики для настроек генерации
        self.dp.callback_query.register(self.settings_handler,
                                        StateFilter(self.SettingsMenu.settings_menu))

        self.dp.message.register(self.org_info_add, self.MainMenu.rec_settings_org)
        self.dp.message.register(self.adm_add, self.MainMenu.rec_settings_adm)

        self.dp.message.register(self.menu_handler, self.MainMenu.menu_handler)
        self.dp.message.register(self.mane_menu, self.MainMenu.mane_state)

        # Обработчики для улучшения текста
        self.dp.message.register(self.text_upgrader, self.UpGradeState.to_settings)
        self.dp.callback_query.register(self.text_upgrader_hendler, StateFilter(self.UpGradeState.to_settings))

    async def mane_menu(self, message: types.Message, state: FSMContext):
        await message.answer("Главное меню :",
                             reply_markup=self.keyboard_main)
        await state.set_state(self.MainMenu.menu_handler)

    async def dop_menu(self, message: types.Message, state: FSMContext):
        await message.delete()
        await message.answer("Дополнительное меню : ", reply_markup=self.keyboard_dop_main)
        await state.set_state(self.MainMenu.menu_handler)

    async def menu_handler(self, message: types.Message, state: FSMContext):
        text = message.text
        if text == "🗂️ Доп. функции":
            await self.dop_menu(message, state)
        elif text == "🔙 Назад":
            await self.mane_menu(message, state)
        elif text == "🔥 Разовый запрос":
            await state.clear()
            await self.handle_solo_quest(message, state)
        elif text == "❓ Запрос с уточнениями":
            await state.clear()
            await self.handle_question_quest(message, state)
        elif text == "🏞️ Генерация изображения":
            await state.clear()
            await self.picture_promt_listen(message, state)
        elif text == "📅 Генерация контент плана":
            await state.clear()
            await self.content_plane_promt_listen(message, state)
        elif text == "🛠️ Настройки генерации":
            await state.clear()
            await self.settings(message, state)
        elif text == "📝 Улучшение текста":
            await state.clear()
            await self.text_upgrader(message, state)

    async def cmd_admin(self, message: types.Message, state: FSMContext):
        """Команда для администраторов"""
        # user = message.from_user
        # if not self.db.user_exists(user.id):
        #     self.db.register_user(
        #         user_id=user.id,
        #         username=user.username,
        #         full_name=user.full_name,
        #         is_admin=False
        #     )

        await state.clear()
        if not self.db.is_admin(message.from_user.id):
            await message.answer("Доступ запрещен")
            return

        # Вставить административные функции здесь
        mane_mass = await message.answer("Панель администратора", reply_markup=self.keyboard_admin)
        await state.update_data(mane_mass=mane_mass)
        await state.set_state(self.MainMenu.adm_settings)
        return

    async def adm_add(self, message: types.Message, state: FSMContext):
        data = await state.get_data()
        if "vvod" not in data:
            await message.message.edit_text(
                text='Введите имя пользователя которого вы хотите назначить администратором системы :')
            await state.update_data(vvod=1)
            await state.set_state(self.MainMenu.rec_settings_adm)
            return
        else:

            result = self.db.add_administrator(message.text[1::] if message.text[0] == "@" else message.text)
            if result:
                await message.answer("Администратор добавлен")
            else:
                await message.answer("Пользователь не зарегистрирован в системе")
            await state.clear()
            await self.mane_menu(message, state)
        await state.clear()
        await self.mane_menu(message, state)
        return

    async def org_info_add(self, message: types.Message, state: FSMContext):
        data = await state.get_data()
        if "vvod" not in data:
            await message.message.edit_text(text='Введите описание вашей организации :')
            await state.update_data(vvod=1)
            await state.set_state(self.MainMenu.rec_settings_org)
            return
        else:

            result = message.text
            # result = self.ai.create_system_prompt(result).output_text
            self.db.organization_info_reload(message.from_user.id, result)

            await message.answer("Данные обновлены")
        await state.clear()
        await self.mane_menu(message, state)
        return

    async def org_info(self, message: types.Message, state: FSMContext):
        info = self.db.get_organization_info(message.from_user.id)

        await message.message.answer(f"Название : \n{info[1]}\n\nОписание : \n{info[0]}")
        await state.clear()
        await self.mane_menu(message, state)

    async def cmd_help(self, message: types.Message):
        await message.answer(f"Доступные команды :\n"
                             f"/start\n"
                             f"/help\n"
                             f"/admin\n")
        return

    async def cmd_start(self, message: types.Message, state: FSMContext):
        """Команда старта с регистрацией"""
        # user = message.from_user
        # if not self.db.user_exists(user.id):
        #     self.db.register_user(
        #         user_id=user.id,
        #         username=user.username,
        #         full_name=user.full_name,
        #         is_admin=False
        #     )

        await message.answer(f"Добро пожаловать {message.from_user.full_name}! Выберите режим для начала работы:",
                             reply_markup=self.keyboard_main)

        await state.set_state(self.MainMenu.menu_handler)

    async def text_upgrader(self, message: types.Message, state: FSMContext):
        data = await state.get_data()
        if "state" not in data:
            await message.answer("Введите текст для улучшения : ")
            await state.update_data(state="main_to_params")
            await state.update_data(kyebord=0)
            await state.set_state(self.UpGradeState.to_settings)


        elif data["state"] == "main_to_params":
            await state.update_data(text=message.text)
            await state.update_data(state="buttons")
            if data["kyebord"] == 1:
                await state.update_data(kyebord=0)
                self.keyboard_param_upgrader.inline_keyboard = self.keyboard_param_upgrader.inline_keyboard[:-2:]
            await message.answer("Выберите нужное улучшение :", reply_markup=self.keyboard_param_upgrader)
            await state.set_state(self.UpGradeState.to_settings)
        elif data["state"] == "again_quest":
            await state.update_data(state="buttons")
            if data["kyebord"] == 0:
                self.keyboard_param_upgrader.inline_keyboard = self.keyboard_param_upgrader.inline_keyboard + [[InlineKeyboardButton(text="✏️ Изменить текст", callback_data="edit")],[InlineKeyboardButton(text="✅ Завершить", callback_data="stop")]]
                await state.update_data(kyebord=1)
            await message.answer("Нужно ли ещё улучшить текст ?", reply_markup=self.keyboard_param_upgrader)


    async def text_upgrader_hendler(self, callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await callback.answer()
        text = data["text"]


        if callback.data == "up_1":
            await callback.message.edit_text("Делаю текст красивше )) : ")

            """
            text + up_1/2/... --> улучшение --> result
            """
            result = "красивый текст"

            await callback.message.answer(result)
            await state.update_data(text=result)
            await state.update_data(state="again_quest")
            await self.text_upgrader(callback.message, state)
        elif callback.data == "up_2":
            await callback.message.edit_text("Делаю текст lheubvb ckjdfvb )) : ")

            """
            text + up_1/2/... --> улучшение --> result
            """
            result = "Другими словами текст"

            await callback.message.answer(result)
            await state.update_data(text=result)
            await state.update_data(state="again_quest")
            await self.text_upgrader(callback.message, state)
        elif callback.data == "up_3":
            await callback.message.edit_text("Делаю текст короче : ")

            """
            text + up_1/2/... --> улучшение --> result
            """
            result = "Кратко текст"

            await callback.message.answer(result)
            await state.update_data(text=result)
            await state.update_data(state="again_quest")
            await self.text_upgrader(callback.message, state)
        elif callback.data == "up_4":
            await callback.message.edit_text("Делаю текст проще : ")

            """
            text + up_1/2/... --> улучшение --> result
            """
            result = "Проще текст"

            await callback.message.answer(result)
            await state.update_data(text=result)
            await state.update_data(state="again_quest")
            await self.text_upgrader(callback.message, state)

        elif callback.data == "stop":
            await state.clear()
            await callback.message.delete()
            await self.mane_menu(callback.message, state)
        elif callback.data == "edit":
            await callback.message.edit_text("Введите измелённый текст :")
            await state.update_data(state="main_to_params")
            await state.set_state(self.UpGradeState.to_settings)



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
        info = self.db.get_organization_info(message.from_user.id)[1]
        system_prompt = info + "Используй при создании постов хештэги."
        result = self.ai.prompt_from_settings(settings) + self.ai.prompt_with_system_context(message.text + "Используй хештэги только из описания организации и указанные выше", system_prompt)

        await state.clear()
        await message.answer(result.output_text)
        await self.mane_menu(message, state)
        return

    async def handle_question_quest(self, message: types.Message, state: FSMContext):
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
            await state.update_data(not_one=0)
            data["not_one"] = 0
        quests = data["quests"]

        if data["finish"] == 1:
            info = self.db.get_organization_info(message.from_user.id)[1]
            resp = self.ai.dialogue(data["quest_data"], info)
            await message.answer(resp.output_text)
            await state.clear()
            await self.mane_menu(message, state)
            return

        if data["quest"] >= data["quests_count"]:
            self.keyboard_quest.inline_keyboard[0] = [InlineKeyboardButton(text="⬅️", callback_data="back")]
        elif data["quest"] <= 1:
            self.keyboard_quest.inline_keyboard[0] = [InlineKeyboardButton(text="➡️", callback_data="next")]
        else:
            self.keyboard_quest.inline_keyboard[0] = [InlineKeyboardButton(text="⬅️", callback_data="back"),
                                                      InlineKeyboardButton(text="➡️", callback_data="next")]

        if data["not_one"] == 1:
            await message.edit_text(quests[str(data["quest"])]["text"], reply_markup=self.keyboard_quest)

        else:
            await message.answer(quests[str(data["quest"])]["text"], reply_markup=self.keyboard_quest)
            await state.update_data(not_one=1)
        await state.set_state(self.QuestState.to_text_answer)
        return

    async def handle_quest_callback(self, callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await callback.answer()
        if callback.data == "next":
            await state.update_data(quest=data["quest"] + 1)
        elif callback.data == "back":
            await state.update_data(quest=data["quest"] - 1)
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

        quest_data = data.get("quest_data", {})
        quest_data[str(data["quest"])] = message.text

        await state.update_data(not_one=0)
        await state.update_data(quest_data=quest_data)
        if data["quest"] <= data["quests_count"] - 1:
            await state.update_data(quest=data["quest"] + 1)

        await self.handle_question_quest(message, state)

    async def handle_multi_quest(self, message: types.Message):
        """Обработчик кнопки 'Мульти чат'"""
        await message.answer("Выбран режим: Мульти чат")
        # Здесь ваша логика для мульти чата

    async def picture_promt_listen(self, message: types.Message, state: FSMContext):
        await message.answer("Опишите, что вы хотите нарисовать")
        await state.set_state(self.PromptStates.waiting_for_picture_prompt)

    async def picture_generator(self, message: types.Message, state: FSMContext):
        prompt = message.text
        result = "pictures/picture.jpg"  # Эту строчку замени
        path = pathlib.Path(result)
        try:
            resp = await self.ai.draw(prompt)
            path.write_bytes(resp.image_bytes)
        finally:
            pass
        await state.clear()
        await message.answer_photo(FSInputFile(result))
        await message.answer("Создать изображение по новой?")
        # await self.mane_menu(message, state)
        return

    async def content_plane_promt_listen(self, message: types.Message, state: FSMContext):
        await message.answer(
            "Напишите на какой срок составить контент-план, по желанию укажите частоту публикаций, целевую аудиторию,предстоящие события, перечислите используемые хештэги, организации с которыми вы сотрудничаете.")
        await state.set_state(self.PromptStates.waiting_for_content_plane_prompt)

    async def content_plane_generator(self, message: types.Message, state: FSMContext):
        prompt = message.text
        info = self.db.get_organization_info(message.from_user.id)[1]
        result = self.ai.content_plan(prompt, info)

        await state.clear()
        await message.answer(result.output_text)
        await self.mane_menu(message, state)
        return

    async def settings(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки 'Настройки'"""
        if "not_first" not in await state.get_data():
            await state.update_data(not_first=1)
            with open('settings.json', 'r', encoding='utf-8') as file:
                settings_list = json.load(file)["settings"]
            await state.update_data(settings_list=settings_list)
            await state.update_data(settings=self.db.get_user_settings(message.from_user.id))
            await message.answer("Настройки генерации:", reply_markup=self.keyboard_settings_mane)
            await state.update_data(state="main")


        else:
            await message.edit_text("Настройки генерации:", reply_markup=self.keyboard_settings_mane)
        await state.set_state(self.SettingsMenu.settings_menu)
        return

    async def settings_handler(self, callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await callback.answer()

        if callback.data == "stile" or data["state"] == "to_stile":
            keyboard_stile_gen = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{value}"+(" 🟢"if str(key) == str(data["settings"]["set_style_type"]) else ""), callback_data=f"stile_select_{key}")] for key, value in data["settings_list"]["style_type"].items()
            ] + [[InlineKeyboardButton(text="💾 Сохранить", callback_data="save")], [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]])
            await state.update_data(state="main")
            await callback.message.edit_text(text="Выберите стиль написания текста:", reply_markup=keyboard_stile_gen)
        elif callback.data == "tone" or data["state"] == "to_tone":
            keyboard_stile_gen = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{value}"+(" 🟢"if str(key) == str(data["settings"]["set_tone"]) else ""), callback_data=f"tone_select_{key}")] for key, value in data["settings_list"]["tone"].items()
            ] + [ [InlineKeyboardButton(text="💾 Сохранить", callback_data="save")],[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]])
            await callback.message.edit_text(text="Выберите тон текста:", reply_markup=keyboard_stile_gen)
            await state.update_data(state="main")
        elif callback.data == "size" or data["state"] == "to_size":
            keyboard_stile_gen = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{value}"+(" 🟢"if str(key) == str(data["settings"]["set_size"]) else ""), callback_data=f"size_select_{key}")] for key, value in data["settings_list"]["size"].items()
            ] + [[InlineKeyboardButton(text="💾 Сохранить", callback_data="save")], [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]])
            await callback.message.edit_text(text="Выберите примерный размер текста:", reply_markup=keyboard_stile_gen)
            await state.update_data(state="main")

        elif "size_select_" in callback.data:
            key = callback.data[len(callback.data)-1::]
            data["settings"]["set_size"] = key
            await state.update_data(settings=data["settings"])
            await state.update_data(state="to_size")
            await self.settings_handler(callback, state)
        elif "tone_select_" in callback.data:
            key = callback.data[len(callback.data)-1::]
            data["settings"]["set_tone"] = key
            await state.update_data(settings=data["settings"])
            await state.update_data(state="to_tone")
            await self.settings_handler(callback, state)
        elif "stile_select_" in callback.data:
            key = callback.data[len(callback.data) - 1::]
            data["settings"]["set_style_type"] = key
            await state.update_data(settings=data["settings"])
            await state.update_data(state="to_stile")
            await self.settings_handler(callback , state)

        elif callback.data == "to_menu":
            await self.bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            await state.clear()
            await self.mane_menu(callback.message, state)
        elif callback.data == "back":
            await self.settings(callback.message, state)
        elif callback.data == "save":
            data = await state.get_data()
            self.db.set_user_settings(callback.from_user.id, data["settings"])
            await self.settings(callback.message, state)
        return

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


