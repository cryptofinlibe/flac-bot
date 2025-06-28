import requests
import os

def get_token_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir, "..", "telegram", "token.txt"))

def load_token_chat():
    token_path = get_token_path()
    if not os.path.exists(token_path):
        return None, None
    with open(token_path, "r") as f:
        lines = f.read().splitlines()
    if len(lines) >= 2:
        return lines[0], lines[1]  # token, chat_id
    return None, None

def send_telegram_message(message: str):
    token, chat_id = load_token_chat()
    if not token or not chat_id:
        print("Telegram token or chat_id not found.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")
