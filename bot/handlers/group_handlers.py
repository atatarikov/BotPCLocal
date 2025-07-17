# handlers/group_handlers.py

from telebot import TeleBot
from telebot.types import CallbackQuery, Message
import logging
from config import BOT_NAME
from utils.api import api_get, api_post, api_delete
from utils.states import AddGroupState
from keyboards.inline import (
    admin_groups_keyboard,
    user_groups_keyboard,
    delete_group_button,
    MAIN_MENU,
    add_comm_main_menu,
)

logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda call: call.data == "my_groups")
    def show_user_groups(call: CallbackQuery):
        username = call.from_user.username
        bot.answer_callback_query(call.id)

        groups = api_get(f"users/{username}/groups")
        if not groups:
            bot.edit_message_text(
                add_comm_main_menu(
                    f"""Вы не участвуете ни в одной группе. Попросите ссылку на вступление у Администратора группы.

так же вы можете присоединиться к глобальной группе https://t.me/{BOT_NAME}?start=join_klub-piterskikh-odinesnikov"""
                ),
                call.message.chat.id,
                call.message.message_id,
            )
            return

        bot.edit_message_text(
            "Ваши группы:", call.message.chat.id, call.message.message_id
        )
        for group in groups:
            bot.send_message(
                call.message.chat.id,
                f"📌 Группа: <b>{group['title']}</b>",
                # TODO сделать ссылку на карту группы
                # LinkGroup = f'{API_URL}/{group["id"]}'
                # f"📌 Группа: <b>{group['title']}</b>\n 🗺️ карта группы: {LinkGroup}"
                reply_markup=user_groups_keyboard(group["id"]),
            )
        bot.send_message(call.message.chat.id, MAIN_MENU)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("leave_group_"))
    def leave_group(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        group_id = call.data.split("_")[-1]
        username = call.from_user.username

        result = api_delete(f"leave-group/{group_id}", {"telegram_login": username})
        msg = (
            result.get("message", "Ошибка при выходе из группы.")
            if result
            else "Ошибка соединения с API."
        )
        bot.edit_message_text(add_comm_main_menu(msg), call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_groups")
    def admin_menu(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        markup = admin_groups_keyboard()
        bot.edit_message_text(
            "Выберите действие:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )

    @bot.callback_query_handler(func=lambda call: call.data == "list_managed_groups")
    def list_managed_groups(call: CallbackQuery):
        username = call.from_user.username
        bot.answer_callback_query(call.id)

        groups = api_get(f"admin-groups/{username}")
        if not groups:
            bot.edit_message_text(
                add_comm_main_menu("У вас нет групп, которыми вы управляете."),
                call.message.chat.id,
                call.message.message_id,
            )
            return

        bot.edit_message_text(
            "Вы управляете этими группами:",
            call.message.chat.id,
            call.message.message_id,
        )
        for group in groups:
            link = f"https://t.me/{BOT_NAME}?start=join_{group['group_link']}"
            text = f"📍 <b>{group['title']}</b>\n🔗 Ссылка для приглашения: {link}"
            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=delete_group_button(group["id"]),
            )
        bot.send_message(call.message.chat.id, MAIN_MENU)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_group_"))
    def delete_group(call: CallbackQuery):
        group_id = call.data.split("_")[-1]
        username = call.from_user.username
        result = api_delete(f"delete-group/{group_id}/{username}")
        if result:
            bot.edit_message_text(
                add_comm_main_menu("Группа удалена."), call.message.chat.id, call.message.message_id
            )
        else:
            bot.edit_message_text(
                add_comm_main_menu("Ошибка при удалении группы."),
                call.message.chat.id,
                call.message.message_id,
            )

    @bot.callback_query_handler(func=lambda call: call.data == "add_manage_group")
    def add_group_title(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "Введите название новой группы:",
            call.message.chat.id,
            call.message.message_id,
        )
        bot.set_state(call.from_user.id, AddGroupState.title, call.message.chat.id)

    @bot.message_handler(state=AddGroupState.title)
    def receive_group_title(message: Message):
        title = message.text
        username = message.from_user.username

        payload = {"title": title, "telegram_login": username}

        result = api_post("add-group", payload)

        if result and "group_link" in result:
            link = f"https://t.me/{BOT_NAME}?start=join_{result['group_link']}"
            bot.send_message(
                message.chat.id, f"Группа создана ✅\n🔗 Ссылка для приглашения: {link}"
            )
            bot.send_message(message.chat.id, MAIN_MENU)

        else:
            bot.send_message(message.chat.id, add_comm_main_menu("Ошибка при создании группы."))

        bot.delete_state(message.from_user.id, message.chat.id)
