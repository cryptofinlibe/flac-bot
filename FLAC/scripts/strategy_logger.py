import os
from datetime import datetime
from FLAC.db.db_writer import log_strategy

DATA_PATH = "FLAC/data/logs"
STRATEGY_LOG_FILE = os.path.join(DATA_PATH, "dummy_strategy.log")

def run_strategy_logger():
    if not os.path.exists(STRATEGY_LOG_FILE):
        print("📭 No strategy signal log found.")
        return

    with open(STRATEGY_LOG_FILE, 'r') as f:
        lines = f.readlines()

    for line in lines:
        try:
            parts = line.strip().split(" - SIGNAL ")
            if len(parts) != 2:
                print(f"❌ Invalid format: {line.strip()}")
                continue

            ts, detail = parts
            pair = detail.split(" | ")[0].strip()
            tf = detail.split("tf=")[1].split(" ")[0].strip()
            signal = detail.split("signal=")[1].split(" ")[0].strip()
            confidence = float(detail.split("confidence=")[1].split(" ")[0])
            source = detail.split("source=")[-1].strip()

            log_strategy({
                "pair": pair,
                "timeframe": tf,
                "date": datetime.fromisoformat(ts.replace("Z", "")),
                "signal": signal,
                "source": source,
                "confidence": confidence,
                "extra": {}
            })

            print(f"✅ Logged signal: {pair} | {tf} | {signal} ({confidence})")

        except Exception as e:
            print(f"❌ Error processing line: {line.strip()} | {e}")

    os.remove(STRATEGY_LOG_FILE)

if __name__ == "__main__":
    run_strategy_logger()
