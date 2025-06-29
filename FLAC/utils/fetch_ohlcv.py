import ccxt
import pandas as pd

def fetch_ohlcv(pair, timeframe='1d', default_market='futures', limit=100):
    exchange = ccxt.binance()
    exchange.options['defaultType'] = default_market  # ✅ penting!

    market = exchange.load_markets()
    
    # Gunakan langsung pair seperti 'BTC/USDT' (bukan 'BTCUSDT')
    base_symbol = pair if '/' in pair else pair.replace("USDT", "/USDT")

    if default_market == 'spot':
        if base_symbol not in market:
            print(f"[ERROR] {base_symbol} not available in spot market.")
            return pd.DataFrame()
        symbol = base_symbol

    elif default_market == 'futures':
        futures_symbol = base_symbol + ":USDT"
        if futures_symbol not in market:
            print(f"[ERROR] {futures_symbol} not available in futures market.")
            return pd.DataFrame()
        symbol = futures_symbol

    else:
        print(f"[ERROR] Invalid market type: {default_market}")
        return pd.DataFrame()

    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch OHLCV for {pair} ({symbol}): {e}")
        return pd.DataFrame()
