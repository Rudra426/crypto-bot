# main.py — Start once, runs forever. Stop with Ctrl+C
# Usage: python main.py

import time
import datetime
import os
import csv
import sys

import config
from data.fetcher import fetch_ohlcv, get_current_price
from data.sentiment import get_sentiment_score
from strategy.indicators import compute_indicators
from strategy.signals import generate_signal
from risk.manager import RiskManager
from execution.trader import place_buy, place_sell
from notify.telegram import alert_trade, alert_exit, send_message

LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'trades_live.csv')

# ── ANSI colors ──────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def clr(text, color): return f"{color}{text}{RESET}"

def log_trade(action, price, qty, confidence, reason, pnl=0.0):
    os.makedirs('logs', exist_ok=True)
    write_header = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['timestamp','action','symbol','price','qty','confidence','reason','pnl'])
        w.writerow([
            datetime.datetime.utcnow().isoformat(),
            action, config.SYMBOL,
            round(price, 4), round(qty, 6),
            round(confidence, 4), reason, round(pnl, 4)
        ])

def print_dashboard(cycle, price, signal, position, last_trade, sentiment, total_pnl):
    os.system('cls' if os.name == 'nt' else 'clear')

    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    action  = signal['action']
    conf    = signal['confidence']
    reasons = signal['reasons']

    action_color = GREEN if action == 'BUY' else RED if action == 'SELL' else YELLOW
    action_str   = clr(f"  ● {action}  ", action_color + BOLD)

    print(clr("━" * 54, CYAN))
    print(clr(f"  🤖  CRYPTO BOT  ·  {config.SYMBOL}  ·  {config.TIMEFRAME}", BOLD))
    print(clr("━" * 54, CYAN))
    print(f"  {clr('Time   :', DIM)}  {now}")
    print(f"  {clr('Cycle  :', DIM)}  #{cycle}   (every {config.LOOP_INTERVAL_SECONDS}s)")
    print(f"  {clr('Price  :', DIM)}  {clr(f'${price:,.4f}', BOLD)}")
    print(f"  {clr('Senti. :', DIM)}  {sentiment:.3f}  {'🟢 bullish' if sentiment > 0.55 else '🔴 bearish' if sentiment < 0.45 else '🟡 neutral'}")
    print(clr("─" * 54, DIM))

    print(f"\n  SIGNAL  →{action_str}  confidence: {clr(f'{conf*100:.1f}%', action_color)}")
    for r in reasons:
        print(f"    {clr('›', DIM)} {r}")

    print(clr("\n─" * 54, DIM))
    if position:
        entry   = position['entry_price']
        qty     = position['qty']
        unreal  = (price - entry) * qty
        unreal_c = GREEN if unreal >= 0 else RED
        print(f"  {clr('OPEN POSITION', BOLD)}")
        print(f"    Entry     : ${entry:,.4f}")
        print(f"    Qty       : {qty:.6f}")
        print(f"    Stop-Loss : ${position['stop_loss']:,.4f}")
        print(f"    Take-Profit: ${position['take_profit']:,.4f}")
        print(f"    Unrealised: {clr(f'${unreal:+.4f}', unreal_c)}")
    else:
        print(f"  {clr('No open position', DIM)}")

    print(clr("\n─" * 54, DIM))
    print(f"  {clr('Realised P&L :', DIM)}  {clr(f'${total_pnl:+.4f}', GREEN if total_pnl >= 0 else RED)}")
    if last_trade:
        lt_color = GREEN if last_trade['action'] == 'BUY' else RED
        print(f"  {clr('Last Trade   :', DIM)}  {clr(last_trade['action'], lt_color)}  @ ${last_trade['price']:,.4f}  [{last_trade['reason']}]")

    print(clr("\n━" * 54, CYAN))
    print(f"  {clr('Press Ctrl+C to stop the bot', DIM)}")
    print(clr("━" * 54, CYAN))

