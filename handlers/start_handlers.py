# handlers/start_handlers.py

from telebot.types import Message
from telebot import TeleBot
import logging
from texts import WELCOME_MESSAGE, ABOUT_MESSAGE, HELP_MESSAGE, MAIN_MESSAGE
from utils.api import api_get, api_post
from keyboards.inline import main_menu_keyboard

logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot):
    # @bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("/"))
    # def interrupt_fsm_on_command(message: Message):
    #     state = bot.get_state(message.from_user.id, message.chat.id)
    #     if state is not None:
    #         bot.delete_state(message.from_user.id, message.chat.id)
    #         bot.send_message(message.chat.id, "❌ Предыдущее действие отменено.")

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
            if not response or not response.get("valid"):
                bot.reply_to(message, "Эта ссылка недействительна или устарела.")
                return

            # Присоединяем пользователя к группе
            join_resp = api_post(
                f"join-group/{invite_code}", {"telegram_login": username}
            )
            if join_resp and "message" in join_resp:
                bot.reply_to(message, join_resp["message"])
            else:
                bot.reply_to(message, "Не удалось присоединиться к группе.")
            return

        # Добавление нового пользователя
        logger.info(f"Новый или повторный запуск /start от @{username}")
        api_post("user/add", {"telegram_login": username})

        # TODO: проверить, есть ли имя
        name = message.from_user.first_name or "Догорой друг"

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
            bot.send_message(message.chat.id, "Нет активного действия.")
            return

        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "❌ Действие отменено.")
