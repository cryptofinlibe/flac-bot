import os
import json
import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.utils.notifier import send_telegram_message
from FLAC.db.db_writer import insert_ohlcv
from FLAC.db.db_reader import get_pairs_by_timeframe

# Optional: Simpan backup lokal ke CSV
SAVE_CSV = False

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
    print(f"✅ Saved snapshot for {pair} → {file_path}")

pairs = get_pairs_by_timeframe('4h')

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
success_count = 0
failed_pairs = []

print(f"🚀 Running 4H Pipeline at {now}")
for full_pair in pairs:
    pair = full_pair.replace("/", "")
    print(f"📥 Fetching {full_pair} ...")
    df = smart_fetch(pair, timeframe='4h', default_market='spot')

    if df is not None and not df.empty:
        # Optional CSV backup
        if SAVE_CSV:
            save_snapshot(df, pair, "4h")

        # Insert into PostgreSQL ohlcv table
        df["pair"] = full_pair
        df["timeframe"] = "4h"
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        insert_ohlcv(df)

        success_count += 1
    else:
        print(f"❌ Failed to fetch {pair}")
        failed_pairs.append(pair)

# Notify
if success_count >= 1:
    msg = f"✅ 4H pipeline completed: {success_count}/{len(pairs)} pairs fetched."
    if failed_pairs:
        msg += f"\n❌ Failed: {', '.join(failed_pairs)}"
else:
    msg = "❌ 4H pipeline failed: No data fetched."

send_telegram_message(msg)
