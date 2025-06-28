import os
import pandas as pd
from datetime import datetime
from FLAC.utils.fetch_ohlcv import fetch_ohlcv

def smart_fetch(pair, timeframe, default_market='spot', max_limit=100):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, f"../data/snapshots/{timeframe}")
    os.makedirs(folder, exist_ok=True)
    
    pair_formatted = pair.replace("USDT", "_USDT")
    file_path = os.path.join(folder, f"{pair_formatted}.csv")
    
    if not os.path.exists(file_path):
        print(f"📦 No existing data for {pair}, fetching full history...")
        return fetch_ohlcv(pair, timeframe, default_market=default_market, limit=max_limit)
    
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except Exception as e:
        print(f"⚠️ Failed to read existing file for {pair}: {e}")
        return fetch_ohlcv(pair, timeframe, default_market=default_market, limit=max_limit)
    
    last_time = df['timestamp'].max()
    now = datetime.utcnow()
    
    # Convert timeframe to hours
    hours_per_bar = {'15m': 0.25, '1h': 1, '4h': 4, '1d': 24}.get(timeframe, 1)
    gap_hours = (now - last_time).total_seconds() / 3600

    if gap_hours > hours_per_bar * 1.5:
        print(f"🧩 Gap detected for {pair}, fetching up to 25 bars...")
        return fetch_ohlcv(pair, timeframe, default_market=default_market, limit=25)
    else:
        print(f"✅ {pair} is up-to-date. Fetching latest bar only.")
        return fetch_ohlcv(pair, timeframe, default_market=default_market, limit=1)
