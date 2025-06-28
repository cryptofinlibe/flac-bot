import os
import json
import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.utils.notifier import send_telegram_message
from FLAC.scripts.merge_anchor_with_ohlcv import merge_anchor_with_ohlcv as run_merge


def save_snapshot(df, pair, timeframe):
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../data/snapshots/{timeframe}")
    os.makedirs(folder, exist_ok=True)
    pair_formatted = pair.replace("/", "_")
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


# Load config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../config/active_pairs.json"))

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
pairs = config.get("daily", [])

today = datetime.utcnow().strftime("%Y-%m-%d")
success_count = 0
failed_pairs = []

print(f"\U0001F680 Running Daily Pipeline for {today}")
for full_pair in pairs:
    print(f"\U0001F4E5 Fetching {full_pair} ...")
    df = smart_fetch(full_pair.replace("/", ""), timeframe='1d', default_market='spot')
    if df is not None and not df.empty:
        save_snapshot(df, full_pair, "1d")
        success_count += 1
    else:
        print(f"❌ Failed to fetch {full_pair}")
        failed_pairs.append(full_pair)

# Notify & Merge
if success_count >= 1:
    msg = f"⚠️ Daily pipeline partial: {success_count}/{len(pairs)} fetched."
    if failed_pairs:
        msg += f"\n❌ Failed: {', '.join(failed_pairs)}"
    msg += f"\n\U0001F680 Merging SMC + OHLCV..."
    send_telegram_message(msg)

    run_merge(timeframe="1d")
    send_telegram_message("✅ Merge complete. `smc_merged.csv` updated.")
else:
    send_telegram_message("❌ Daily pipeline failed: No data fetched. Merge skipped.")
