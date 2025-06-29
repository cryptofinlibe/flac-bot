# FLAC/db/db_reader.py
import psycopg2
from FLAC.config.db_config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_latest_smc_bias(pair):
    query = """
        SELECT bias
        FROM smc_merged
        WHERE pair = %s
        ORDER BY date DESC
        LIMIT 1
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, (pair,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def fetch_last_ingest_timestamp(channel_name):
    query = """
        SELECT last_timestamp
        FROM channel_ingest_tracker
        WHERE channel_name = %s
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, (channel_name,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def fetch_enabled_pairs_by_timeframe(tf):
    query = """
        SELECT pair
        FROM watchlist
        WHERE enabled = true AND mode = %s
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, (tf,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

def is_pair_tracked(pair):
    query = """
        SELECT 1 FROM watchlist WHERE pair = %s AND enabled = true LIMIT 1
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, (pair,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def get_last_snapshot_date(pair):
    query = "SELECT MAX(date) FROM snapshot_daily WHERE pair = %s"
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (pair,))
                result = cur.fetchone()
                return result[0]  # None if no data
    except Exception as e:
        print(f"❌ Failed to fetch last date for {pair}: {e}")
        return None

def get_last_ohlcv_date(pair: str, timeframe: str = "1d"):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(timestamp)
            FROM ohlcv
            WHERE pair = %s AND timeframe = %s
        """, (pair, timeframe))
        result = cur.fetchone()
        conn.close()
        return result[0].date() if result[0] else None
    except Exception as e:
        print(f"❌ Error fetching last ohlcv date: {e}")
        return None

def get_pairs_by_timeframe(tf: str) -> list:
    from FLAC.config.db_config import DB_CONFIG
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT pair FROM pair_config
        WHERE is_active = TRUE
        AND %s = ANY(timeframes)
        AND (type IS NULL OR type NOT IN ('narrative', 'inactive'))
        ORDER BY pair;
    """, (tf,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

def get_active_pairs_by_timeframe(tf: str) -> list:
    from FLAC.config.db_config import DB_CONFIG
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT pair FROM pair_config
        WHERE is_active = TRUE
        AND %s = ANY(timeframes)
        AND (type IS NULL OR type NOT IN ('narrative', 'inactive'))
        ORDER BY pair;
    """, (tf,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

def get_market_type(pair: str) -> str:
    from FLAC.config.db_config import DB_CONFIG
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT market_type FROM pair_config
        WHERE pair = %s
    """, (pair,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 'spot'

def get_open_positions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, pair, entry_price, direction FROM positions WHERE status = 'open'")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "pair": r[1], "entry_price": float(r[2]), "direction": r[3]}
        for r in rows
    ]

def get_latest_snapshot_4h(pair):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT trend FROM trend_state
        WHERE symbol = %s AND timeframe = '4h'
        ORDER BY detected_at DESC
        LIMIT 1
    """, (pair,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None
