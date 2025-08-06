from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from telebot.types import Message

# Токен бота
BOT_TOKEN = "6985414096:AAHzDV9aRot6PQfrljZ_yPtByy99_Z24CWM"

# Создаем хранилище состояний
storage = StateMemoryStorage()

# Создаем экземпляр бота с использованием хранилища состояний
bot = TeleBot(BOT_TOKEN, state_storage=storage, use_class_middlewares=True)

# Обработчик команды /test
@bot.message_handler(commands=["test"])
def handle_test(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Проверяем наличие данных в хранилище для текущего пользователя
    with bot.retrieve_data(user_id, chat_id) as data:
        # Получаем значение счетчика или устанавливаем начальное значение
        counter = data.get('counter', 0)

        # Увеличиваем счетчик
        counter += 1

        # Сохраняем обновленное значение обратно в хранилище
        data['counter'] = counter

    # Отправляем сообщение с новым значением счетчика
    bot.send_message(chat_id, f"Counter = {counter}")

# Запускаем бесконечный цикл опроса сообщений
if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()