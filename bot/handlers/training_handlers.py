from telebot.types import Message, ReplyKeyboardRemove, CallbackQuery
from telebot import TeleBot
import logging
from config import FINAL_STAGE_TRAINING
from utils.texts import (
    main_message,
    MAIN_MESSAGE_S4_FiNAL_TRANING,
)
from utils.api import (
    api_get,
    handle_api_error,
    update_training_stage,
)
from keyboards.inline import (
    main_menu_keyboard,
    location_action_keyboard,
)


logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot):

    @bot.message_handler(commands=["skip_training"])
    def skip_training(message: Message):
        training_stage = FINAL_STAGE_TRAINING
        training_stage, error = update_training_stage(
            bot, message.from_user.id, training_stage, message.chat.id
        )
        if error:
            return
        bot.send_message(
            message.chat.id,
            text="Отлично, как тольо у нас появится что-то новое, я дам тебе знать.\nТы всегда можешь пройти обучение заного /repeat_training",
            reply_markup=ReplyKeyboardRemove(),
        )
        bot.send_message(
            message.chat.id,
            text=main_message(training_stage).format(
                first_name=message.from_user.first_name
            ),
            reply_markup=main_menu_keyboard(bot, message.from_user, message.chat.id),
        )

    @bot.message_handler(commands=["repeat_training"])
    def repeat_training(message: Message):
        training_stage = 0
        training_stage, error = update_training_stage(
            bot, message.from_user.id, training_stage, message.chat.id
        )
        if error:
            return
        bot.send_message(
            message.chat.id,
            text="Отлично, наченем сначала.\nТы всегда можешь пропусть /skip_training",
            reply_markup=ReplyKeyboardRemove(),
        )
        bot.send_message(
            message.chat.id,
            text=main_message(training_stage).format(
                first_name=message.from_user.first_name
            ),
            reply_markup=main_menu_keyboard(bot, message.from_user, message.chat.id),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "training_start_map")
    def training_start_map(call):
        bot.answer_callback_query(callback_query_id=call.id)
        first_name = call.from_user.first_name or "Дорогой друг"
        training_stage = 1
        training_stage, error = update_training_stage(
            bot, call.from_user.id, training_stage, call.message.chat.id
        )
        if error:
            handle_api_error(bot, call.message.chat.id)
            return

        bot.send_message(
            call.message.chat.id,
            text=main_message(training_stage).format(first_name=first_name),
            reply_markup=main_menu_keyboard(bot, call.from_user, call.message.chat.id),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "training_add_location")
    def training_add_location(call):
        bot.answer_callback_query(callback_query_id=call.id)
        first_name = call.from_user.first_name or "Дорогой друг"
        training_stage = 2
        training_stage, error = update_training_stage(
            bot, call.from_user.id, training_stage, call.message.chat.id
        )
        if error:
            handle_api_error(bot, call.message.chat.id)
            return
        bot.send_message(
            call.message.chat.id,
            text=main_message(training_stage).format(first_name=first_name),
            reply_markup=main_menu_keyboard(bot, call.from_user, call.message.chat.id),
        )

    @bot.callback_query_handler(
        func=lambda call: call.data == "training_list_locations"
    )
    def training_list_locations(call: CallbackQuery):
        bot.answer_callback_query(call.id)

        result, e = api_get(f"user/{call.from_user.id}/locations")

        if e:
            handle_api_error(bot, call.message.chat.id, call.message.message_id)
            return
        locations = result["data"]
        if not locations:

            bot.send_message(
                call.message.chat.id,
                "У вас нет сохранённых локаций. Давай добавим точку",
            )
            training_add_location(call)
            return

        bot.send_message(
            call.message.chat.id,
            "Твои локации:",
        )
        for loc in locations:
            text = f"📍 <b>{loc['description']}</b>\nКоординаты: ({loc['latitude']}, {loc['longitude']})"
            keyboard = location_action_keyboard(loc["id"])
            bot.send_message(call.message.chat.id, text, reply_markup=keyboard)
        training_stage = FINAL_STAGE_TRAINING
        training_stage, error = update_training_stage(
            bot, call.from_user.id, training_stage, call.message.chat.id
        )
        if error:
            handle_api_error(bot, call.message.chat.id)
            return
        bot.send_message(
            call.message.chat.id,
            text=MAIN_MESSAGE_S4_FiNAL_TRANING,
            reply_markup=main_menu_keyboard(bot, call.from_user, call.message.chat.id),
        )
