import ccxt
import pandas as pd

def fetch_ohlcv(pair, timeframe='1d', default_market='futures', limit=100):
    exchange = ccxt.binance()
    market = exchange.load_markets()
    
    base_symbol = pair.replace("USDT", "/USDT")
    
    if default_market == 'spot':
        if base_symbol in market:
            symbol = base_symbol
        else:
            print(f"[ERROR] {pair} not available in spot market.")
            return pd.DataFrame()
    elif default_market == 'futures':
        futures_symbol = base_symbol + ":USDT"
        if futures_symbol in market:
            symbol = futures_symbol
        else:
            print(f"[ERROR] {pair} not available in futures market.")
            return pd.DataFrame()
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
