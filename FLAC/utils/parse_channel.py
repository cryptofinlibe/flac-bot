import re
import psycopg2
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.tl.types import Message
from xml.etree import ElementTree as ET

from FLAC.config.db_config import DB_CONFIG
from FLAC.config.telegram_config import TELEGRAM_CLIENT
from FLAC.db.db_writer import insert_sentiment, insert_onchain, insert_smc, update_timestamp, get_last_timestamp

# Client
client = TelegramClient(
    TELEGRAM_CLIENT["session_name"],
    TELEGRAM_CLIENT["api_id"],
    TELEGRAM_CLIENT["api_hash"]
)

# Load keyword from DB
def load_keywords(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT keyword, type, value FROM dictionary WHERE is_active = TRUE")
        rows = cur.fetchall()
        coin_dict = {}
        sentiment_dict = {}
        for kw, t, val in rows:
            if t == "coin":
                coin_dict.setdefault(val.upper(), []).append(kw.lower())
            elif t == "sentiment":
                sentiment_dict.setdefault(val.lower(), []).append(kw.lower())
    return coin_dict, sentiment_dict

# Coin detection
def detect_coin(text, coin_dict):
    text_lower = text.lower()
    for pair, keywords in coin_dict.items():
        if any(kw in text_lower for kw in keywords):
            return pair
    return None

# Sentiment analysis
def detect_sentiment(text, sentiment_dict):
    text_lower = text.lower()
    for sentiment, keywords in sentiment_dict.items():
        if any(kw in text_lower for kw in keywords):
            return sentiment
    return "neutral"

# Main parsing
def parse_and_store(message: Message, tag: str, channel: str, conn, coin_dict, sentiment_dict):
    text = message.message
    if not isinstance(text, str) or not text.strip():
        print(f"⚠️ Skipped non-text or empty message in {channel}")
        return

    raw = text
    timestamp = message.date

    try:
        if tag == "S":
            pair = detect_coin(text, coin_dict)
            if pair:
                sentiment = detect_sentiment(text, sentiment_dict)
                score = {"positive": 1, "neutral": 0, "negative": -1}[sentiment]
                insert_sentiment(conn, pair, timestamp, channel, score, sentiment, raw)
                print(f"⚠️ [Sentiment-Fallback] Inserted {sentiment} for {pair}")
            else:
                print(f"❌ [Sentiment] No coin match: {text[:100]}...")

        elif tag == "O":
            pair = detect_coin(text, coin_dict)
            if pair:
                metric = "others"
                value = 0.0
                insert_onchain(conn, pair, timestamp, metric, value, raw)
                print(f"⚠️ [Onchain-Fallback] Inserted ({metric}) for {pair}")
            else:
                print(f"❌ [Onchain] No coin match: {text[:100]}...")

        elif tag == "T":
            if "<crypto_data>" in text:
                root = ET.fromstring(text)
                for coin in root.findall("coin"):
                    pair = coin.findtext("pair")
                    if not pair:
                        continue
                    insert_smc(
                        conn,
                        pair=pair,
                        date=timestamp.date(),
                        bias=coin.findtext("bias"),
                        structure=coin.findtext("structure"),
                        last_event=coin.findtext("last_event"),
                        position=coin.findtext("position"),
                        supply_zone=coin.findtext("supply_zone"),
                        demand_zone=coin.findtext("demand_zone"),
                        status=coin.findtext("status"),
                        note=coin.findtext("note"),
                        trade_priority=coin.findtext("trade_priority"),
                        mode=coin.findtext("mode"),
                        tag=coin.findtext("tag"),
                        entry_type=coin.find("entry_zone/type").text if coin.find("entry_zone/type") is not None else None,
                        entry_range=coin.find("entry_zone/range").text if coin.find("entry_zone/range") is not None else None,
                        raw=raw
                    )
                    print(f"✅ [SMC-XML] Inserted: {pair}")
            else:
                print(f"❌ [SMC] Invalid XML: {text[:100]}...")

    except Exception as e:
        print(f"❌ Error parsing {tag} message in {channel}: {e}")

# Entry point per channel
def parse_channel_messages(channel_name: str):
    tag = "T" if channel_name == "flac_technical" else ("S" if channel_name == "flac_sentiment" else "O")
    with client:
        with psycopg2.connect(**DB_CONFIG) as conn:
            coin_dict, sentiment_dict = load_keywords(conn)
            last_ts = get_last_timestamp(conn, channel_name)
            msgs = client.iter_messages(channel_name, offset_date=last_ts)

            count = 0
            latest_ts = last_ts

            for msg in msgs:
                msg_time = msg.date.replace(tzinfo=None)
                if last_ts and msg_time <= last_ts.replace(tzinfo=None):
                    break

                parse_and_store(msg, tag, channel_name, conn, coin_dict, sentiment_dict)
                latest_ts = max(latest_ts, msg.date) if latest_ts else msg.date
                count += 1

            if count > 0:
                update_timestamp(conn, channel_name, latest_ts)
                print(f"\n🎯 {count} messages parsed and stored from {channel_name}")
            else:
                print(f"ℹ️ No new messages found in {channel_name}")
