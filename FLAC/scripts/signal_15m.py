import pandas as pd
from datetime import datetime
from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator

from FLAC.utils.smart_fetch import smart_fetch
from FLAC.utils.notifier import send_telegram_message
from FLAC.utils.position_handler import open_position
from FLAC.db.db_reader import get_active_pairs_by_timeframe
from FLAC.db.db_reader import get_latest_smc_bias
from FLAC.db.db_reader import get_latest_snapshot_4h
from FLAC.db.db_writer import insert_snapshot_15m
from FLAC.scripts.strategy_decision import analyze_with_sentiment
from FLAC.scripts.exit_tracker import run_exit_tracker

# === Parameter sinyal ===
VOLUME_MULTIPLIER = 1.8
RSI_LONG_THRESHOLD = 55
RSI_SHORT_THRESHOLD = 45
MACD_CONFIRM = 0
ADX_THRESHOLD = 20

def run_signal_15m():
    today_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    print(f"🚨 Running 15M Signal Scanner — {today_str}")

    pairs = get_active_pairs_by_timeframe('15m')
    triggered = []

    for pair in pairs:
        try:
            df = smart_fetch(pair, timeframe='15m', default_market='spot', max_limit=100)
            if df is None or df.empty or len(df) < 30:
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', inplace=True)

            df['sma20'] = SMAIndicator(df['close'], window=20).sma_indicator()
            df['vol_ma20'] = df['volume'].rolling(20).mean()
            df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
            df['macd'] = MACD(df['close']).macd_diff()
            df['adx'] = ADXIndicator(df['high'], df['low'], df['close']).adx()

            latest = df.iloc[-1]
            timestamp = latest['timestamp']
            close = latest['close']
            volume = latest['volume']
            sma = latest['sma20']
            vol_avg = latest['vol_ma20']
            rsi = latest['rsi']
            macd = latest['macd']
            adx = latest['adx']

            # Ambil SMC dan 4H trend
            smc = get_latest_smc_bias(pair)
            structure = get_latest_snapshot_4h(pair)
            if not smc or not structure or smc != structure:
                continue
            if adx < ADX_THRESHOLD:
                continue

            sentiment_info = analyze_with_sentiment(pair.split('/')[0])
            if sentiment_info:
                print(f"[🧠 CONTEXT] {pair} sentiment/onchain info:\n{sentiment_info}\n")

            entry_signal = None
            if smc == "LONG" and close > sma and volume > vol_avg * VOLUME_MULTIPLIER and rsi > RSI_LONG_THRESHOLD and macd > MACD_CONFIRM:
                entry_signal = "LONG"
            elif smc == "SHORT" and close < sma and volume > vol_avg * VOLUME_MULTIPLIER and rsi < RSI_SHORT_THRESHOLD and macd < -MACD_CONFIRM:
                entry_signal = "SHORT"

            if entry_signal:
                score = f"{rsi:.1f}-{macd:.2f}-{adx:.1f}"
                insert_snapshot_15m(
                    pair=pair,
                    datetime=timestamp,
                    entry_signal=entry_signal,
                    rsi=rsi,
                    volume=volume,
                    macd=macd,
                    adx=adx
                )
                open_position(pair, trend=entry_signal, score=score, direction=entry_signal.lower())
                triggered.append(
                    f"{'📈' if entry_signal == 'LONG' else '📉'} {pair} {entry_signal} @ {close:.2f} — RSI:{rsi:.1f} Vol:{volume:.0f} ADX:{adx:.1f}"
                )

        except Exception as e:
            print(f"❌ Error processing {pair}: {e}")

    if triggered:
        send_telegram_message("⚡ 15M Signals:\n" + "\n".join(triggered))
    else:
        send_telegram_message("✅ 15M scan complete: No valid signal found.")

    run_exit_tracker()

if __name__ == "__main__":
    run_signal_15m()
