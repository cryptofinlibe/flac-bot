from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env")
load_dotenv(dotenv_path=env_path)

TELEGRAM_BOT = {
    "bot_id": int(os.getenv("TG_BOT_ID")),
    "bot_token": os.getenv("TG_BOT_TOKEN"),
}

TELEGRAM_CLIENT = {
    "api_id": int(os.getenv("TG_API_ID")),
    "api_hash": os.getenv("TG_API_HASH"),
    "session_name": os.getenv("TG_SESSION_NAME"),
}
