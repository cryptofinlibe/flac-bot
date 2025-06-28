import os
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree
from telethon.sync import TelegramClient
from telethon.tl.types import Message

# Telegram setup
api_id = 27330139  # ← sesuaikan dengan punyamu
api_hash = '7d4b9e2be85113ac678b1ee083bcf9ad'
client = TelegramClient('flac_session', api_id, api_hash)

# Folder tujuan
RAW_DIR = "data/raw_telegram"
SENTIMENT_DIR = "data/sentiment"
ONCHAIN_DIR = "data/onchain"
SNAPSHOT_DIR = "data/snapshots"

# Coin list
COIN_LIST = ["BTC", "ETH", "SOL", "AVAX", "BNB", "PEPE", "DOGE", "TRX", "LINK", "TON", "SUI"]

def detect_token(content):
    content_upper = content.upper()
    for coin in COIN_LIST:
        if coin in content_upper:
            return coin
    return "GLOBAL"

def build_xml(content, tag_type, token):
    root = Element('data')
    SubElement(root, 'type').text = tag_type
    SubElement(root, 'token').text = token
    SubElement(root, 'content').text = content.strip()
    SubElement(root, 'datetime').text = datetime.now().isoformat()
    SubElement(root, 'source').text = 'telegram'
    return ElementTree(root)

def parse_channel_messages(channel_username, tag_type):
    os.makedirs(RAW_DIR, exist_ok=True)
    with client:
        for msg in client.iter_messages(channel_username, limit=20):
            if not msg.text:
                continue

            token = detect_token(msg.text)
            xml_tree = build_xml(msg.text, tag_type, token)
            timestamp_str = datetime.now().strftime('%y%m%d_%H%M%S')
            filename = f"{tag_type}_{token}_{timestamp_str}.xml"

            if tag_type == "S":
                out_path = os.path.join(SENTIMENT_DIR, filename)
            elif tag_type == "O":
                out_path = os.path.join(ONCHAIN_DIR, filename)
            else:
                out_path = os.path.join(SNAPSHOT_DIR, filename)

            xml_tree.write(out_path, encoding="utf-8", xml_declaration=True)
            print(f"✅ Parsed: {out_path}")
