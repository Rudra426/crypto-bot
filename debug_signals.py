# debug_signals.py — Run this to see what confidence scores your signals are producing

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from data.fetcher import fetch_ohlcv
from strategy.indicators import compute_indicators
from strategy.signals import generate_signal
import config

print(f"Fetching candles for {config.SYMBOL}...")
df = fetch_ohlcv(config.SYMBOL, '1h', 300)
df = compute_indicators(df)

buy_scores  = []
sell_scores = []
hold_count  = 0

for i in range(50, min(150, len(df))):
    window = df.iloc[:i]
    sig = generate_signal(window)
    if sig['action'] == 'BUY':
        buy_scores.append(sig['confidence'])
    elif sig['action'] == 'SELL':
        sell_scores.append(sig['confidence'])
    else:
        hold_count += 1

print(f"\n--- Signal Distribution (100 candles) ---")
print(f"BUY  signals : {len(buy_scores)}  | avg confidence: {sum(buy_scores)/len(buy_scores):.3f}" if buy_scores else "BUY  signals : 0")
print(f"SELL signals : {len(sell_scores)} | avg confidence: {sum(sell_scores)/len(sell_scores):.3f}" if sell_scores else "SELL signals : 0")
print(f"HOLD         : {hold_count}")

all_scores = buy_scores + sell_scores
if all_scores:
    print(f"\nMax confidence seen : {max(all_scores):.3f}")
    print(f"Min confidence seen : {min(all_scores):.3f}")
    print(f"\n→ Recommended MIN_CONFIDENCE: {round(min(all_scores) - 0.05, 2)}")
else:
    print("\nNo BUY/SELL signals at all — checking last 5 candle indicator values:")
    print(df[['close','rsi','macd','macd_signal','ema_fast','ema_slow','bb_upper','bb_lower']].tail(5).to_string())
