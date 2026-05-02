# data/fetcher.py — Fetches OHLCV market data via CCXT

import ccxt
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

def get_exchange():
    exchange = ccxt.binance({
        'apiKey': config.API_KEY,
        'secret': config.API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    if config.USE_TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange

def fetch_ohlcv(symbol=None, timeframe=None, limit=None):
    symbol    = symbol    or config.SYMBOL
    timeframe = timeframe or config.TIMEFRAME
    limit     = limit     or config.CANDLE_LIMIT

    exchange = get_exchange()
    raw = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def fetch_ticker(symbol=None):
    symbol = symbol or config.SYMBOL
    exchange = get_exchange()
    return exchange.fetch_ticker(symbol)

def fetch_balance():
    exchange = get_exchange()
    return exchange.fetch_balance()

def get_current_price(symbol=None):
    symbol = symbol or config.SYMBOL
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return float(ticker['last'])