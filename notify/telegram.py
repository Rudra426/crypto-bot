# notify/telegram.py — Telegram alerts

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

def send_message(text):
    if not config.TELEGRAM_ENABLED:
        print(f"[Telegram DISABLED] {text}")
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': config.TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}, timeout=10)
    except Exception as e:
        print(f"[Telegram] Failed: {e}")

def alert_trade(action, symbol, price, confidence, reasons):
    emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
    msg = (
        f"{emoji} <b>{action} {symbol}</b>\n"
        f"💰 Price: {price}\n"
        f"📊 Confidence: {confidence*100:.1f}%\n"
        f"📝 Reasons:\n" + "\n".join(f"  • {r}" for r in reasons)
    )
    send_message(msg)

def alert_exit(reason, symbol, price, pnl_pct):
    emoji = "✅" if pnl_pct >= 0 else "❌"
    msg = (
        f"{emoji} <b>EXIT {symbol}</b> [{reason}]\n"
        f"💰 Price: {price}\n"
        f"📈 P&L: {pnl_pct*100:.2f}%"
    )
    send_message(msg)
