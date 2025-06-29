# FLAC/utils/price_utils.py
import ccxt

BINANCE = ccxt.binance()

def get_price(pair):
    try:
        symbol = pair if '/' in pair else pair.replace("USDT", "/USDT")
        ticker = BINANCE.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"❌ Failed to get price for {pair}: {e}")
        return None
