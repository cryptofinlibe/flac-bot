import time
from FLAC.utils.parse_channel import parse_channel_messages

def run_ingest():
    print("🚀 Starting Telegram Channel Ingest")

    # Semua channel, tidak pakai tag eksplisit
    channel_list = [
        "flac_sentiment",
        "flac_onchain",
        "flac_technical"
    ]

    for channel in channel_list:
        print(f"📥 Scraping channel: {channel}")
        try:
            parse_channel_messages(channel)
        except Exception as e:
            print(f"❌ Failed to parse {channel}: {e}")
        time.sleep(1)

    print("✅ All channels parsed")

if __name__ == "__main__":
    run_ingest()
