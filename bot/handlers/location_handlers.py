# handlers/location_handlers.py

from telebot import TeleBot
from telebot.types import CallbackQuery, Message
import logging
from config import FINAL_STAGE_TRAINING
from utils.api import (
    api_get,
    api_post,
    api_delete,
    handle_api_error,
    get_training_stage,
    update_training_stage,
)
from utils.states import AddLocationState
from keyboards.inline import (
    location_action_keyboard,
    add_another_location,
    main_menu_keyboard,
)
from utils.texts import main_message


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
        bot.send_message(
            call.message.chat.id,
            "Что вы хотите сделать с локациями?",
            reply_markup=location_action_keyboard(),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "list_locations")
    def list_user_locations(call: CallbackQuery):
        bot.answer_callback_query(call.id)

        result, e = api_get(f"user/{call.from_user.id}/locations")

        if e:
            handle_api_error(bot, call.message.chat.id, call.message.message_id)
            return
        locations = result["data"]
        if not locations:
            bot.send_message(
                call.message.chat.id,
                "У вас нет сохранённых локаций.",
                reply_markup=add_another_location(call.from_user),
            )
            return

        bot.send_message(
            call.message.chat.id,
            "Ваши локации:",
        )
        for loc in locations:
            text = f"📍 <b>{loc['description']}</b>\nКоординаты: ({loc['latitude']}, {loc['longitude']})"
            keyboard = location_action_keyboard(loc["id"])
            bot.send_message(call.message.chat.id, text, reply_markup=keyboard)
        bot.send_message(
            call.message.chat.id, "Что ты хочешь сделать дальше?", reply_markup=add_another_location(call.from_user)
        )

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("delete_location_")
    )
    def delete_location(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        location_id = call.data.split("_")[-1]
        payload = {"telegram_id": call.from_user.id}
        result, e = api_delete(f"location/{location_id}/delete", payload)

        if e:
            handle_api_error(bot, call.message.chat.id, call.message.message_id)
            return

        if result:
            bot.send_message(
                call.message.chat.id,
                result["message"],
                reply_markup=add_another_location(call.from_user),
            )
        else:
            bot.send_message(
                call.message.chat.id,
                "Ошибка при удалении локации.",
                location_action_keyboard(),
            )

    @bot.callback_query_handler(func=lambda call: call.data == "add_location")
    def start_add_location(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            ("Введи описание для новой локации\n" "или отмените добавление /cancel"),
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
                "⚠️Можно приблезительную, помни о безопасности!⚠️\n"
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
                "❌ Ты находишся в режиме добавления локации.\n"
                "Пожалуйста, отправь геопозицию через 📎 (кнопка 'Прикрепить' -> 'Геопозиция' или 'Место')\n"
                "Или отправь /cancel для отмены"
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
                "telegram_id": message.from_user.id,
                "description": description,
                "latitude": latitude,
                "longitude": longitude,
            }

            result, e = api_post("location/add", payload)

            if e:
                handle_api_error(bot, message.chat.id)
                return

            training_stage = get_training_stage(bot, message.from_user, message.chat.id)

            if training_stage < FINAL_STAGE_TRAINING:
                if training_stage < 3:
                    training_stage = 3
                    training_stage, error = update_training_stage(
                        bot, message.from_user.id, training_stage, message.chat.id
                    )
                    if error:
                        return
                bot.send_message(
                    message.chat.id,
                    text=main_message(training_stage).format(
                        first_name=message.from_user.first_name
                    ),
                    reply_markup=main_menu_keyboard(
                        bot, message.from_user, message.chat.id
                    ),
                )
                return
            bot.send_message(
                message.chat.id,
                ("Локация успешно добавлена ✅\n мошешь добавить еще точки 🤗"),
                reply_markup=add_another_location(message.from_user),
            )

        bot.delete_state(message.from_user.id, message.chat.id)
