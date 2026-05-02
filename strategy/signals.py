# strategy/signals.py — Rule-based multi-indicator signal engine

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

def generate_signal(df, sentiment_score=0.5):
    """
    Returns dict: { 'action': 'BUY'|'SELL'|'HOLD', 'confidence': float, 'reasons': [str] }

    Scoring breakdown (max possible = 1.0):
      RSI             : 0.30
      MACD crossover  : 0.25
      EMA trend       : 0.20
      Bollinger Band  : 0.15
      Volume confirm  : 0.10
      Sentiment       : 0.10  (only if SENTIMENT_ENABLED)
    A single strong indicator fires ~0.25-0.30, two indicators = ~0.50
    """
    if len(df) < 3:
        return {'action': 'HOLD', 'confidence': 0.0, 'reasons': ['Not enough data']}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_score  = 0.0
    sell_score = 0.0
    reasons    = []

    # --- RSI (weight: 0.30) ---
    rsi = last['rsi']
    if rsi < config.RSI_OVERSOLD:
        buy_score += 0.30
        reasons.append(f"RSI oversold ({rsi:.1f} < {config.RSI_OVERSOLD})")
    elif rsi < 40:
        buy_score += 0.15
        reasons.append(f"RSI approaching oversold ({rsi:.1f})")
    elif rsi > config.RSI_OVERBOUGHT:
        sell_score += 0.30
        reasons.append(f"RSI overbought ({rsi:.1f} > {config.RSI_OVERBOUGHT})")
    elif rsi > 60:
        sell_score += 0.15
        reasons.append(f"RSI approaching overbought ({rsi:.1f})")

    # --- MACD crossover (weight: 0.25) ---
    macd_cross_up   = prev['macd'] < prev['macd_signal'] and last['macd'] >= last['macd_signal']
    macd_cross_down = prev['macd'] > prev['macd_signal'] and last['macd'] <= last['macd_signal']
    macd_positive   = last['macd'] > 0 and last['macd_hist'] > 0
    macd_negative   = last['macd'] < 0 and last['macd_hist'] < 0

    if macd_cross_up:
        buy_score += 0.25
        reasons.append("MACD bullish crossover")
    elif macd_positive:
        buy_score += 0.12
        reasons.append(f"MACD positive momentum ({last['macd']:.2f})")

    if macd_cross_down:
        sell_score += 0.25
        reasons.append("MACD bearish crossover")
    elif macd_negative:
        sell_score += 0.12
        reasons.append(f"MACD negative momentum ({last['macd']:.2f})")

    # --- EMA trend filter (weight: 0.20) ---
    price = last['close']
    if price > last['ema_fast'] and last['ema_fast'] > last['ema_slow']:
        buy_score += 0.20
        reasons.append("Uptrend: price > EMA50 > EMA200")
    elif price > last['ema_fast']:
        buy_score += 0.10
        reasons.append("Price above EMA50")
    elif price < last['ema_fast'] and last['ema_fast'] < last['ema_slow']:
        sell_score += 0.20
        reasons.append("Downtrend: price < EMA50 < EMA200")
    elif price < last['ema_fast']:
        sell_score += 0.10
        reasons.append("Price below EMA50")

    # --- Bollinger Bands (weight: 0.15) ---
    if price < last['bb_lower']:
        buy_score += 0.15
        reasons.append("Price below lower Bollinger Band (oversold)")
    elif price < last['bb_mid']:
        buy_score += 0.07
        reasons.append("Price below BB midline")
    elif price > last['bb_upper']:
        sell_score += 0.15
        reasons.append("Price above upper Bollinger Band (overbought)")
    elif price > last['bb_mid']:
        sell_score += 0.07
        reasons.append("Price above BB midline")

    # --- Volume confirmation (weight: 0.10) ---
    if last['volume'] > last['vol_ma'] * 1.3:
        if buy_score >= sell_score:
            buy_score += 0.10
            reasons.append(f"High volume confirming bullish move")
        else:
            sell_score += 0.10
            reasons.append(f"High volume confirming bearish move")

    # --- Sentiment (weight: 0.10, only when enabled) ---
    if config.SENTIMENT_ENABLED:
        if sentiment_score > 0.65:
            buy_score += 0.10
            reasons.append(f"Positive news sentiment ({sentiment_score:.2f})")
        elif sentiment_score < 0.35:
            sell_score += 0.10
            reasons.append(f"Negative news sentiment ({sentiment_score:.2f})")

    # --- Final decision ---
    confidence = round(max(buy_score, sell_score), 4)

    if buy_score >= config.MIN_CONFIDENCE and buy_score > sell_score:
        return {'action': 'BUY',  'confidence': buy_score,  'reasons': reasons}
    elif sell_score >= config.MIN_CONFIDENCE and sell_score > buy_score:
        return {'action': 'SELL', 'confidence': sell_score, 'reasons': reasons}
    else:
        return {'action': 'HOLD', 'confidence': confidence, 'reasons': reasons}
