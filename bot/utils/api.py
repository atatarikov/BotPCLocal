# utils/api.py

import requests
import logging
from config import API_URL, TIMEOUT
from telebot import TeleBot
from keyboards.inline import add_comm_main_menu

logger = logging.getLogger(__name__)


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
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"GET {url} — ошибка: {e}")
        return None


def api_post(endpoint: str, payload: dict):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_api_error("POST", url, e)
        return None


def api_delete(endpoint: str, payload: dict = None):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.delete(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_api_error("DELETE", url, e)
        return None


def log_api_error(method: str, url: str, error: Exception) -> None:
    """Логирует детали ошибки API-запроса."""
    error_details = {
        "method": method,
        "url": url,
        "error": str(error),
    }
    logger.error(f"API request failed: {error_details}")
