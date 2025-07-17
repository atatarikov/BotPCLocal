# handlers/location_handlers.py

from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)
import logging

from utils.api import api_get, api_post, api_delete
from utils.states import AddLocationState
from keyboards.inline import MAIN_MENU, location_action_keyboard, add_comm_mail_menu


logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda call: call.data == "locations")
    def locations_menu(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        markup = location_action_keyboard()
        bot.edit_message_text(
            add_comm_mail_menu("Что вы хотите сделать с локациями?"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
        )

    @bot.callback_query_handler(func=lambda call: call.data == "list_locations")
    def list_user_locations(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        username = call.from_user.username

        locations = api_get(f"users/{username}/locations")
        if not locations:
            bot.edit_message_text(
                add_comm_mail_menu("У вас нет сохранённых локаций."),
                call.message.chat.id,
                call.message.message_id,
            )
            return

        bot.edit_message_text(
            "Ваши локации:", call.message.chat.id, call.message.message_id
        )
        for loc in locations:
            text = f"📍 <b>{loc['description']}</b>\nКоординаты: ({loc['latitude']}, {loc['longitude']})"
            keyboard = location_action_keyboard(loc["id"])
            bot.send_message(call.message.chat.id, text, reply_markup=keyboard)
        bot.send_message(call.message.chat.id, MAIN_MENU)

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("delete_location_")
    )
    def delete_location(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        location_id = call.data.split("_")[-1]
        username = call.from_user.username

        result = api_delete(f"users/{username}/locations/{location_id}")
        if result:
            bot.edit_message_text(
                "Локация успешно удалена.",
                call.message.chat.id,
                call.message.message_id,
            )
        else:
            bot.edit_message_text(
                add_comm_mail_menu("Ошибка при удалении локации."),
                call.message.chat.id,
                call.message.message_id,
            )

    @bot.callback_query_handler(func=lambda call: call.data == "add_location")
    def start_add_location(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "Введите описание для новой локации или отмените добавление /cancel :",
            call.message.chat.id,
            call.message.message_id,
        )
        bot.set_state(
            call.from_user.id, AddLocationState.description, call.message.chat.id
        )

    @bot.message_handler(state=AddLocationState.description)
    def receive_description(message: Message):
        # пример как кнопку геолокации передать
        # markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        # location_button = KeyboardButton(
        #     "📍Поделиться локацией",
        #     request_location=True
        # )
        # markup.add(location_button)
        # bot.send_message(message.chat.id, "Теперь отправьте геопозицию 📍", reply_markup=markup)
        bot.send_message(
            message.chat.id, "Теперь отправьте геопозицию 📍(по📎любую геопозицию) или отмените добавление /cancel"
        )
        bot.set_state(message.from_user.id, AddLocationState.location, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["description"] = message.text

    @bot.message_handler(content_types=["location"], state=AddLocationState.location)
    def receive_location(message: Message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            description = data.get("description", "")
            location = message.location
            username = message.from_user.username

            payload = {
                "telegram_login": username,
                "description": description,
                "latitude": location.latitude,
                "longitude": location.longitude,
            }

            result = api_post("add-location", payload)
            if result:
                bot.send_message(
                    message.chat.id,
                    add_comm_mail_menu("Локация успешно добавлена ✅"),
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                bot.send_message(
                    message.chat.id,
                    add_comm_mail_menu("Произошла ошибка при добавлении локации"),
                    reply_markup=ReplyKeyboardRemove(),
                )

        bot.delete_state(message.from_user.id, message.chat.id)

    @bot.message_handler(state=AddLocationState.location)
    def invalid_location(message: Message):
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, отправьте именно геопозицию, используя 📎 или отмените добавление /cancel"
        )
