import asyncio
import logging
from typing import Dict, List, Callable, Any
from collections import defaultdict
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties


# ---------------------------
# КЛАССЫ ДЛЯ ОЧЕРЕДИ И ЗАДАЧ
# ---------------------------
@dataclass
class Task:
    user_id: int
    function: Callable
    args: tuple
    kwargs: dict
    priority: int = 0


class TaskQueue:
    """
    Очередь задач для выполнения функций между пользователями
    """

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.current_tasks: Dict[int, asyncio.Task] = {}

    async def add_task(self, task: Task):
        """Добавление задачи в очередь"""
        await self.queue.put(task)

    async def process_tasks(self):
        """Обработчик очереди задач"""
        self.is_running = True
        while self.is_running:
            try:
                task = await self.queue.get()
                # ВСТАВЬТЕ ВАШУ ЛОГИКУ ПРИОРИТЕТОВ ЗДЕСЬ

                # Выполнение задачи
                if task.user_id not in self.current_tasks:
                    self.current_tasks[task.user_id] = asyncio.create_task(
                        self._execute_task(task)
                    )
                else:
                    # Если у пользователя уже есть задача, ждем ее завершения
                    await self.current_tasks[task.user_id]
                    self.current_tasks[task.user_id] = asyncio.create_task(
                        self._execute_task(task)
                    )

                self.queue.task_done()
            except Exception as e:
                logging.error(f"Ошибка обработки задачи: {e}")

    async def _execute_task(self, task: Task):
        """Выполнение конкретной задачи"""
        try:
            await task.function(*task.args, **task.kwargs)
        except Exception as e:
            logging.error(f"Ошибка выполнения задачи: {e}")
        finally:
            if task.user_id in self.current_tasks:
                del self.current_tasks[task.user_id]

    async def stop(self):
        """Остановка обработчика очереди"""
        self.is_running = False


