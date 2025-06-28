import pandas as pd

def is_stochrsi_oversold(close_prices, period=14, smooth_k=3, smooth_d=3, threshold=20):
    close = pd.Series(close_prices)

    # Hitung RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Hitung StochRSI
    stochrsi = (rsi - rsi.rolling(period).min()) / (rsi.rolling(period).max() - rsi.rolling(period).min()) * 100
    k = stochrsi.rolling(smooth_k).mean()
    d = k.rolling(smooth_d).mean()

    # Cek oversold (k dan d < threshold)
    if k.iloc[-1] < threshold and d.iloc[-1] < threshold:
        return True
    return False
