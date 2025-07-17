# utils/states.py

from telebot.handler_backends import State, StatesGroup


class AddLocationState(StatesGroup):
    description = State()
    location = State()


class AddGroupState(StatesGroup):
    title = State()
