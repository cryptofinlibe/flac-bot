import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.db.db_reader import get_active_pairs_by_timeframe
from FLAC.utils.detectors import detect_volatility_1h
from FLAC.utils.notifier import send_telegram_message
from FLAC.db.db_writer import insert_volatility_logs

def run_volatility_detector():
    print(f"🚨 Running Volatility Detector (1H) — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    pairs = get_active_pairs_by_timeframe('1h')

    results = []
    for pair in pairs:
        df = smart_fetch(pair, timeframe='1h', default_market='spot', max_limit=50)
        if df is None or df.empty or len(df) < 5:
            print(f"⚠️ No data for {pair}, skipping...")
            continue

        try:
            result = detect_volatility_1h(df, pair)
            if result:
                results.append(result)

                if result['is_spike']:
                    msg = (
                        f"💥 VOLATILITY SPIKE DETECTED\n"
                        f"Pair: {pair}\nTime: {result['time_logged']}\n"
                        f"Price Change: {result['price_change']}%\nNote: {result['notes']}"
                    )
                    send_telegram_message(msg)

        except Exception as e:
            print(f"[ERROR] Detection failed for {pair}: {e}")

    if results:
        insert_volatility_logs(pd.DataFrame(results))
    else:
        print("✅ No results to log.")

if __name__ == '__main__':
    run_volatility_detector()
