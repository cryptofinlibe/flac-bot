import ccxt
from datetime import datetime
from FLAC.db.db_writer import get_open_positions, update_position_exit, get_tp_sl_for_pair
from FLAC.utils.notifier import send_telegram_message

BINANCE = ccxt.binance({
    'options': {'defaultType': 'spot'}
})

def get_price(pair):
    try:
        return BINANCE.fetch_ticker(pair)['last']
    except Exception as e:
        print(f"❌ Error fetching price for {pair}: {e}")
        return None

def run_exit_tracker():
    print(f"🕐 Exit tracker running at {datetime.utcnow()}")
    open_positions = get_open_positions()
    if not open_positions:
        print("📟 No open positions in DB.")
        return

    messages = []

    for pos in open_positions:
        pair = pos['pair']
        entry_price = float(pos['entry_price'])
        position_id = pos['id']

        tp_pct, sl_pct = get_tp_sl_for_pair(pair)

        now_price = get_price(pair)
        if now_price is None:
            continue

        change_pct = (now_price - entry_price) / entry_price
        status = None

        if change_pct >= tp_pct:
            status = "TP"
        elif change_pct <= -sl_pct:
            status = "SL"

        if status:
            pnl_pct = round(change_pct * 100, 2)
            try:
                update_position_exit(
                    position_id=position_id,
                    exit_price=now_price,
                    exit_time=datetime.utcnow(),
                    pnl=pnl_pct
                )
                messages.append(f"💸 {pair} hit {status} | PnL: {pnl_pct:.2f}%")
            except Exception as e:
                print(f"❌ Failed to close {pair}: {e}")

    if messages:
        print("✅ Updated positions:")
        for m in messages:
            print(m)
        send_telegram_message("💼 Exit Tracker:\n" + "\n".join(messages))
    else:
        print("📈 No TP/SL triggered.")

if __name__ == "__main__":
    run_exit_tracker()
