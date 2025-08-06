# utils/states.py

from telebot.handler_backends import State, StatesGroup


class AddLocationState(StatesGroup):
    description = State()
    location = State()


class AddGroupState(StatesGroup):
    title = State()


class UserStorage:
    def __init__(self, bot, user_id, chat_id):
        self.bot = bot
        self.user_id = user_id
        self.chat_id = chat_id

    # --- State ---
    def get_state(self):
        return self.bot.get_state(self.user_id, self.chat_id)

    def set_state(self, state):
        self.bot.set_state(self.user_id, self.chat_id, state)

    def delete_state(self):
        self.bot.delete_state(self.user_id, self.chat_id)

    # --- Data ---
    def get_data(self, key, default=None):
        with self.bot.retrieve_data(self.user_id, self.chat_id) as data:
            return data.get(key, default)

    def set_data(self, key, value):
        with self.bot.retrieve_data(self.user_id, self.chat_id) as data:
            data[key] = value

    def update_data(self, data_dict):
        with self.bot.retrieve_data(self.user_id, self.chat_id) as data:
            data.update(data_dict)

    def reset_data(self):
        self.bot.reset_data(self.user_id, self.chat_id)

    def all_data(self):
        with self.bot.retrieve_data(self.user_id, self.chat_id) as data:
            return dict(data)  # возвращаем копию
