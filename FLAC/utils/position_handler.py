from FLAC.db.db_writer import insert_position, is_pair_open, close_position as db_close_position
from FLAC.utils.price_utils import get_price

def open_position(pair, score="N/A", trend="N/A", direction="long"):
    """
    Membuka posisi baru jika belum ada yang terbuka.
    Akan menyimpan ke tabel `positions` di PostgreSQL.
    """
    if is_pair_open(pair):
        print(f"⚠️ {pair} already open — skipping.")
        return False

    price = get_price(pair)
    if price is None:
        print(f"⚠️ {pair} price not available — skipping.")
        return False

    insert_position({
        "pair": pair,
        "entry_price": price,
        "direction": direction,
        "status": "open",
        "score": score,
        "trend": trend
    })

    print(f"✅ Opened position for {pair} at {price}")
    return True

def close_position(pair):
    """
    Menutup posisi terbuka dengan mengambil harga real-time sebagai `exit_price`.
    Akan mengubah status posisi menjadi `closed` di PostgreSQL.
    """
    price = get_price(pair)
    if price is None:
        print(f"⚠️ Price not available for {pair} — cannot close position.")
        return False

    db_close_position(pair, price)
    print(f"🔒 Closed position for {pair} at {price}")
    return True
