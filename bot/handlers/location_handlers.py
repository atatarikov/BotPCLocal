# handlers/location_handlers.py

from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)
import logging

from utils.api import api_get, api_post, api_delete, handle_api_error
from utils.states import AddLocationState
from keyboards.inline import MAIN_MENU, location_action_keyboard, add_comm_main_menu


logger = logging.getLogger(__name__)

ALL_CONTENT_TYPES = [
    "text",
    "audio",
    "document",
    "photo",
    "sticker",
    "video",
    "voice",
    "video_note",
    "contact",
    "location",
    "venue",
    "animation",
]


def register_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda call: call.data == "locations")
    def locations_menu(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        markup = location_action_keyboard()
        bot.edit_message_text(
            add_comm_main_menu("Что вы хотите сделать с локациями?"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
        )

    @bot.callback_query_handler(func=lambda call: call.data == "list_locations")
    def list_user_locations(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        username = call.from_user.username

        locations = api_get(f"users/{username}/locations")

        if locations is None:
            handle_api_error(bot, call.message.chat.id, call.message.message_id)
            return

        if not locations:
            bot.edit_message_text(
                add_comm_main_menu("У вас нет сохранённых локаций."),
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

        if result is None:
            handle_api_error(bot, call.message.chat.id, call.message.message_id)
            return

        if result:
            bot.edit_message_text(
                add_comm_main_menu("Локация успешно удалена."),
                call.message.chat.id,
                call.message.message_id,
            )
        else:
            bot.edit_message_text(
                add_comm_main_menu("Ошибка при удалении локации."),
                call.message.chat.id,
                call.message.message_id,
            )

    @bot.callback_query_handler(func=lambda call: call.data == "add_location")
    def start_add_location(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            ("Введите описание для новой локации\n" "или отмените добавление /cancel"),
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
            message.chat.id,
            (
                "📍 Теперь, отправьте геопозицию через 📎 (кнопка 'Прикрепить' -> 'Геопозиция')\n"
                "или отмените добавление /cancel"
            ),
        )
        bot.set_state(message.from_user.id, AddLocationState.location, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["description"] = message.text

    @bot.message_handler(
        state=AddLocationState.location, content_types=ALL_CONTENT_TYPES
    )
    def handle_location_state(message: Message):

        if message.content_type == "location":
            latitude = message.location.latitude
            longitude = message.location.longitude
            venue_parts = []
        elif message.content_type == "venue":
            latitude = message.venue.location.latitude
            longitude = message.venue.location.longitude
            venue_parts = []
            if message.venue.title:
                venue_parts.append(message.venue.title)
            if message.venue.address:
                venue_parts.append(message.venue.address)
        else:
            warning_msg = (
                "❌ Вы находитесь в режиме добавления локации.\n"
                "Пожалуйста, отправьте геопозицию через 📎 (кнопка 'Прикрепить' -> 'Геопозиция' или 'Место')\n"
                "Или отправьте /cancel для отмены"
            )
            bot.send_message(message.chat.id, warning_msg)

            logger.warning(
                f"User {message.from_user.id} sent wrong content type in location state: "
                f"{message.content_type}"
            )
            return  # Выходим из функции, чтобы не выполнять остальной код

        # Обработка location или venue
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            base_description = data.get("description", "")
            username = message.from_user.username

            if venue_parts:
                venue_info = ", ".join(venue_parts)
                description = (
                    f"{base_description} ({venue_info})"
                    if base_description
                    else f"({venue_info})"
                )
            else:
                description = base_description

            payload = {
                "telegram_login": username,
                "description": description,
                "latitude": latitude,
                "longitude": longitude,
            }

            result = api_post("add-location", payload)

            if result is None:
                handle_api_error(bot, message.chat.id)
            elif result:
                bot.send_message(
                    message.chat.id,
                    add_comm_main_menu("Локация успешно добавлена ✅"),
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                bot.send_message(
                    message.chat.id,
                    add_comm_main_menu("Произошла ошибка при добавлении локации"),
                    reply_markup=ReplyKeyboardRemove(),
                )

        bot.delete_state(message.from_user.id, message.chat.id)
