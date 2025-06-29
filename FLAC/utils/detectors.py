import pandas as pd

def detect_volatility_1h(df: pd.DataFrame, pair: str) -> dict:
    try:
        price_change = abs(df["close"].iloc[-1] - df["open"].iloc[-1]) / df["open"].iloc[-1] * 100
        volume_now = df["volume"].iloc[-1]
        vol_ma = df["volume"].rolling(20).mean().iloc[-2]
        atr = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]
        atr_ma = (df["high"] - df["low"]).rolling(14).mean().rolling(20).mean().iloc[-2]

        is_spike = (
            (price_change > 2 and volume_now > vol_ma * 1.5)
            or (atr > atr_ma * 1.5)
        )

        return {
            "symbol": pair,
            "time_logged": df["timestamp"].iloc[-1],
            "price_change": round(price_change, 2),
            "volume": round(volume_now, 2),
            "vol_ma": round(vol_ma, 2),
            "atr": round(atr, 2),
            "atr_ma": round(atr_ma, 2),
            "is_spike": is_spike,
            "notes": "Volatility spike" if is_spike else "Normal"
        }

    except Exception as e:
        print(f"[ERROR] Volatility calc failed for {pair}: {e}")
        return None
