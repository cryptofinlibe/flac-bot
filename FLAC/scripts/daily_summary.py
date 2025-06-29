from datetime import datetime
import pandas as pd
import psycopg2
from FLAC.config.db_config import DB_CONFIG
from FLAC.utils.notifier import send_telegram_message

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_table(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def summarize_smc():
    query = """
        SELECT pair, bias, zone_description, trend
        FROM smc_merged
        WHERE date = (SELECT MAX(date) FROM smc_merged)
        ORDER BY pair;
    """
    df = fetch_table(query)
    lines = ["📊 *SMC Bias Summary:*"]
    for _, row in df.iterrows():
        lines.append(f"- {row['pair']}: {row['bias']} | {row['zone_description']} | {row['trend']}")
    return "\n".join(lines)

def summarize_signals():
    today = datetime.utcnow().date()
    query = f"""
        SELECT strategy, symbol, signal_type, signal_time
        FROM signals
        WHERE signal_time::date = '{today}'
        ORDER BY signal_time DESC;
    """
    df = fetch_table(query)
    if df.empty:
        return "📡 *Signals Today:*\nNo signals triggered today."
    lines = ["📡 *Signals Today:*"]
    for _, row in df.iterrows():
        lines.append(f"- {row['symbol']} {row['signal_type']} [{row['strategy']}] @ {row['signal_time'].strftime('%H:%M UTC')}")
    return "\n".join(lines)

def summarize_positions():
    query = """
        SELECT pair, entry_price, direction, opened_at
        FROM positions
        WHERE status = 'open'
        ORDER BY opened_at DESC;
    """
    df = fetch_table(query)
    if df.empty:
        return "📈 *Open Positions:*\nNo active positions."
    lines = ["📈 *Open Positions:*"]
    for _, row in df.iterrows():
        lines.append(f"- {row['pair']} {row['direction']} @ {row['entry_price']} (Since {row['opened_at'].strftime('%H:%M')})")
    return "\n".join(lines)

def summarize_volatility():
    today = datetime.utcnow().date()
    query = f"""
        SELECT symbol, time_logged, price_change, volume, is_spike
        FROM volatility_logs
        WHERE time_logged::date = '{today}' AND is_spike = true
        ORDER BY time_logged DESC;
    """
    df = fetch_table(query)
    if df.empty:
        return "🌪️ *1H Volatility Spikes:*\nNone detected today."
    lines = ["🌪️ *1H Volatility Spikes:*"]
    for _, row in df.iterrows():
        lines.append(f"- {row['symbol']} spike at {row['time_logged'].strftime('%H:%M')} | ΔPrice: {row['price_change']}%")
    return "\n".join(lines)

def send_summary():
    parts = [
        summarize_smc(),
        summarize_signals(),
        summarize_positions(),
        summarize_volatility()
    ]

    full_text = "\n\n".join(parts)
    messages = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
    for msg in messages:
        send_telegram_message(msg, parse_mode="Markdown")

if __name__ == "__main__":
    send_summary()
