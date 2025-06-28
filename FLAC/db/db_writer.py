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