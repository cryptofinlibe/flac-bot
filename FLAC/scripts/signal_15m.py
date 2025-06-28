import os
import pandas as pd
from datetime import datetime
from FLAC.utils.smart_fetch import smart_fetch
from FLAC.scripts.get_active_pairs import get_active_pairs
from FLAC.utils.notifier import send_telegram_message
from FLAC.utils.position_handler import open_position
from FLAC.scripts.exit_tracker import run_exit_tracker
from FLAC.scripts.strategy_decision import analyze_with_sentiment
from FLAC.db.db_writer import insert_snapshot_15m

from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator

VOLUME_MULTIPLIER = 1.8
RSI_LONG_THRESHOLD = 55
RSI_SHORT_THRESHOLD = 45
MACD_CONFIRM = 0
ADX_THRESHOLD = 20


def load_smc_bias():
    from FLAC.utils.smc_loader import get_latest_smc_bias
    return get_latest_smc_bias()


def validate_4h(pair):
    from FLAC.utils.snapshot_loader import get_latest_snapshot_4h
    return get_latest_snapshot_4h(pair)


def run_signal_15m():
    today_str = datetime.utcnow().strftime('%Y%m%d')
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
                continue

            sentiment_info = analyze_with_sentiment(pair.split('/')[0])
            if sentiment_info:
                print(f"[🧠 CONTEXT] {pair} sentiment/onchain info:\n{sentiment_info}\n")

            if smc == "LONG" and close > sma and volume > vol_avg * VOLUME_MULTIPLIER and rsi > RSI_LONG_THRESHOLD and macd > MACD_CONFIRM:
                signals.append([pair, latest['timestamp'], 'LONG', rsi, volume, macd, adx])
                triggered.append(f"📈 {pair} LONG @ {close:.2f}")
                open_position(pair, trend='LONG')

            elif smc == "SHORT" and close < sma and volume > vol_avg * VOLUME_MULTIPLIER and rsi < RSI_SHORT_THRESHOLD and macd < -MACD_CONFIRM:
                signals.append([pair, latest['timestamp'], 'SHORT', rsi, volume, macd, adx])
                triggered.append(f"📉 {pair} SHORT @ {close:.2f}")
                open_position(pair, trend='SHORT')

        except Exception as e:
            print(f"❌ Error processing {pair}: {e}")

    for sig in signals:
        insert_snapshot_15m(
            pair=sig[0],
            timestamp=sig[1],
            entry_signal=sig[2],
            rsi=sig[3],
            volume=sig[4],
            macd=sig[5],
            adx=sig[6]
        )

    if triggered:
        send_telegram_message("🚨 15M Signals:\n" + "\n".join(triggered))
        print(f"✅ {len(triggered)} signal(s) inserted into DB.")
    else:
        send_telegram_message("✅ 15M signal check done — no valid signal at this moment.")
        print("⛔ No valid 15M signal detected")

    run_exit_tracker()


if __name__ == "__main__":
    run_signal_15m()
