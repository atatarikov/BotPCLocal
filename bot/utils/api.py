# utils/api.py

import requests
import logging
from config import API_URL

logger = logging.getLogger(__name__)


def api_get(endpoint: str):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"GET {url} — ошибка: {e}")
        return None


def api_post(endpoint: str, payload: dict):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"POST {url} — ошибка: {e}")
        return None


def api_delete(endpoint: str, payload: dict = None):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.delete(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"DELETE {url} — ошибка: {e}")
        return None
