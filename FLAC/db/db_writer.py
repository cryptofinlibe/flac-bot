# FLAC/db/db_writer.py
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
# from FLAC.db.db_config import DB_CONFIG
from FLAC.config.db_config import DB_CONFIG

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

