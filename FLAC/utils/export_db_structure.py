# FLAC/utils/export_db_structure.py

import psycopg2
from FLAC.config.db_config import DB_CONFIG

def export_structure(output_file="db_structure.txt"):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get all table names in public schema
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = cur.fetchall()

    with open(output_file, "w") as f:
        for table in tables:
            table_name = table[0]
            f.write(f"\n===== Structure of table: {table_name} =====\n")
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cur.fetchall()

            for col in columns:
                col_name, col_type, nullable, default = col
                f.write(f"{col_name} | {col_type} | Nullable: {nullable} | Default: {default}\n")
    
    cur.close()
    conn.close()
    print(f"✅ Struktur semua tabel disimpan di {output_file}")

if __name__ == "__main__":
    export_structure()
