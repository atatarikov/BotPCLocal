# keyboards/inline.py

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import MAP_URL

MAIN_MENU = "/main - Главное меню"


def add_comm_main_menu(txt: str):
    return txt + "\n" + MAIN_MENU


def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        # InlineKeyboardButton("О боте", callback_data="about"),
        InlineKeyboardButton("Мои группы", callback_data="my_groups"),
        InlineKeyboardButton("Мои локации", callback_data="locations"),
        InlineKeyboardButton("Открыть карту 🌍", url=MAP_URL),
    )
    return markup


def admin_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Администратор групп", callback_data="admin_groups"),
    )

    return markup


def location_action_keyboard(location_id: str = None):
    markup = InlineKeyboardMarkup()
    if location_id:
        markup.add(
            InlineKeyboardButton(
                "Удалить локацию", callback_data=f"delete_location_{location_id}"
            )
        )
    else:
        markup.add(
            InlineKeyboardButton("Список моих локаций", callback_data="list_locations"),
            InlineKeyboardButton(
                "Добавить новую локацию", callback_data="add_location"
            ),
        )
    return markup


# keyboards/inline.py (добавь в конец)


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
            "Выйти из группы и удалить все метки",
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
