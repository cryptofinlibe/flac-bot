import os
import json
import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.utils.notifier import send_telegram_message

def save_snapshot(df, pair, timeframe):
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../data/snapshots/{timeframe}")
    os.makedirs(folder, exist_ok=True)
    pair_formatted = pair.replace("USDT", "_USDT")
    file_path = os.path.join(folder, f"{pair_formatted}.csv")

    if os.path.exists(file_path):
        existing = pd.read_csv(file_path)
        latest_time = df['timestamp'].iloc[-1]
        if latest_time in existing['timestamp'].values:
            print(f"ℹ️ {pair} bar already exists. Skipping save.")
            return
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(file_path, index=False)
    print(f"✅ Saved 4H snapshot for {pair} → {file_path}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../config/active_pairs.json"))

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
pairs = config.get("4h", [])

today = datetime.utcnow().strftime("%Y-%m-%d")
success_count = 0
failed_pairs = []

print(f"⏳ Running 4H Pipeline for {today}")
for full_pair in pairs:
    pair = full_pair.replace("/", "")
    print(f"📥 Fetching {full_pair} ...")
    df = smart_fetch(pair, timeframe='4h', default_market='spot')
    if df is not None and not df.empty:
        save_snapshot(df, pair, "4h")
        success_count += 1
    else:
        print(f"❌ Failed to fetch {pair}")
        failed_pairs.append(pair)

# Telegram Notification
if success_count >= 1:
    msg = f"⚠️ 4H pipeline partial: {success_count}/{len(pairs)} fetched."
    if failed_pairs:
        msg += f"\n❌ Failed: {', '.join(failed_pairs)}"
    send_telegram_message(msg)
else:
    send_telegram_message("❌ 4H pipeline failed: No data fetched.")
