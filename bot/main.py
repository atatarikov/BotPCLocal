# main.py
import logging
import telebot
from telebot import custom_filters
from telebot.storage import StateRedisStorage, StateMemoryStorage

# from telebot.types import Message, CallbackQuery
from dotenv import load_dotenv
import os

from handlers import start_handlers, location_handlers, group_handlers, training_handlers

# from utils.states import AddLocationState, AddGroupState

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    storage = StateRedisStorage(
        host=REDIS_HOST, port=6379, db=0, prefix="fsm"
    )  # важно: host='redis', как в docker-compose
    storage.set_data("test_key", "test_value")
    value = storage.get_data("test_key")
except Exception as e:
    print(f"Ошибка Redis: {e}")
    storage = StateMemoryStorage()

# storage.state_ttl = 300  # ⏱ 5 минут
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
training_handlers.register_handlers(bot)


# Запуск бота
if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()