def main():
    rm         = RiskManager()
    cycle      = 0
    total_pnl  = 0.0
    last_trade = None

    send_message("🤖 <b>Crypto Bot Started</b>\nRunning 24/7 — will notify on every trade.")
    print(clr(f"\n[BOT] Starting — {config.SYMBOL} | Testnet: {config.USE_TESTNET}", BOLD))
    print(clr(f"[BOT] Interval: {config.LOOP_INTERVAL_SECONDS}s | Min Confidence: {config.MIN_CONFIDENCE}", DIM))
    print(clr("[BOT] Bot is live. Press Ctrl+C to stop.\n", GREEN))
    time.sleep(2)

    while True:
        cycle += 1
        try:
            # ── 1. Fetch & compute ──────────────────────────────
            df    = fetch_ohlcv()
            df    = compute_indicators(df)
            price = get_current_price()

            # ── 2. Sentiment ────────────────────────────────────
            sentiment = get_sentiment_score("Bitcoin")

            # ── 3. Check stop-loss / take-profit ────────────────
            exit_reason = rm.should_exit(config.SYMBOL, price)
            if exit_reason and rm.has_open_position(config.SYMBOL):
                pos     = rm.open_positions[config.SYMBOL]
                pnl_abs = (price - pos['entry_price']) * pos['qty']
                pnl_pct = (price - pos['entry_price']) / pos['entry_price']
                order   = place_sell(config.SYMBOL, pos['qty'])
                if order:
                    total_pnl += pnl_abs
                    log_trade('SELL', price, pos['qty'], 1.0, exit_reason, pnl_abs)
                    alert_exit(exit_reason, config.SYMBOL, price, pnl_pct)
                    last_trade = {'action': 'SELL', 'price': price, 'reason': exit_reason}
                    rm.close_position(config.SYMBOL)

            # ── 4. Generate signal ──────────────────────────────
            signal = generate_signal(df, sentiment)

            # ── 5. Execute trade ────────────────────────────────
            if signal['action'] == 'BUY' and not rm.has_open_position(config.SYMBOL):
                if rm.position_count() < config.MAX_OPEN_POSITIONS:
                    qty   = rm.calc_position_size(config.TOTAL_CAPITAL_USDT, price)
                    order = place_buy(config.SYMBOL, qty)
                    if order:
                        rm.open_position(config.SYMBOL, price, qty)
                        log_trade('BUY', price, qty, signal['confidence'], 'SIGNAL')
                        alert_trade('BUY', config.SYMBOL, price, signal['confidence'], signal['reasons'])
                        last_trade = {'action': 'BUY', 'price': price, 'reason': 'SIGNAL'}

            elif signal['action'] == 'SELL' and rm.has_open_position(config.SYMBOL):
                pos     = rm.open_positions[config.SYMBOL]
                pnl_abs = (price - pos['entry_price']) * pos['qty']
                order   = place_sell(config.SYMBOL, pos['qty'])
                if order:
                    total_pnl += pnl_abs
                    log_trade('SELL', price, pos['qty'], signal['confidence'], 'SIGNAL', pnl_abs)
                    alert_trade('SELL', config.SYMBOL, price, signal['confidence'], signal['reasons'])
                    last_trade = {'action': 'SELL', 'price': price, 'reason': 'SIGNAL'}
                    rm.close_position(config.SYMBOL)

            # ── 6. Draw live dashboard ──────────────────────────
            pos_info = rm.open_positions.get(config.SYMBOL)
            # Build position dict with all fields for display
            if pos_info:
                display_pos = pos_info  # already has entry_price, qty, stop_loss, take_profit
            else:
                display_pos = None

            print_dashboard(cycle, price, signal, display_pos, last_trade, sentiment, total_pnl)

        except KeyboardInterrupt:
            print(clr("\n\n[BOT] Stopped by user. Goodbye!\n", YELLOW))
            send_message("🛑 <b>Bot stopped</b> by user.")
            sys.exit(0)

        except Exception as e:
            print(clr(f"\n[ERROR] Cycle {cycle}: {e}", RED))
            send_message(f"⚠️ Bot error (cycle {cycle}): {e}")

        # ── Countdown timer ─────────────────────────────────────
        for remaining in range(config.LOOP_INTERVAL_SECONDS, 0, -1):
            sys.stdout.write(f"\r  {clr('Next scan in:', DIM)} {clr(str(remaining) + 's ', CYAN)}  ")
            sys.stdout.flush()
            time.sleep(1)

if __name__ == '__main__':
    main()
