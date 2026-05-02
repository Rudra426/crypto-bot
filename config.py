# ============================================================
# config.py — All settings. Change values marked with ← YOU
# ============================================================

# --- Exchange API Keys (Binance Testnet) ---
# Get keys from: https://testnet.binance.vision/

import os

API_KEY    = os.environ.get("API_KEY", "YOUR_BINANCE_TESTNET_API_KEY")
API_SECRET = os.environ.get("API_SECRET", "YOUR_BINANCE_TESTNET_API_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
NEWSAPI_KEY        = os.environ.get("NEWSAPI_KEY", "")


# --- Trading Pair & Timeframe ---
SYMBOL     = "BTC/USDT"   # ← YOU (e.g. "ETH/USDT", "BNB/USDT")
TIMEFRAME  = "5m"         # ← YOU (1m, 5m, 15m, 1h)
CANDLE_LIMIT = 200        # candles to fetch each cycle

# --- Testnet / Live Toggle ---
USE_TESTNET = True        # ← Set to False when going LIVE (be careful!)

# --- Capital & Risk ---
TOTAL_CAPITAL_USDT  = 100.0   # ← YOU: your total USDT budget
RISK_PER_TRADE_PCT  = 0.02    # 2% of capital risked per trade
MAX_OPEN_POSITIONS  = 1       # max concurrent trades
STOP_LOSS_PCT       = 0.02    # 2% stop loss below entry
TAKE_PROFIT_PCT     = 0.04    # 4% take profit above entry

# --- Technical Indicator Settings ---
RSI_PERIOD     = 14
RSI_OVERSOLD   = 30
RSI_OVERBOUGHT = 70
EMA_FAST       = 50
EMA_SLOW       = 200
MACD_FAST      = 12
MACD_SLOW      = 26
MACD_SIGNAL    = 9

# --- Signal Confidence Threshold ---
# LOWERED from 0.60 to 0.25 — a single indicator firing scores ~0.25-0.35
# Raise this back toward 0.50 once backtest shows profitable results
MIN_CONFIDENCE = 0.25

# --- Loop Interval ---
LOOP_INTERVAL_SECONDS = 300  # 5 minutes

# --- Telegram Alerts ---
TELEGRAM_ENABLED   = True

# --- News Sentiment ---
SENTIMENT_ENABLED = True
