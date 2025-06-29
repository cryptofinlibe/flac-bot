# FLAC/db/db_writer.py
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from FLAC.config.db_config import DB_CONFIG
from psycopg2.extras import execute_batch

def insert_position(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO positions (pair, position_type, entry_time, entry_price, stop_loss, take_profit, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        data["pair"],
        data["position_type"],
        data["entry_time"],
        data["entry_price"],
        data["stop_loss"],
        data["take_profit"],
        data["notes"]
    ))
    position_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return position_id

def update_position_exit(position_id, exit_price, exit_time, pnl):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        UPDATE positions
        SET exit_price = %s,
            exit_time = %s,
            pnl = %s,
            status = 'closed'
        WHERE id = %s;
    """, (
        exit_price,
        exit_time,
        pnl,
        position_id
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_open_positions():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, pair, entry_price
        FROM positions
        WHERE status = 'open'
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "pair": r[1], "entry_price": r[2]}
        for r in rows
    ]

def get_tp_sl_for_pair(pair):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT rr_ratio FROM watchlist WHERE pair = %s AND enabled = true
    """, (pair,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    # Default R:R 1:2 → SL=1.5%, TP=3.0%
    rr_ratio = float(result[0]) if result else 2.0
    tp_pct = 0.015 * rr_ratio
    sl_pct = 0.015
    return tp_pct, sl_pct

def get_tp_sl_for_pair(pair):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT rr_ratio FROM watchlist
        WHERE pair = %s AND enabled = true
        LIMIT 1
    """, (pair,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    # Default: RR 2.0 → SL 1.5%, TP = SL × RR
    rr = float(result[0]) if result else 2.0
    sl_pct = 0.015
    tp_pct = sl_pct * rr
    return tp_pct, sl_pct

def get_rr_for_pair(pair):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT rr_ratio FROM watchlist
        WHERE pair = %s AND enabled = true
        LIMIT 1
    """, (pair,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return float(result[0]) if result and result[0] else 2.0  # default RR = 2.0

def insert_snapshot_15m(pair, timestamp, entry_signal, rsi, volume, macd, adx):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO snapshot_15m (pair, datetime, entry_signal, rsi, volume, macd, adx)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (pair, timestamp, entry_signal, rsi, volume, macd, adx))
        conn.commit()
    except Exception as e:
        print(f"❌ Failed to insert snapshot_15m for {pair}: {e}")
    finally:
        conn.close()
# FLAC/db/db_writer.py

def insert_snapshot_daily(pair, date, open_, high, low, close, volume):
    query = """
        INSERT INTO snapshot_daily (pair, date, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (pair, date) DO UPDATE
        SET open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume;
    """
    values = (pair, date, open_, high, low, close, volume)

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()
    except Exception as e:
        print(f"❌ Error inserting snapshot for {pair} on {date}: {e}")


def insert_snapshot_4h(pair, datetime, structure=None, signal=None, confidence=None):
    query = """
        INSERT INTO snapshot_4h (pair, datetime, structure, signal, confidence)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (pair, datetime) DO NOTHING;
    """
    values = (pair, datetime, structure, signal, confidence)
    execute_query(query, values)

def log_strategy(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO strategy_log (pair, timeframe, date, signal, source, confidence, extra)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        data['pair'],
        data['timeframe'],
        data['date'],
        data['signal'],
        data.get('source'),
        data.get('confidence'),
        data.get('extra')
    ))

    conn.commit()
    cursor.close()
    conn.close()

def insert_sentiment(conn, pair, timestamp, source, score, summary, raw):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO sentiment_data (pair, timestamp, source, sentiment_score, sentiment_summary, raw_xml)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (pair, timestamp, source, score, summary, raw))

def insert_onchain(conn, pair, timestamp, metric, value, raw):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO onchain_data (pair, timestamp, metric, value, raw_xml)
            VALUES (%s, %s, %s, %s, %s)
        """, (pair, timestamp, metric, value, raw))

def insert_smc(conn, pair, date, bias, structure, last_event, position,
               supply_zone, demand_zone, status, note, trade_priority,
               mode, tag, entry_type, entry_range, raw):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO smc_map (
                pair, date, bias, structure, last_event, position,
                supply_zone, demand_zone, status, note, trade_priority,
                mode, tag, entry_type, entry_range, raw_xml
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            pair, date, bias, structure, last_event, position,
            supply_zone, demand_zone, status, note, trade_priority,
            mode, tag, entry_type, entry_range, raw
        ))

def update_timestamp(conn, channel, last_ts):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO channel_ingest_tracker (channel_name, last_timestamp, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (channel_name) DO UPDATE
            SET last_timestamp = EXCLUDED.last_timestamp, updated_at = NOW()
        """, (channel, last_ts))
        conn.commit()