# ---------------------------
# ОСНОВНОЙ КЛАСС БОТА
# ---------------------------
class TelegramBot:
    def __init__(self, token: str):
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        self.dp = Dispatcher()

        # Система очередей
        self.task_queue = TaskQueue()
        self.user_states: Dict[int, str] = {}  # Состояния пользователей
        self.user_data: Dict[int, Dict] = defaultdict(dict)  # Данные пользователей

        # Регистрация обработчиков
        self._register_handlers()

    def _register_handlers(self):
        """Регистрация всех обработчиков сообщений"""
        self.dp.message.register(self._cmd_start, Command('start'))
        self.dp.message.register(self._cmd_help, Command('help'))
        self.dp.message.register(self._cmd_queue_info, Command('queue'))
        self.dp.message.register(self._handle_message)

    # ---------------------------
    # ОЧЕРЕДЬ ЗАДАЧ - ВАША ЛОГИКА
    # ---------------------------
    async def add_to_queue(self, user_id: int, function: Callable, *args, **kwargs):
        """
        Добавление задачи в очередь
        Используйте этот метод для выполнения функций через очередь
        """
        task = Task(user_id=user_id, function=function, args=args, kwargs=kwargs)
        await self.task_queue.add_task(task)

    async def process_long_task(self, user_id: int, duration: int):
        """
        Пример долгой задачи - ЗАМЕНИТЕ НА СВОЮ ЛОГИКУ
        """
        user_data = self.user_data[user_id]
        user_data['processing'] = True

        # Имитация долгой задачи
        for i in range(duration):
            if not user_data.get('processing', True):
                break

            progress = (i + 1) / duration * 100
            await self.bot.send_message(
                user_id,
                f"⏳ Обработка... {progress:.1f}%"
            )
            await asyncio.sleep(1)

        user_data['processing'] = False
        await self.bot.send_message(user_id, "✅ Задача завершена!")

    # ---------------------------
    # ОБРАБОТЧИКИ КОМАНД - ВАША ЛОГИКА
    # ---------------------------
    async def _cmd_start(self, message: types.Message):
        """Обработчик команды /start"""
        # ВСТАВЬТЕ ВАШ КОД ЗДЕСЬ
        await message.answer(
            "🚀 Бот запущен!\n"
            "Используйте /process для запуска задачи\n"
            "Используйте /queue для информации об очереди"
        )

    async def _cmd_help(self, message: types.Message):
        """Обработчик команды /help"""
        # ВСТАВЬТЕ ВАШ КОД ЗДЕСЬ
        help_text = """
📖 Доступные команды:
/start - запуск бота
/help - помощь
/process - запустить обработку
/queue - информация об очереди
/cancel - отмена текущей задачи
        """
        await message.answer(help_text)

    async def _cmd_queue_info(self, message: types.Message):
        """Информация об очереди"""
        # ВСТАВЬТЕ ВАШУ ЛОГИКУ СТАТИСТИКИ ОЧЕРЕДИ ЗДЕСЬ
        queue_size = self.task_queue.queue.qsize()
        active_users = len(self.task_queue.current_tasks)

        await message.answer(
            f"📊 Статистика очереди:\n"
            f"• Задач в очереди: {queue_size}\n"
            f"• Активных пользователей: {active_users}\n"
            f"• Ваш статус: {'В обработке' if message.from_user.id in self.task_queue.current_tasks else 'Свободен'}"
        )

    async def _cmd_process(self, message: types.Message):
        """Запуск обработки через очередь"""
        # ВСТАВЬТЕ ВАШУ ЛОГИКУ ЗАПУСКА ЗАДАЧ ЗДЕСЬ
        user_id = message.from_user.id

        if user_id in self.task_queue.current_tasks:
            await message.answer("⏳ Ваша задача уже выполняется...")
            return

        await message.answer("📥 Задача добавлена в очередь...")

        # Добавление задачи в очередь
        await self.add_to_queue(
            user_id=user_id,
            function=self.process_long_task,
            user_id=user_id,
            duration=5  # Параметры вашей задачи
        )

    async def _cmd_cancel(self, message: types.Message):
        """Отмена текущей задачи"""
        # ВСТАВЬТЕ ВАШУ ЛОГИКУ ОТМЕНЫ ЗДЕСЬ
        user_id = message.from_user.id

        if user_id in self.user_data and self.user_data[user_id].get('processing'):
            self.user_data[user_id]['processing'] = False
            await message.answer("❌ Задача отменена")
        else:
            await message.answer("ℹ️ У вас нет активных задач")

    async def _handle_message(self, message: types.Message):
        """Обработчик произвольных сообщений"""
        # ВСТАВЬТЕ ВАШ КОД ЗДЕСЬ
        user_id = message.from_user.id

        # Пример обработки текстовых команд
        if message.text.lower() == 'статус':
            status = "обрабатывается" if user_id in self.task_queue.current_tasks else "свободен"
            await message.answer(f"Ваш статус: {status}")
        else:
            await message.answer(f"Вы сказали: {message.text}")

    # ---------------------------
    # СИСТЕМНЫЕ МЕТОДЫ
    # ---------------------------
    async def on_startup(self):
        """Действия при запуске бота"""
        # Запуск обработчика очереди
        asyncio.create_task(self.task_queue.process_tasks())

        # ВСТАВЬТЕ ВАШ КОД ИНИЦИАЛИЗАЦИИ ЗДЕСЬ
        logging.info("Бот запущен и готов к работе")

    async def on_shutdown(self):
        """Действия при остановке бота"""
        await self.task_queue.stop()
        # ВСТАВЬТЕ ВАШ КОД ОЧИСТКИ ЗДЕСЬ
        logging.info("Бот остановлен")

    async def run(self):
        """Запуск бота"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )

        self.dp.startup.register(self.on_startup)
        self.dp.shutdown.register(self.on_shutdown)

        # Удаляем вебхук и запускаем поллинг
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)


# ---------------------------
# ЗАПУСК БОТА
# ---------------------------
if __name__ == "__main__":
    # ЗАМЕНИТЕ НА ВАШ ТОКЕН
    BOT_TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN"

    bot = TelegramBot(BOT_TOKEN)

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Бот остановлен")