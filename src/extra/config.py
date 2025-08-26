import os
from dotenv import load_dotenv

load_dotenv()


def get_bot_token() -> str:
    return os.getenv("BOT_TOKEN")


def get_openrouter_token() -> str:
    return os.getenv("OPENROUTER_TOKEN")
