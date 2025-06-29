# FLAC/utils/notifier.py

import requests
from FLAC.config.telegram_config import TELEGRAM_BOT

def send_telegram_message(message: str, parse_mode: str = None):
    """
    Kirim pesan ke Telegram menggunakan bot.
    - message: string pesan.
    - parse_mode: opsional, bisa 'Markdown', 'MarkdownV2', atau None.
    """
    token = TELEGRAM_BOT.get("bot_token")
    chat_id = TELEGRAM_BOT.get("bot_id")

    if not token or not chat_id:
        print("Telegram token or bot_id not found.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"[Telegram Error] {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")
