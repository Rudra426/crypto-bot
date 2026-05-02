# execution/trader.py — Places orders via CCXT

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from data.fetcher import get_exchange

def place_buy(symbol, qty):
    """Places a market BUY order. Returns order dict."""
    exchange = get_exchange()
    try:
        order = exchange.create_market_buy_order(symbol, qty)
        print(f"[Trader] BUY {qty} {symbol} — Order ID: {order['id']}")
        return order
    except Exception as e:
        print(f"[Trader] BUY failed: {e}")
        return None

def place_sell(symbol, qty):
    """Places a market SELL order. Returns order dict."""
    exchange = get_exchange()
    try:
        order = exchange.create_market_sell_order(symbol, qty)
        print(f"[Trader] SELL {qty} {symbol} — Order ID: {order['id']}")
        return order
    except Exception as e:
        print(f"[Trader] SELL failed: {e}")
        return None

def get_current_price(symbol=None):
    symbol = symbol or config.SYMBOL
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']
