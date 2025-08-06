# utils/api.py

import requests
import logging
from config import API_URL, TIMEOUT
from telebot import TeleBot
from telebot.types import User
from keyboards.inline import add_comm_main_menu
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Базовый класс для ошибок API"""

    def __init__(self, message: str, status_code: int = None, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def _process_response(
    response: requests.Response,
) -> Tuple[Optional[Dict], Optional[APIError]]:
    """Обрабатывает ответ API в стандартном формате"""
    try:
        data = response.json()
    except ValueError:
        return None, APIError("Invalid JSON response", response.status_code)

    if response.status_code >= 400:
        # Обрабатываем error response
        error_msg = data.get("message", "Unknown error")
        details = data.get("details")
        return None, APIError(error_msg, response.status_code, details)

    # Обрабатываем success response
    return data, None


def handle_api_error(
    bot: TeleBot, chat_id: int, message_id: int = None, text: str = None
) -> None:
    """
    Универсальная обработка ошибок API.

    Args:
        bot: Экземпляр TeleBot
        chat_id: ID чата для отправки сообщения
        message_id: ID сообщения для редактирования (если есть)
        text: Дополнительный текст перед сообщением об ошибке
    """
    error_msg = "⚠️ Ошибка соединения с сервером. Попробуйте позже."
    full_msg = f"{text}\n{error_msg}" if text else error_msg
    full_msg = add_comm_main_menu(full_msg)
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=full_msg)
        except Exception as e:
            logger.error(f"Не удалось исправить собщение: {e}")
            bot.send_message(chat_id, full_msg)
    else:
        bot.send_message(chat_id, full_msg)


def api_get(endpoint: str):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        return _process_response(response)
    except Exception as e:
        log_data = {"method": "GET", "url": url, "error": str(e)}
        logger.error(f"API request failed: {log_data}")
        return None, APIError(f"Connection error: {str(e)}")


def api_post(endpoint: str, payload: dict):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        return _process_response(response)
    except Exception as e:
        log_data = {
            "method": "POST",
            "url": url,
            "error": str(e),
            "payload": payload if payload else None,
        }
        logger.error(f"API request failed: {log_data}")
        return None, APIError(f"Connection error: {str(e)}")


def api_delete(endpoint: str, payload: dict = None):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.delete(url, json=payload, timeout=TIMEOUT)
        return _process_response(response)
    except Exception as e:
        log_data = {
            "method": "DELETE",
            "url": url,
            "error": str(e),
            "payload": payload if payload else None,
        }
        logger.error(f"API request failed: {log_data}")
        return None, APIError(f"Connection error: {str(e)}")


def update_training_stage(bot, telegram_id, new_training_stage, chat_id):
    api_response_user, error = api_post(
        "user/update_training_stage",
        {"telegram_id": telegram_id, "new_training_stage": new_training_stage},
    )
    if error:
        handle_api_error(
            bot,
            chat_id,
            None,
            "Не удалось обновить этап обучения",
        )
        return

    return new_training_stage, None


def get_training_stage(bot: TeleBot, user_tg: User, chat_id):
    # with bot.retrieve_data(user_tg.id, chat_id) as data:
    #     training_stage = data.get("training_stage")

    # if training_stage is None:
    user_data, error = get_or_create_user(user_tg)
    if error:
        handle_api_error(
            bot,
            chat_id,
            None,
            "Не удалось зарегистрировать пользователя",
        )
        return
    training_stage = user_data.training_stage
    # storage.set_data("training_stage", training_stage)
    # with bot.retrieve_data(user_tg.id, chat_id) as data:
    #     data["training_stage"] = training_stage

    return training_stage


class UserData:
    """Класс для хранения данных пользователя и этапа обучения"""

    def __init__(self, tg_user: User, training_stage: int):
        self.user = tg_user  # Объект пользователя из telebot
        self.training_stage = training_stage  # Текущий этап обучения


def get_or_create_user(tg_user: User) -> Tuple[Optional[int], Optional[str]]:
    """
    Получает или создает пользователя через API

    Возвращает:
        tuple: (UserData, None) при успехе или (None, error) при ошибке
    """
    # 1. Запрашиваем данные через API
    api_response, error = api_post(
        "user/add",
        {
            "telegram_id": tg_user.id,
            "username": tg_user.username,
            "first_name": tg_user.first_name,
        },
    )

    # 2. Если ошибка - возвращаем (None, error)
    if api_response is None:
        return None, error

    # 3. Извлекаем этап обучения (по умолчанию 0)
    training_stage = api_response['data']['training_stage']

    # 4. Создаем и возвращаем объект UserData
    return UserData(tg_user=tg_user, training_stage=training_stage), None


# TODO
# Всегда проверяйте, что username не None (многие пользователи скрывают его)
# Лучше использовать telegram_id для важных операций - он всегда уникален и доступен
# Для ответа используйте call.message.chat.id, чтобы ответить в тот же ча
# Пример с обработкой отсутствующего username:

# python
# @bot.callback_query_handler(func=lambda call: True)
# def handle_callback(call):
#     user = call.from_user
#     username = user.username or f"id{user.id}"
#     name = user.first_name or "Аноним"

#     bot.answer_callback_query(call.id, f"Привет, {name} (@{username})!")
