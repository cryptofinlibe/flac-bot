# FLAC/telegram/telegram_sender.py

import requests
from FLAC.config.telegram_config import TELEGRAM_BOT

def send_telegram_message(message: str, parse_mode: str = "MarkdownV2"):
    token = TELEGRAM_BOT.get("bot_token")
    chat_id = TELEGRAM_BOT.get("bot_id")

    if not token or not chat_id:
        print("Telegram token or bot_id not found.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
    }

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")
