import os
import json
import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.utils.notifier import send_telegram_message
from FLAC.db.db_writer import insert_ohlcv
from FLAC.db.db_reader import get_pairs_by_timeframe
pairs = get_pairs_by_timeframe('daily')


now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
success_count = 0
failed_pairs = []

print(f"📅 Running Daily Pipeline at {now}")
for full_pair in pairs:
    pair = full_pair.replace("/", "")
    print(f"📥 Fetching {full_pair} ...")
    df = smart_fetch(pair, timeframe='1d', default_market='spot')

    if df is not None and not df.empty:
        df["pair"] = full_pair
        df["timeframe"] = "1d"
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        insert_ohlcv(df)
        success_count += 1
    else:
        print(f"❌ Failed to fetch {pair}")
        failed_pairs.append(pair)

# Telegram Notification
if success_count >= 1:
    msg = f"✅ Daily pipeline completed: {success_count}/{len(pairs)} pairs fetched."
    if failed_pairs:
        msg += f"\n❌ Failed: {', '.join(failed_pairs)}"
else:
    msg = "❌ Daily pipeline failed: No data fetched."

send_telegram_message(msg)
