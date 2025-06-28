import time
from FLAC.utils.parse_channel_to_xml import parse_channel_messages

def run_ingest():
    print("🚀 Starting Telegram Channel Ingest")

    channels = {
        "flac_sentiment": "S",
        "flac_onchain": "O",
        "flac_technical": "T"
    }

    for channel, tag in channels.items():
        print(f"📥 Scraping channel: {channel}")
        try:
            parse_channel_messages(channel, tag)
        except Exception as e:
            print(f"❌ Failed to parse {channel}: {e}")
        time.sleep(1)

    print("✅ All channels parsed")

if __name__ == "__main__":
    run_ingest()
