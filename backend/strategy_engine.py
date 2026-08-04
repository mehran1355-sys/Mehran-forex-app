# backend/strategy_engine.py

from risk_manager import RiskManager
from chart_generator import generate_chart

risk_manager = RiskManager()


# ============================
#   Candle Class
# ============================

class Candle:
    def __init__(self, time, open_, high, low, close):
        self.time = time
        self.open = open_
        self.high = high
        self.low = low
        self.close = close

    @property
    def body(self):
        return abs(self.close - self.open)

    @property
    def is_bull(self):
        return self.close > self.open

    @property
    def upper_shadow(self):
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self):
        return min(self.open, self.close) - self.low


# ============================
#   SupplyDemandEngine Class
# ============================

class SupplyDemandEngine:
    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.tf = timeframe  # MN1, W1, D1

    def get_monitoring_timeframe(self):
        if self.tf == "MN1":
            return "D1"
        elif self.tf == "W1":
            return "H4"
        elif self.tf == "D1":
            return "H1"
        return "H1"

    def classify_candle(self, last_candle: Candle, recent_bodies):
        top_two = sorted(recent_bodies, reverse=True)[:2]
        avg = sum(top_two) / 2 if top_two else last_candle.body
        ratio = last_candle.body / avg if avg != 0 else 0

        if ratio >= 0.6:
            return "very_long"
        elif ratio >= 0.4:
            return "long"
        elif ratio >= 0.1:
            return "short"
        else:
