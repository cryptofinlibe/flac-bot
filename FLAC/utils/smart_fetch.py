import pandas as pd
from datetime import datetime, time
from FLAC.utils.fetch_ohlcv import fetch_ohlcv
from FLAC.db.db_reader import get_last_ohlcv_date, get_market_type

def smart_fetch(pair, timeframe='1d', default_market=None, max_limit=100):
    try:
        # 1. Tentukan market_type dari DB kalau tidak diberikan
        market = default_market or get_market_type(pair)

        # 2. Ambil last_timestamp dari DB
        last_timestamp = get_last_ohlcv_date(pair, timeframe=timeframe)
        now = datetime.utcnow()

        if last_timestamp is None:
            print(f"📦 No existing DB data for {pair}, fetching full history...")
            return fetch_ohlcv(pair, timeframe, default_market=market, limit=max_limit)

        # 3. Normalisasi timestamp
        last_dt = last_timestamp if isinstance(last_timestamp, datetime) else datetime.combine(last_timestamp, time.min)

        # 4. Hitung jarak data terakhir
        hours_per_bar = {'15m': 0.25, '1h': 1, '4h': 4, '1d': 24}.get(timeframe, 1)
        gap_hours = (now - last_dt).total_seconds() / 3600

        if gap_hours > hours_per_bar * 1.5:
            print(f"🧩 Gap detected for {pair}, fetching up to 25 bars...")
            return fetch_ohlcv(pair, timeframe, default_market=market, limit=25)
        else:
            print(f"✅ {pair} is up-to-date. Fetching latest bar only.")
            return fetch_ohlcv(pair, timeframe, default_market=market, limit=1)

    except Exception as e:
        print(f"❌ Error in smart_fetch for {pair}: {e}")
        return None
