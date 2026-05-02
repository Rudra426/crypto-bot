# backtest/engine.py — Simulate strategy on historical OHLCV data

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import config
from data.fetcher import fetch_ohlcv
from strategy.indicators import compute_indicators
from strategy.signals import generate_signal

def run_backtest(symbol=None, timeframe='1h', limit=500, initial_capital=1000.0):
    symbol = symbol or config.SYMBOL
    print(f"[Backtest] Fetching {limit} {timeframe} candles for {symbol}...")
    df = fetch_ohlcv(symbol, timeframe, limit)
    df = compute_indicators(df)

    capital  = initial_capital
    position = None   # dict: {entry, qty, sl, tp}
    trades   = []     # list of dicts
    sl_pct   = config.STOP_LOSS_PCT
    tp_pct   = config.TAKE_PROFIT_PCT
    risk_pct = config.RISK_PER_TRADE_PCT

    for i in range(config.EMA_SLOW + 5, len(df)):
        window = df.iloc[:i]
        price  = float(df.iloc[i]['close'])
        signal = generate_signal(window)

        # --- Check exits first ---
        if position:
            exit_reason = None
            if price <= position['sl']:
                exit_reason = 'STOP_LOSS'
            elif price >= position['tp']:
                exit_reason = 'TAKE_PROFIT'

            if exit_reason:
                pnl = (price - position['entry']) * position['qty']
                capital += price * position['qty']
                trades.append({
                    'action': 'SELL',
                    'price':  price,
                    'qty':    position['qty'],
                    'pnl':    round(pnl, 4),
                    'reason': exit_reason,
                    'time':   df.index[i]
                })
                position = None
                continue

        # --- Entry ---
        if signal['action'] == 'BUY' and position is None:
            risk_amt  = capital * risk_pct
            stop_dist = price * sl_pct
            qty       = risk_amt / stop_dist if stop_dist > 0 else 0
            cost      = qty * price
            if cost > capital:
                qty  = capital / price
                cost = capital
            if qty > 0:
                capital -= cost
                position = {
                    'entry': price,
                    'qty':   qty,
                    'sl':    price * (1 - sl_pct),
                    'tp':    price * (1 + tp_pct)
                }
                trades.append({
                    'action': 'BUY',
                    'price':  price,
                    'qty':    qty,
                    'pnl':    0.0,
                    'reason': 'SIGNAL',
                    'time':   df.index[i]
                })

        # --- Signal SELL (before SL/TP) ---
        elif signal['action'] == 'SELL' and position is not None:
            pnl = (price - position['entry']) * position['qty']
            capital += price * position['qty']
            trades.append({
                'action': 'SELL',
                'price':  price,
                'qty':    position['qty'],
                'pnl':    round(pnl, 4),
                'reason': 'SIGNAL',
                'time':   df.index[i]
            })
            position = None

    # --- Close any open position at end of data ---
    if position:
        price = float(df.iloc[-1]['close'])
        pnl   = (price - position['entry']) * position['qty']
        capital += price * position['qty']
        trades.append({
            'action': 'SELL',
            'price':  price,
            'qty':    position['qty'],
            'pnl':    round(pnl, 4),
            'reason': 'END_OF_DATA',
            'time':   df.index[-1]
        })

    # --- Results ---
    if not trades:
        print("\n[Backtest] No trades were executed. Try lowering MIN_CONFIDENCE in config.py.")
        return pd.DataFrame()

    trades_df  = pd.DataFrame(trades)
    sells      = trades_df[trades_df['action'] == 'SELL']
    total_pnl  = sells['pnl'].sum()
    wins       = sells[sells['pnl'] > 0]
    losses     = sells[sells['pnl'] <= 0]
    win_rate   = len(wins) / len(sells) if len(sells) > 0 else 0
    ret_pct    = (capital - initial_capital) / initial_capital * 100

    print(f"\n{'='*45}")
    print(f"  BACKTEST RESULTS — {symbol} ({timeframe})")
    print(f"{'='*45}")
    print(f"  Initial Capital  : ${initial_capital:.2f}")
    print(f"  Final Capital    : ${capital:.2f}")
    print(f"  Total P&L        : ${total_pnl:.2f}")
    print(f"  Return           : {ret_pct:.2f}%")
    print(f"  Total Trades     : {len(sells)}")
    print(f"  Wins / Losses    : {len(wins)} / {len(losses)}")
    print(f"  Win Rate         : {win_rate*100:.1f}%")
    print(f"{'='*45}\n")

    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    out_path = os.path.join(log_dir, 'backtest_trades.csv')
    trades_df.to_csv(out_path, index=False)
    print(f"[Backtest] Saved trade log → logs/backtest_trades.csv")

    return trades_df

if __name__ == '__main__':
    run_backtest()
