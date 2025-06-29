import psycopg2
import pandas as pd
from FLAC.config.db_config import DB_CONFIG

def merge_anchor_with_ohlcv():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Ambil latest SMC per pair
        cur.execute("""
            SELECT DISTINCT ON (pair)
                pair, date, bias, structure AS trend, note, zone_description
            FROM smc_map
            WHERE date IS NOT NULL
            ORDER BY pair, date DESC
        """)
        smc_rows = cur.fetchall()

        # Ambil OHLCV timeframe 1d terbaru per pair
        cur.execute("""
            SELECT DISTINCT ON (pair)
                pair, timestamp, close, high, low, volume
            FROM ohlcv
            WHERE timeframe = '1d'
            ORDER BY pair, timestamp DESC
        """)
        ohlcv_rows = cur.fetchall()

        # Buat dataframe
        smc_df = pd.DataFrame(smc_rows, columns=["pair", "date", "bias", "trend", "note", "zone_description"])
        ohlcv_df = pd.DataFrame(ohlcv_rows, columns=["pair", "timestamp", "close", "high", "low", "volume"])

        # Gabungkan
        merged_df = pd.merge(smc_df, ohlcv_df, on="pair", how="inner")

        for _, row in merged_df.iterrows():
            cur.execute("""
                INSERT INTO smc_merged (
                    pair, date, timeframe, bias, zone_description,
                    close, high, low, volume, trend
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pair, date, timeframe) DO UPDATE SET
                    bias = EXCLUDED.bias,
                    zone_description = EXCLUDED.zone_description,
                    close = EXCLUDED.close,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    volume = EXCLUDED.volume,
                    trend = EXCLUDED.trend
            """, (
                row["pair"],
                row["date"],
                "1d",
                row["bias"],
                row["zone_description"],
                row["close"],
                row["high"],
                row["low"],
                row["volume"],
                row["trend"]
            ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ {len(merged_df)} rows merged into `smc_merged`.")

    except Exception as e:
        print(f"❌ Merge error: {e}")

if __name__ == "__main__":
    merge_anchor_with_ohlcv()
