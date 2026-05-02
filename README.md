# 🤖 Autonomous Crypto Trading Bot

A fully autonomous 24/7 crypto trading bot using technical indicators,
ML prediction, and news sentiment to make BUY/SELL/HOLD decisions.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure (REQUIRED — see config.py)
Edit `config.py` and fill in:
- `API_KEY` / `API_SECRET` — Binance Testnet keys
- `SYMBOL` — trading pair (e.g. "BTC/USDT")
- `TOTAL_CAPITAL_USDT` — your budget
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — (optional) for alerts

### 3. Run backtest first (STRONGLY RECOMMENDED)
```bash
python backtest/engine.py
```
Check `logs/backtest_trades.csv` for results.

### 4. Train ML model (optional)
```python
from data.fetcher import fetch_ohlcv
from strategy.indicators import compute_indicators
from strategy.ml_model import train_model

df = compute_indicators(fetch_ohlcv(limit=1000))
train_model(df)
```

### 5. Run the live bot
```bash
python main.py
```

## Deployment (24/7 on Railway/Render)
1. Push to GitHub
2. Create new service on railway.app / render.com
3. Set environment variables (API keys) in the dashboard
4. Start command: `python main.py`

## File Structure
```
crypto-bot/
├── main.py              ← Master loop
├── config.py            ← All settings (YOU edit this)
├── requirements.txt
├── data/
│   ├── fetcher.py       ← CCXT market data
│   └── sentiment.py     ← News sentiment (FinBERT)
├── strategy/
│   ├── indicators.py    ← RSI, MACD, EMA, BB
│   ├── signals.py       ← Buy/Sell/Hold logic
│   └── ml_model.py      ← Random Forest model
├── risk/
│   └── manager.py       ← Stop-loss, position sizing
├── execution/
│   └── trader.py        ← Order placement
├── backtest/
│   └── engine.py        ← Historical simulation
├── notify/
│   └── telegram.py      ← Telegram alerts
└── logs/                ← Trade logs (auto-created)
```

## Risk Disclaimer
This bot is for educational purposes. Crypto trading is highly risky.
Always run on TESTNET first. Never invest money you cannot afford to lose.
