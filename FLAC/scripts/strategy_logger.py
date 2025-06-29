import os
import json
from datetime import datetime
from FLAC.db.db_writer import log_strategy

LOG_FILE = "FLAC/data/logs/dummy_strategy.log"

def parse_line(line):
    try:
        parts = line.strip().split(" - SIGNAL ")
        if len(parts) != 2:
            return None

        ts_raw, content = parts
        ts = datetime.fromisoformat(ts_raw.replace("Z", ""))

        segments = content.split(" | ")
        pair = segments[0].strip()
        tf = content.split("tf=")[1].split(" ")[0].strip()
        signal = content.split("signal=")[1].split(" ")[0].strip()
        confidence = float(content.split("confidence=")[1].split(" ")[0])
        source = content.split("source=")[-1].strip()

        return {
            "pair": pair,
            "timeframe": tf,
            "date": ts,
            "signal": signal,
            "source": source,
            "confidence": confidence,
            "extra": json.dumps({})
        }

    except Exception as e:
        print(f"❌ Failed to parse line: {line.strip()} | {e}")
        return None

def run_strategy_logger():
    if not os.path.exists(LOG_FILE):
        print("📭 No strategy log file found.")
        return

    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()

    for line in lines:
        data = parse_line(line)
        if not data:
            continue
        try:
            log_strategy(data)
            print(f"✅ Logged: {data['pair']} | {data['timeframe']} | {data['signal']} ({data['confidence']})")
        except Exception as e:
            print(f"❌ DB log failed: {e}")

    os.remove(LOG_FILE)
    print("🧹 Cleaned up dummy_strategy.log")

if __name__ == "__main__":
    run_strategy_logger()
