# File: FLAC/telegram/telegram_scraper.py

def scrape_channel(channel_username, target_folder):
    from telethon.sync import TelegramClient
    from telethon.tl.types import Message
    import os
    from datetime import datetime

    api_id = 27330139
    api_hash = '7d4b9e2be85113ac678b1ee083bcf9ad'
    client = TelegramClient('flac_session', api_id, api_hash)
    
    folder_path = f"data/raw_telegram/{target_folder}"
    os.makedirs(folder_path, exist_ok=True)

    with client:
        messages = client.iter_messages(channel_username, limit=10)
        for idx, msg in enumerate(messages):
            if msg.text:
                date = datetime.now().strftime('%y%m%d')
                fname = f"{folder_path}/MSG_{date}_{idx}.txt"
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(msg.text.strip())
        print(f"📥 Scrape complete: {channel_username}")
