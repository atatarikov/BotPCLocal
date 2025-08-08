# handlers/start_handlers.py

from telebot.types import Message
from telebot import TeleBot
import logging
from utils.texts import (
    ABOUT_MESSAGE,
    HELP_MESSAGE,
    main_message
)
from utils.api import (
    api_get,
    api_post,
    handle_api_error,
    get_training_stage,
)
from keyboards.inline import (
    main_menu_keyboard,
    add_comm_main_menu,
    admin_menu_keyboard,
)

logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot):

    @bot.message_handler(commands=["start", "main"])
    def handle_start(message: Message):
        user_tg = message.from_user
        # storage = UserStorage(bot, user_tg.id, message.chat.id)
        # Если training_stage есть, то мы уже получали пользователя, т.е. он есть уже в базе
        # training_stage = storage.get_data("training_stage")

        training_stage = get_training_stage(bot, user_tg, message.chat.id)
        args = message.text.split()
        # Deep link: /start join_abc123
        if len(args) > 1 and args[1].startswith("join_"):
            # invite_code = args[1][len("join_") :] Иде, постоянно ошибку показывал пеп
            invite_code = args[1].split("join_", 1)[1]
            logger.info(
                f"@{user_tg.username} использует ссылку приглашения: {invite_code}"
            )

            # Проверка валидности ссылки
            response = api_get(f"check-invite-code/{invite_code}")
            if response is None:
                handle_api_error(bot, message.chat.id)
                return

            if not response.get("valid"):
                bot.reply_to(
                    message,
                    add_comm_main_menu("Эта ссылка недействительна или устарела."),
                )
                return

            # Присоединяем пользователя к группе
            join_resp = api_post(
                f"join-group/{invite_code}", {"telegram_id": user_tg.id}
            )
            if join_resp is None:
                handle_api_error(bot, message.chat.id)
                return

            join_msg = join_resp.get("message", "Не удалось присоединиться к группе.")
            bot.reply_to(message, add_comm_main_menu(join_msg))

            # Если пользователь уже был в группе, НЕ отправляем ещё одно приветствие
            # if "уже состоите" in join_msg.lower():
            #     return

        # Основное сообщение
        first_name = user_tg.first_name or "Дорогой друг"
        bot.send_message(
            message.chat.id,
            text=main_message(training_stage).format(first_name=first_name),
            reply_markup=main_menu_keyboard(bot, user_tg, message.chat.id),
        )

    @bot.message_handler(commands=["about"])
    def handle_about(message: Message):

        bot.send_message(
            message.chat.id,
            text=ABOUT_MESSAGE,
            reply_markup=main_menu_keyboard(bot, message.from_user, message.chat.id),
        )

    @bot.message_handler(commands=["help"])
    def handle_help(message: Message):
        text = HELP_MESSAGE

        bot.send_message(
            message.chat.id,
            text=text,
            reply_markup=main_menu_keyboard(bot, message.from_user, message.chat.id),
        )

    @bot.message_handler(commands=["cancel"])
    def cancel_fsm(message: Message):
        state = bot.get_state(message.from_user.id, message.chat.id)
        if state is None:
            bot.send_message(
                message.chat.id, add_comm_main_menu("Нет активного действия.")
            )
            return

        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, add_comm_main_menu("❌ Действие отменено."))

    @bot.message_handler(commands=["admin03"])
    def admin03(message: Message):
        bot.send_message(
            message.chat.id,
            text="Вы попали в скрытое меню",
            reply_markup=admin_menu_keyboard(),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def handle_main_menu_callback(call):
        # Основное сообщение
        bot.answer_callback_query(callback_query_id=call.id)
        first_name = call.from_user.first_name or "Дорогой друг"
        training_stage = get_training_stage(bot, call.from_user, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            text=main_message(training_stage).format(first_name=first_name),
            reply_markup=main_menu_keyboard(bot, call.from_user, call.message.chat.id),
        )
