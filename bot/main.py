# main.py
import logging
import telebot
from telebot import custom_filters
from telebot.storage import StateMemoryStorage

# from telebot.types import Message, CallbackQuery
from dotenv import load_dotenv
import os

from handlers import start_handlers, location_handlers, group_handlers

# from utils.states import AddLocationState, AddGroupState

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


storage = StateMemoryStorage()
storage.state_ttl = 300  # ⏱ 5 минут
# storage.update_types = ['message', 'callback_query', 'edited_message']
bot = telebot.TeleBot(
    BOT_TOKEN, state_storage=storage, use_class_middlewares=True, parse_mode="HTML"
)
# bot.setup_middleware(storage)

bot.add_custom_filter(custom_filters.StateFilter(bot))

# Регистрация всех обработчиков
start_handlers.register_handlers(bot)
location_handlers.register_handlers(bot)
group_handlers.register_handlers(bot)


# Запуск бота
if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()
