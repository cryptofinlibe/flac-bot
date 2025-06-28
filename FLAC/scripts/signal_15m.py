import os
import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.scripts.get_active_pairs import get_active_pairs
from FLAC.utils.notifier import send_telegram_message
from FLAC.utils.position_handler import open_position, is_pair_open
from FLAC.scripts.exit_tracker import run_exit_tracker
from FLAC.scripts.strategy_decision import analyze_with_sentiment

from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator

SIGNAL_PATH = "FLAC/data/logs"
SNAPSHOT_4H = "FLAC/data/snapshots/4h"
MERGED_DAILY_PATH = "FLAC/data/logs/smc_merged_{}.csv".format(datetime.utcnow().strftime('%Y%m%d'))

VOLUME_MULTIPLIER = 1.8
RSI_LONG_THRESHOLD = 55
RSI_SHORT_THRESHOLD = 45
MACD_CONFIRM = 0
ADX_THRESHOLD = 20

def load_smc_bias():
    if not os.path.exists(MERGED_DAILY_PATH):
        print("\u26a0\ufe0f SMC Merged file not found")
        return {}
    df = pd.read_csv(MERGED_DAILY_PATH)
    return dict(zip(df['pair'], df['bias']))

def validate_4h(pair):
    filename = f"{pair.replace('/', '_')}.csv"
    filepath = os.path.join(SNAPSHOT_4H, filename)
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath)
    if df.empty:
        return None
    last_candle = df.iloc[-1]
    return "LONG" if last_candle['close'] > last_candle['open'] else "SHORT"

def run_signal_15m():
    os.makedirs(SIGNAL_PATH, exist_ok=True)
    today_str = datetime.utcnow().strftime('%Y%m%d')
    output_file = os.path.join(SIGNAL_PATH, f"signal_15m_{today_str}.csv")

    config = get_active_pairs()
    pairs = config.get("15m", [])
    smc_bias = load_smc_bias()
    triggered = []
    signals = []

    for pair in pairs:
        try:
            df = smart_fetch(pair, timeframe='15m', default_market='spot', max_limit=100)
            if df is None or df.empty or len(df) < 30:
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', inplace=True)

            # Indicators
            df['sma20'] = SMAIndicator(df['close'], window=20).sma_indicator()
            df['vol_ma20'] = df['volume'].rolling(20).mean()
            df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
            df['macd'] = MACD(df['close']).macd_diff()
            df['adx'] = ADXIndicator(df['high'], df['low'], df['close']).adx()

            latest = df.iloc[-1]
            sma = latest['sma20']
            vol_avg = latest['vol_ma20']
            rsi = latest['rsi']
            macd = latest['macd']
            adx = latest['adx']
            close = latest['close']
            volume = latest['volume']

            smc = smc_bias.get(pair.replace('_', '/'), None)
            confirm_4h = validate_4h(pair)

            if not smc or not confirm_4h or smc != confirm_4h:
                continue

            if adx < ADX_THRESHOLD:
                continue  # Skip weak trends

            sentiment_info = analyze_with_sentiment(pair.split('/')[0])
            if sentiment_info:
                print(f"[\U0001f9e0 CONTEXT] {pair} sentiment/onchain info:\n{sentiment_info}\n")

            if smc == "LONG" and close > sma and volume > vol_avg * VOLUME_MULTIPLIER and rsi > RSI_LONG_THRESHOLD and macd > MACD_CONFIRM:
                signals.append([pair, latest['timestamp'], 'LONG', close, round(rsi,2), round(volume,2), round(macd,2), round(adx,2)])
                triggered.append(f"\ud83d\udcc8 {pair} LONG @ {close:.2f}")
                open_position(pair, trend='LONG')

            elif smc == "SHORT" and close < sma and volume > vol_avg * VOLUME_MULTIPLIER and rsi < RSI_SHORT_THRESHOLD and macd < -MACD_CONFIRM:
                signals.append([pair, latest['timestamp'], 'SHORT', close, round(rsi,2), round(volume,2), round(macd,2), round(adx,2)])
                triggered.append(f"\ud83d\udcc9 {pair} SHORT @ {close:.2f}")
                open_position(pair, trend='SHORT')

        except Exception as e:
            print(f"\u274c Error processing {pair}: {e}")

    if signals:
        pd.DataFrame(signals, columns=['pair', 'timestamp', 'signal', 'price', 'rsi', 'volume', 'macd', 'adx']).to_csv(output_file, index=False)
        send_telegram_message("\ud83d\udea8 15M Signals:\n" + "\n".join(triggered))
        print(f"\u2705 Signal saved: {output_file}")
    else:
        send_telegram_message("\u2705 15M signal check done — no valid signal at this moment.")
        print("\u26d4 No valid 15M signal detected")

    run_exit_tracker()

if __name__ == "__main__":
    run_signal_15m()