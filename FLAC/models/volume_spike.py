import pandas as pd

def detect_volume_spike(volume_series, window=20, threshold_ratio=1.5):
    """
    volume_series: pd.Series of volume data (ordered oldest to latest)
    window: jumlah candle rata-rata (default 20)
    threshold_ratio: multiplier dari MA volume (default 1.5x)

    return: dict hasil deteksi
    """
    if len(volume_series) < window:
        return {
            "volume_spike": False,
            "reason": "Data terlalu sedikit",
            "latest_volume": None,
            "average_volume": None
        }

    average_volume = volume_series[-window:].mean()
    latest_volume = volume_series.iloc[-1]

    return {
        "volume_spike": latest_volume > average_volume * threshold_ratio,
        "latest_volume": latest_volume,
        "average_volume": round(average_volume, 2),
        "threshold_ratio": threshold_ratio
    }
