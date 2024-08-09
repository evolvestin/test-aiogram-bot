import asyncio
from config import API_TOKEN
from aiogram.utils import executor
from aiogram.types import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup


bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)  # Инициализация бота и диспетчера
dispatcher = Dispatcher(bot, storage=MemoryStorage())


async def send_reminder(chat_id: int):  # Функция отправки напоминания пользователю
    await bot.send_message(chat_id, 'Вы забыли ответить.')


class StateReminder(StatesGroup):  # Хранение состояний
    waiting_for_response = State()


class MiddlewareReminder(BaseMiddleware):  # Middleware для отслеживания ожидания ответа
    def __init__(self):
        super(MiddlewareReminder, self).__init__()

    @staticmethod
    async def on_process_message(message: types.Message, data: dict):
        # Состояние пользователя передается в data['state'], поэтому его не надо запрашивать
        if await data['state'].get_state() == StateReminder.waiting_for_response.state:
            await data['state'].finish()  # Сбрасываем состояние, если получен ответ от пользователя

    @staticmethod
    async def on_pre_process_message(message: types.Message, data: dict):
        state = dispatcher.current_state(chat=message.chat.id, user=message.from_user.id)  # Получение состояния
        if message.text.startswith('/start'):
            await state.finish()  # Сброс состояния, чтобы при отправленной команде /start она не являлась ответом


@dispatcher.message_handler(commands=['start'])  # Команда старт
async def send_welcome(message: types.Message):
    await StateReminder.waiting_for_response.set()  # Устанавливаем состояние
    await message.answer(f'Привет, {message.from_user.first_name}! Как ты сегодня?')  # Задаем вопрос пользователю
    await asyncio.sleep(15 * 60)  # Запуск таймера на 15 минут

    state = dispatcher.current_state(chat=message.chat.id, user=message.from_user.id)  # Получение состояния
    if await state.get_state() == StateReminder.waiting_for_response.state:
        await send_reminder(message.chat.id)


@dispatcher.message_handler(state=StateReminder.waiting_for_response)  # От для получения ответа
async def process_response(message: types.Message, state: FSMContext):
    await message.answer('Спасибо за ваш ответ!')  # Отвечаем пользователю
    await state.finish()  # Сброс состояния


dispatcher.middleware.setup(MiddlewareReminder())  # Установка нашего middleware в dispatcher


if __name__ == '__main__':
    executor.start_polling(dispatcher, skip_updates=True)  # Запуск бота (с помощью поллинга)
