import os
import logging
from telegram.ext import Updater, MessageHandler, Filters
from telegram import Bot
from FLAC.scripts.parse_smc_xml import parse_smc_xml
from FLAC.utils.notifier import notify

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load token and chat_id from file
def load_token_chat_id():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_file = os.path.join(base_dir, "..", "telegram", "token.txt")
    if not os.path.exists(token_file):
        raise FileNotFoundError("Token file not found.")
    with open(token_file, 'r') as f:
        lines = f.read().strip().split(',')
        if len(lines) != 2:
            raise ValueError("Token file must contain TOKEN,CHAT_ID format.")
        return lines[0], lines[1]

TOKEN, CHAT_ID = load_token_chat_id()
bot = Bot(token=TOKEN)

# Handler function
def handle_file(update, context):
    file = update.message.document or update.message.photo[-1]
    file_name = file.file_name if hasattr(file, 'file_name') else "unknown_file"
    file_path = os.path.join("FLAC/data/uploads", file_name)

    logging.info(f"[RECEIVED] File: {file_name}")
    new_file = context.bot.get_file(file.file_id)
    new_file.download(file_path)
    logging.info(f"[SAVED] {file_path}")

    try:
        if file_name.startswith("T_") and file_name.endswith(".xml"):
            logging.info("🧠 Parsing SMC XML...")
            parse_smc_xml(file_path)
            notify("✅ Struktur SMC berhasil diproses.")
        elif file_name.startswith("S_") and file_name.endswith(".xml"):
            from FLAC.scripts.parse_sentiment_xml import parse_sentiment_xml
            logging.info("📊 Parsing Sentiment XML...")
            parse_sentiment_xml(file_path)
            notify("✅ Sentiment data berhasil diproses.")
        elif file_name.startswith("O_") and file_name.endswith(".xml"):
            from FLAC.scripts.parse_onchain_xml import parse_onchain_xml
            logging.info("🔗 Parsing Onchain XML...")
            parse_onchain_xml(file_path)
            notify("✅ Onchain data berhasil diproses.")
        else:
            logging.info("⚠️ Format file tidak dikenali.")
            notify("⚠️ File diterima tapi format tidak dikenali.")
    except Exception as e:
        logging.error(f"❌ Error processing {file_name}: {e}")
        notify(f"❌ Gagal parsing file: {file_name}\n{e}")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document | Filters.photo, handle_file))
    updater.start_polling()
    logging.info("[BOT] Listening for incoming files...")
    updater.idle()

if __name__ == "__main__":
    main()
