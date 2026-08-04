from risk_manager import RiskManager
import datetime

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
            return "very_short"

    def is_long_shadow(self, body, shadow, candle_type):
        if self.tf in ["MN1", "W1"]:
            if candle_type in ["long", "very_long"]:
                return shadow >= body
            else:
                return shadow >= 2 * body
        elif self.tf == "D1":
            if candle_type in ["long", "very_long"]:
                return shadow >= 1.5 * body
            else:
                return shadow >= 2.5 * body
        return False

    def calculate_orange_lines(self, df_dict):
        candles = [
            Candle(t, o, h, l, c)
            for t, o, h, l, c in zip(
                df_dict["time"], df_dict["open"], df_dict["high"], df_dict["low"], df_dict["close"]
            )
        ]
        last = candles[-1]

        window = 12 if self.tf == "MN1" else 24 if self.tf == "W1" else 30
        recent = candles[-window:]
        recent_bodies = [c.body for c in recent]

        candle_type = self.classify_candle(last, recent_bodies)

        body = last.body
        up_shadow = last.upper_shadow
        down_shadow = last.lower_shadow

        up_long = self.is_long_shadow(body, up_shadow, candle_type)
        down_long = self.is_long_shadow(body, down_shadow, candle_type)

        if candle_type == "very_long":
            if last.is_bull:
                line1 = last.close - 0.25 * body
                line2 = last.high if not up_long else last.high - up_shadow * 0.5
            else:
                line1 = last.close + 0.25 * body
                line2 = last.low if not down_long else last.low + down_shadow * 0.5

        elif candle_type == "long":
            if last.is_bull:
                line1 = last.open + 0.5 * body
                line2 = last.high if not up_long else last.high - up_shadow * 0.5
            else:
                line1 = last.close + 0.5 * body
                line2 = last.low if not down_long else last.low + down_shadow * 0.5

        else:
            line2 = last.high - up_shadow * 0.5 if up_long else last.high
            line1 = last.low + down_shadow * 0.5 if down_long else last.low

        top_orange = max(line1, line2)
        bottom_orange = min(line1, line2)

        category_map = {
            "very_long": "کندل خیلی بلند",
            "long": "کندل بلند",
            "short": "کندل کوتاه",
            "very_short": "کندل خیلی کوتاه",
        }

        return {
            "category": category_map.get(candle_type, candle_type),
            "top_orange": top_orange,
            "bottom_orange": bottom_orange,
        }

    def calculate_zones(self, orange_info, touched_top_first):
        top = orange_info["top_orange"]
        bottom = orange_info["bottom_orange"]
        zone_size = abs(top - bottom)
        one_third = zone_size / 3

        if touched_top_first:
            near = (top - one_third, top)
            mid = (top - 2 * one_third, top - one_third)
            far = (bottom, top - 2 * one_third)
        else:
            near = (bottom, bottom + one_third)
            mid = (bottom + one_third, bottom + 2 * one_third)
            far = (bottom + 2 * one_third, top)

        return {"near": near, "mid": mid, "far": far}

    def detect_breakout(self, df_dict, orange_info):
        top = orange_info["top_orange"]
        bottom = orange
