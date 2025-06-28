# FLAC/utils/test_db_connection.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import psycopg2
from FLAC.config.db_config import DB_CONFIG

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("✅ Koneksi ke flac_db berhasil!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Gagal koneksi: {e}")
