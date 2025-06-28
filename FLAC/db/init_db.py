import psycopg2

# Konfigurasi koneksi (bisa pindah ke .env atau config JSON nanti)
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
}

TABLE_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS positions (
        id SERIAL PRIMARY KEY,
        pair TEXT NOT NULL,
        position_type TEXT CHECK (position_type IN ('long', 'short')) NOT NULL,
        status TEXT CHECK (status IN ('open', 'closed')) NOT NULL,
        entry_time TIMESTAMP NOT NULL,
        exit_time TIMESTAMP,
        entry_price NUMERIC,
        exit_price NUMERIC,
        stop_loss NUMERIC,
        take_profit NUMERIC,
        pnl NUMERIC,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS strategy_log (
        id SERIAL PRIMARY KEY,
        pair TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        date TIMESTAMP NOT NULL,
        signal TEXT CHECK (signal IN ('long', 'short', 'wait')) NOT NULL,
        source TEXT,
        confidence NUMERIC,
        extra JSONB
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS watchlist (
        id SERIAL PRIMARY KEY,
        pair TEXT UNIQUE NOT NULL,
        enabled BOOLEAN DEFAULT TRUE,
        mode TEXT CHECK (mode IN ('spot', 'futures')) DEFAULT 'futures',
        default_qty NUMERIC,
        max_loss_per_trade NUMERIC,
        rr_ratio NUMERIC,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sentiment_data (
        id SERIAL PRIMARY KEY,
        pair TEXT,
        timestamp TIMESTAMP NOT NULL,
        source TEXT,
        sentiment_score NUMERIC,
        sentiment_summary TEXT,
        raw_xml TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS onchain_data (
        id SERIAL PRIMARY KEY,
        pair TEXT,
        timestamp TIMESTAMP NOT NULL,
        metric TEXT,
        value NUMERIC,
        extra JSONB,
        raw_xml TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS smc_map (
        id SERIAL PRIMARY KEY,
        pair TEXT NOT NULL,
        date DATE NOT NULL,
        bias TEXT CHECK (bias IN ('long', 'short', 'wait')),
        zone_description TEXT,
        raw_xml TEXT
    );
    """
]

def create_tables():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for query in TABLE_QUERIES:
            cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ All tables created successfully.")
    except Exception as e:
        print("❌ Error creating tables:", e)

if __name__ == "__main__":
    create_tables()
