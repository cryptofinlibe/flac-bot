import os
from datetime import datetime
import ccxt
from FLAC.db.db_writer import insert_position, get_open_position, get_rr_for_pair
from FLAC.config.db_config import DB_CONFIG

BINANCE = ccxt.binance({
    'options': {
        'defaultType': 'spot'
    }
})

ENTRY_LOG = "FLAC/data/logs/dummy_entry.log"

def get_price(pair):
    try:
        ticker = BINANCE.fetch_ticker(pair)
        return ticker['last']
    except Exception as e:
        print(f"❌ Failed to get price for {pair}: {e}")
        return None

def open_position(pair, score="N/A", trend="N/A"):
    if get_open_position(pair):
        print(f"⚠️ {pair} already open — skipping.")
        return False

    price = get_price(pair)
    if price is None:
        print(f"⚠️ {pair} price not available — skipping.")
        return False

    rr_ratio = get_rr_for_pair(pair)  # from watchlist or default = 2.0
    sl_pct = 0.015
    tp_pct = sl_pct * rr_ratio

    if trend.lower() == "up":
        sl = price * (1 - sl_pct)
        tp = price * (1 + tp_pct)
    else:
        sl = price * (1 + sl_pct)
        tp = price * (1 - tp_pct)

    data = {
        "pair": pair,
        "position_type": "long" if trend.lower() == "up" else "short",
        "entry_time": datetime.utcnow(),
        "entry_price": price,
        "stop_loss": round(sl, 4),
        "take_profit": round(tp, 4),
        "rr_ratio": rr_ratio,
        "notes": f"Score={score}, Trend={trend}"
    }

    try:
        position_id = insert_position(data)
        print(f"✅ Opened position for {pair} at {price} (id: {position_id})")
        return True
    except Exception as e:
        print(f"❌ DB insert failed for {pair}: {e}")
        return False

def run_entry_tracker():
    if not os.path.exists(ENTRY_LOG):
        return

    with open(ENTRY_LOG, 'r') as f:
        lines = f.readlines()

    for line in lines:
        try:
            parts = line.strip().split(" - ENTRY ")
            if len(parts) != 2:
                print(f"❌ Unexpected log format: {line.strip()}")
                continue

            ts, details = parts
            pair = details.split(" | ")[0].strip()
            score = details.split("score=")[1].split(" ")[0].strip()
            trend = details.split("trend=")[-1].strip()
            print(f"🔍 Parsed entry: pair={pair}, score={score}, trend={trend}")
            open_position(pair, score, trend)
        except Exception as e:
            print(f"❌ Failed to process line: {line.strip()} | Error: {e}")

    os.remove(ENTRY_LOG)

if __name__ == "__main__":
    run_entry_tracker()
