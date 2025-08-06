# keyboards/inline.py
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, User
from config import MAP_URL, FINAL_STAGE_TRAINING


MAIN_MENU = "/main - Главное меню"


def add_comm_main_menu(txt: str):
    return txt + "\n" + MAIN_MENU


def main_menu_keyboard(bot: TeleBot, user_tg: User, chat_id):
    from utils.api import get_training_stage

    # storage = UserStorage(bot, user_tg.id, chat_id)
    # training_stage = storage.get_data("training_stage")

    training_stage = get_training_stage(bot, user_tg, chat_id)

    if training_stage < FINAL_STAGE_TRAINING:
        return training_keyboard(user_tg, training_stage)

    markup = InlineKeyboardMarkup(row_width=1)

    map_url_with_user = MAP_URL
    # map_url_with_user = f"{MAP_URL}?uid={user_tg.id}&nts=1"
    markup.add(InlineKeyboardButton("Открыть карту 🌍", url=map_url_with_user))

    markup.add(InlineKeyboardButton("Мои локации📍", callback_data="locations"))

    markup.add(InlineKeyboardButton("Главное меню 🏠", callback_data="main_menu"))

    return markup


def training_keyboard(user_tg: User, training_stage: int):

    markup = InlineKeyboardMarkup(row_width=1)

    if training_stage == 0:
        markup.add(
            InlineKeyboardButton(
                "Начать обучение🤓", callback_data="training_start_map"
            )
        )
        return markup

    # Стадия 1 Открыть карту
    if training_stage == 1:
        map_url_with_user = MAP_URL
        # if training_stage == 0:
        #     map_url_with_user = f"{MAP_URL}?uid={user_tg.id}&nts=1"

        markup.add(InlineKeyboardButton("🌍 Открой карту, ШАГ 1 🤓", url=map_url_with_user))

        markup.add(
            InlineKeyboardButton(
                "📍Научись добавлять локации, ШАГ 2 🤓", callback_data="training_add_location"
            )
        )
        return markup

        # Стадия 1  Добавить локацию
    if training_stage == 2:
        markup.add(
            InlineKeyboardButton("Добавить локацию 📍, ШАГ 2", callback_data="add_location")
        )

    if training_stage == 3:
        markup.add(
            InlineKeyboardButton(
                "📝Список моих локаций, ШАГ 3 🤓", callback_data="training_list_locations"
            )
        )
        return markup

    # Стадия 2 и выше: Удалить локацию
    if training_stage == 4:
        markup.add(InlineKeyboardButton("Мои локации", callback_data="locations"))

    return markup


def add_another_location(user_tg):

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Добавить локацию 📍", callback_data="add_location")
    )

    markup.add(InlineKeyboardButton("Открыть карту 🌍", url=MAP_URL))

    markup.add(InlineKeyboardButton("Главное меню 🏠", callback_data="main_menu"))

    return markup


def admin_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Администратор групп", callback_data="admin_groups"),
    )

    return markup


def location_action_keyboard(location_id: str = None):
    markup = InlineKeyboardMarkup(row_width=1)
    if location_id:
        markup.add(
            InlineKeyboardButton(
                "Удалить локацию", callback_data=f"delete_location_{location_id}"
            )
        )
    else:
        markup.add(
            InlineKeyboardButton("Список моих локаций 📝", callback_data="list_locations"),
            InlineKeyboardButton(
                "Добавить локацию📍", callback_data="add_location"
            ),
            InlineKeyboardButton("Главное меню 🏠", callback_data="main_menu"),
        )
    return markup


def admin_groups_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Список моих групп", callback_data="list_managed_groups"),
        InlineKeyboardButton("Добавить новую группу", callback_data="add_manage_group"),
    )
    return markup


def user_groups_keyboard(group_id: str):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "Выйти из группы",
            callback_data=f"leave_group_{group_id}",
        )
    )
    return markup


def delete_group_button(group_id: str):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Удалить группу", callback_data=f"delete_group_{group_id}")
    )
    return markup
