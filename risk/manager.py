# risk/manager.py — Position sizing, stop-loss, take-profit logic

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

class RiskManager:
    def __init__(self):
        self.open_positions = {}  # symbol -> {entry_price, qty, stop_loss, take_profit}

    def calc_position_size(self, capital_usdt, price):
        """How many units to buy given risk per trade and current price."""
        risk_amount = capital_usdt * config.RISK_PER_TRADE_PCT
        # Risk amount = qty * (entry - stop_loss)
        stop_dist = price * config.STOP_LOSS_PCT
        qty = risk_amount / stop_dist
        return round(qty, 6)

    def open_position(self, symbol, entry_price, qty):
        self.open_positions[symbol] = {
            'entry_price':  entry_price,
            'qty':          qty,
            'stop_loss':    round(entry_price * (1 - config.STOP_LOSS_PCT), 6),
            'take_profit':  round(entry_price * (1 + config.TAKE_PROFIT_PCT), 6),
        }
        print(f"[Risk] Opened {symbol}: entry={entry_price}, SL={self.open_positions[symbol]['stop_loss']}, TP={self.open_positions[symbol]['take_profit']}")

    def close_position(self, symbol):
        if symbol in self.open_positions:
            del self.open_positions[symbol]

    def should_exit(self, symbol, current_price):
        """Returns 'STOP_LOSS', 'TAKE_PROFIT', or None."""
        pos = self.open_positions.get(symbol)
        if not pos:
            return None
        if current_price <= pos['stop_loss']:
            return 'STOP_LOSS'
        if current_price >= pos['take_profit']:
            return 'TAKE_PROFIT'
        return None

    def has_open_position(self, symbol):
        return symbol in self.open_positions

    def position_count(self):
        return len(self.open_positions)
