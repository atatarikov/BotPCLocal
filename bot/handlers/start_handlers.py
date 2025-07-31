# handlers/start_handlers.py

from telebot.types import Message
from telebot import TeleBot
import logging
from texts import WELCOME_MESSAGE, ABOUT_MESSAGE, HELP_MESSAGE, MAIN_MESSAGE
from utils.api import api_get, api_post, handle_api_error
from keyboards.inline import main_menu_keyboard, add_comm_main_menu, admin_menu_keyboard

logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot):

    @bot.message_handler(commands=["start"])
    def handle_start(message: Message):
        username = message.from_user.username
        args = message.text.split()

        # Deep link: /start join_abc123
        if len(args) > 1 and args[1].startswith("join_"):
            invite_code = args[1][len("join_"):]
            logger.info(
                f"Пользователь @{username} использует ссылку для присоединения: {invite_code}"
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
                f"join-group/{invite_code}", {"telegram_login": username}
            )
            if join_resp is None:
                handle_api_error(bot, message.chat.id)
                return

            if "message" in join_resp:
                bot.reply_to(message, add_comm_main_menu(join_resp["message"]))
            else:
                bot.reply_to(
                    message, add_comm_main_menu("Не удалось присоединиться к группе.")
                )
            return

        # Добавление нового пользователя
        logger.info(f"Новый или повторный запуск /start от @{username}")
        api_response = api_post("user/add", {"telegram_login": username})

        if api_response is None:
            handle_api_error(
                bot, message.chat.id, None, "Не удалось зарегистрировать пользователя"
            )
            return

        name = message.from_user.first_name or "Дорогой друг"
        bot.send_message(
            message.chat.id,
            text=WELCOME_MESSAGE.format(name=name),
            reply_markup=main_menu_keyboard(),
        )

    @bot.message_handler(commands=["about"])
    def handle_about(message: Message):
        bot.send_message(
            message.chat.id,
            text=ABOUT_MESSAGE,
            reply_markup=main_menu_keyboard(),
        )

    @bot.message_handler(commands=["help"])
    def handle_help(message: Message):
        bot.send_message(
            message.chat.id,
            text=HELP_MESSAGE,
            reply_markup=main_menu_keyboard(),
        )

    @bot.message_handler(commands=["main"])
    def handle_main(message: Message):
        bot.send_message(
            message.chat.id,
            text=MAIN_MESSAGE,
            reply_markup=main_menu_keyboard(),
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
