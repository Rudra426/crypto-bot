# strategy/indicators.py — Compute technical indicators on OHLCV DataFrame

import pandas_ta as ta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

def compute_indicators(df):
    df = df.copy()

    # RSI
    df['rsi'] = ta.rsi(df['close'], length=config.RSI_PERIOD)

    # MACD — dynamic column detection
    macd = ta.macd(df['close'],
                   fast=config.MACD_FAST,
                   slow=config.MACD_SLOW,
                   signal=config.MACD_SIGNAL)
    macd_col   = [c for c in macd.columns if c.startswith('MACD_') and 'MACDs' not in c and 'MACDh' not in c][0]
    signal_col = [c for c in macd.columns if c.startswith('MACDs_')][0]
    hist_col   = [c for c in macd.columns if c.startswith('MACDh_')][0]
    df['macd']        = macd[macd_col]
    df['macd_signal'] = macd[signal_col]
    df['macd_hist']   = macd[hist_col]

    # EMA
    df['ema_fast'] = ta.ema(df['close'], length=config.EMA_FAST)
    df['ema_slow'] = ta.ema(df['close'], length=config.EMA_SLOW)

    # Bollinger Bands — dynamic column detection
    bb = ta.bbands(df['close'], length=20, std=2)
    upper_col = [c for c in bb.columns if c.startswith('BBU')][0]
    lower_col = [c for c in bb.columns if c.startswith('BBL')][0]
    mid_col   = [c for c in bb.columns if c.startswith('BBM')][0]
    df['bb_upper'] = bb[upper_col]
    df['bb_lower'] = bb[lower_col]
    df['bb_mid']   = bb[mid_col]

    # Volume MA
    df['vol_ma'] = ta.sma(df['volume'], length=20)

    return df.dropna()
