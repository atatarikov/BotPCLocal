# config.py
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
MAP_URL = os.getenv("MAP_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
HELP_USERNAMES = os.getenv("HELP_USERNAMES")
