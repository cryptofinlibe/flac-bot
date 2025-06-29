from FLAC.utils.price_utils import get_price
from FLAC.db.db_reader import get_open_positions
from FLAC.db.db_writer import close_position
from FLAC.utils.notifier import send_telegram_message

TP_THRESHOLD = 0.03  # +3%
SL_THRESHOLD = -0.02  # -2%

def run_exit_tracker():
    positions = get_open_positions()
    closed = []

    for pos in positions:
        pair = pos["pair"]
        entry_price = pos["entry_price"]
        direction = pos["direction"]
        current_price = get_price(pair)

        if current_price is None:
            continue

        if direction == "long":
            gain_pct = (current_price - entry_price) / entry_price
        else:  # short
            gain_pct = (entry_price - current_price) / entry_price

        if gain_pct >= TP_THRESHOLD:
            close_position(pair, current_price)
            closed.append(f"🎯 TP Hit: {pair} {direction.upper()} +{gain_pct*100:.2f}%")
        elif gain_pct <= SL_THRESHOLD:
            close_position(pair, current_price)
            closed.append(f"⚠️ SL Hit: {pair} {direction.upper()} {gain_pct*100:.2f}%")

    if closed:
        send_telegram_message("🔒 Exit Tracker Update:\n" + "\n".join(closed))
