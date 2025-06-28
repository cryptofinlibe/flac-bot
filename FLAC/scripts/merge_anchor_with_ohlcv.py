import os
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
}

ANCHOR_PATH = "FLAC/data/anchors/daily_smc.xml"
SNAPSHOT_PATH = "FLAC/data/snapshots/1d"


def parse_smc_anchor(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    rows = []
    for coin_elem in root.findall("coin"):
        pair = coin_elem.get("symbol")
        bias = coin_elem.findtext("bias")
        note = coin_elem.findtext("note")
        trend = coin_elem.findtext("trend")
        zone_description = coin_elem.findtext("zone_description")
        rows.append({
            "pair": pair,
            "bias": bias,
            "note": note,
            "trend": trend,
            "zone_description": zone_description
        })
    return pd.DataFrame(rows)


def merge_anchor_with_ohlcv():
    smc_df = parse_smc_anchor(ANCHOR_PATH)
    merged_rows = []

    for _, row in smc_df.iterrows():
        pair = row["pair"].replace("/", "")
        ohlcv_path = os.path.join(SNAPSHOT_PATH, f"{pair}.csv")
        if not os.path.exists(ohlcv_path):
            print(f"⚠️ OHLCV not found for {pair}, skipping.")
            continue

        ohlcv_df = pd.read_csv(ohlcv_path)
        last_bar = ohlcv_df.iloc[-1]
        merged_rows.append({
            "pair": pair,
            "date": datetime.utcfromtimestamp(last_bar["timestamp"] / 1000).date(),
            "timeframe": "1d",
            "bias": row["bias"],
            "zone_description": row["zone_description"],
            "close": last_bar["close"],
            "high": last_bar["high"],
            "low": last_bar["low"],
            "volume": last_bar["volume"],
            "trend": row["trend"]
        })

    merged_df = pd.DataFrame(merged_rows)
    save_to_db(merged_df)


def save_to_db(df):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO smc_merged (
                    pair, date, timeframe, bias, zone_description, close,
                    high, low, volume, trend
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pair, date, timeframe) DO UPDATE SET
                    bias = EXCLUDED.bias,
                    zone_description = EXCLUDED.zone_description,
                    close = EXCLUDED.close,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    volume = EXCLUDED.volume,
                    trend = EXCLUDED.trend;
            """, (
                row["pair"], row["date"], row["timeframe"], row["bias"],
                row["zone_description"], row["close"], row["high"],
                row["low"], row["volume"], row["trend"]
            ))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Merged data saved to smc_merged table.")
    except Exception as e:
        print(f"❌ DB insert error: {e}")


if __name__ == "__main__":
    merge_anchor_with_ohlcv()