def get_last_timestamp(conn, channel):
    with conn.cursor() as cur:
        cur.execute("SELECT last_timestamp FROM channel_ingest_tracker WHERE channel_name = %s", (channel,))
        result = cur.fetchone()
        return result[0] if result else None

def insert_ohlcv(data):
    import pandas as pd
    from FLAC.config.db_config import DB_CONFIG
    import psycopg2
    from psycopg2.extras import execute_values

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Jika hanya 1 row (dict atau Series)
    if isinstance(data, dict):
        records = [[
            data["pair"], data["timestamp"], data["timeframe"],
            data["open"], data["high"], data["low"],
            data["close"], data["volume"]
        ]]
    elif isinstance(data, pd.Series):
        records = [[
            data["pair"], data["timestamp"], data["timeframe"],
            data["open"], data["high"], data["low"],
            data["close"], data["volume"]
        ]]
    # Jika DataFrame
    elif isinstance(data, pd.DataFrame):
        required_cols = {"pair", "timestamp", "timeframe", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(data.columns):
            raise ValueError("DataFrame missing required OHLCV columns.")
        records = data[["pair", "timestamp", "timeframe", "open", "high", "low", "close", "volume"]].values.tolist()
    else:
        raise TypeError("Input must be a dict, pandas Series, or DataFrame.")

    query = """
        INSERT INTO ohlcv (pair, timestamp, timeframe, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (pair, timestamp, timeframe) DO NOTHING
    """
    execute_values(cursor, query, records)
    conn.commit()
    cursor.close()
    conn.close()

def insert_trend_log(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trend_logs (pair, timestamp, timeframe, price_change, volume, volume_ma, atr, atr_ma, triggered)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data["pair"],
        data["timestamp"],
        data["timeframe"],
        data["price_change"],
        data["volume"],
        data["volume_ma"],
        data["atr"],
        data["atr_ma"],
        data["triggered"]
    ))
    conn.commit()
    cur.close()
    conn.close()

def insert_volatility_logs(df: pd.DataFrame):
    from FLAC.config.db_config import DB_CONFIG
    import psycopg2
    from psycopg2.extras import execute_batch

    if df.empty:
        print("⚠️ No volatility data to insert.")
        return

    df = df.dropna(subset=['symbol', 'time_logged'])

    insert_query = """
        INSERT INTO volatility_logs 
        (symbol, time_logged, price_change, volume, vol_ma, atr, atr_ma, is_spike, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, time_logged) DO NOTHING
    """

    values = [
        (
            row['symbol'], row['time_logged'], row['price_change'], row['volume'],
            row['vol_ma'], row['atr'], row['atr_ma'], row['is_spike'], row['notes']
        )
        for _, row in df.iterrows()
    ]

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                execute_batch(cur, insert_query, values)
        print(f"✅ Inserted {len(values)} volatility log(s) into database.")
    except Exception as e:
        print(f"❌ Error inserting volatility logs: {e}")


import psycopg2
from FLAC.config.db_config import DB_CONFIG

def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )

def insert_position(data):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO positions (pair, entry_price, direction, status, score, trend)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (
        data["pair"],
        data["entry_price"],
        data.get("direction", "long"),
        data.get("status", "open"),
        data.get("score", None),
        data.get("trend", None)
    ))
    conn.commit()
    cur.close()
    conn.close()

def is_pair_open(pair):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM positions WHERE pair = %s AND status = 'open'", (pair,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def close_position(pair, exit_price):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        UPDATE positions
        SET exit_price = %s, closed_at = NOW(), status = 'closed'
        WHERE pair = %s AND status = 'open'
    """
    cur.execute(query, (exit_price, pair))
    conn.commit()
    cur.close()
    conn.close()

