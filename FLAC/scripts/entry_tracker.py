import os
from datetime import datetime
import ccxt
from FLAC.db.db_writer import insert_position, update_position_exit
import psycopg2

# Binance Setup
BINANCE = ccxt.binance({
    'options': {
        'defaultType': 'spot'
    }
})

# Log File
DATA_PATH = "FLAC/data/logs"
ENTRY_LOG = os.path.join(DATA_PATH, "dummy_entry.log")

# DB Config (optional: pindahkan ke config file jika perlu)
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
}

def get_price(pair):
    try:
        ticker = BINANCE.fetch_ticker(pair)  # jangan diubah
        return ticker['last']
    except Exception as e:
        print(f"❌ Failed to get price for {pair}: {e}")
        return None

def get_open_position(pair):
    """
    Get the most recent open position for a given pair
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, entry_price, entry_time FROM positions
            WHERE pair = %s AND status = 'open'
            ORDER BY entry_time DESC LIMIT 1;
        """, (pair,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            return {"id": result[0], "entry_price": result[1], "entry_time": result[2]}
        return None
    except Exception as e:
        print(f"❌ Failed to fetch open position from DB: {e}")
        return None

def open_position(pair, score="N/A", trend="N/A"):
    # Skip if position already open
    if get_open_position(pair):
        print(f"⚠️ {pair} already open — skipping.")
        return False

    price = get_price(pair)
    if price is None:
        print(f"⚠️ {pair} price not available — skipping.")
        return False

    data = {
        "pair": pair,
        "position_type": "long" if trend.lower() == "up" else "short",
        "entry_time": datetime.utcnow(),
        "entry_price": price,
        "stop_loss": None,
        "take_profit": None,
        "notes": f"Score={score}, Trend={trend}"
    }

    try:
        position_id = insert_position(data)
        print(f"✅ Opened position for {pair} at {price} (id: {position_id})")
        return True
    except Exception as e:
        print(f"❌ DB insert failed for {pair}: {e}")
        return False

def close_position(pair, exit_reason="manual"):
    open_pos = get_open_position(pair)
    if not open_pos:
        print(f"⚠️ No open position found for {pair}")
        return False

    exit_price = get_price(pair)
    if exit_price is None:
        print(f"❌ Cannot fetch exit price for {pair}")
        return False

    entry_price = float(open_pos["entry_price"])
    pnl_pct = ((exit_price - entry_price) / entry_price) * 100

    try:
        update_position_exit(
            position_id=open_pos["id"],
            exit_price=exit_price,
            exit_time=datetime.utcnow(),
            pnl=pnl_pct
        )
        print(f"💸 Closed {pair} at {exit_price} | PnL: {pnl_pct:.2f}%")
        return True
    except Exception as e:
        print(f"❌ Failed to update position for {pair}: {e}")
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
                return

            ts, details = parts

            try:
                pair = details.split(" | ")[0].strip()
                score = details.split("score=")[1].split(" ")[0].strip()
                trend = details.split("trend=")[-1].strip()
                print(f"🔍 Parsed entry: pair={pair}, score={score}, trend={trend}")
            except Exception as e:
                print(f"❌ Error parsing line content: {line.strip()} | {e}")
                return
            open_position(pair, score, trend)
        except Exception as e:
            print(f"❌ Failed to process line: {line.strip()} | Error: {e}")

    os.remove(ENTRY_LOG)

if __name__ == "__main__":
    run_entry_tracker()
