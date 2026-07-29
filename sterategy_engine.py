Mehran Sabbabeh:
"""
استراتژی روانشناسی عرضه و تقاضا - Supply & Demand Psychology Strategy
نویسنده: AI Assistant (بر اساس استراتژی Mehran Sababeh)
نسخه کامل با اتصال به متاتریدر ۵ (MT5) و مدیریت کامل قوانین
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# در صورت عدم نصب متاتریدر، برنامه در حالت شبیه‌سازی کار خواهد کرد
try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


# ============================================================
# بخش ۱: تعاریف پایه و ساختار داده‌ها
# ============================================================


class CandleSize(Enum):
    VERY_LONG = "خیلی_بلند"
    LONG = "بلند"
    SHORT = "کوتاه"
    VERY_SHORT = "خیلی_کوتاه"


class CandleDirection(Enum):
    BULLISH = "صعودی"
    BEARISH = "نزولی"


class BreakType(Enum):
    NONE = "هیچ"
    INITIAL = "شکست_اولیه"
    COMPLETE = "شکست_تکمیلی"


@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    time: Optional[datetime] = None

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def direction(self) -> CandleDirection:
        return (
            CandleDirection.BULLISH
            if self.close >= self.open
            else CandleDirection.BEARISH
        )

    @property
    def upper_shadow(self) -> float:
        return (
            (self.high - self.close)
            if self.direction == CandleDirection.BULLISH
            else (self.high - self.open)
        )

    @property
    def lower_shadow(self) -> float:
        return (
            (self.open - self.low)
            if self.direction == CandleDirection.BULLISH
            else (self.close - self.low)
        )


@dataclass
class OrangeLines:
    upper: float
    lower: float

    @property
    def height(self) -> float:
        return abs(self.upper - self.lower)


@dataclass
class TradingZones:
    near_zone: Tuple[float, float]
    middle_zone: Tuple[float, float]
    far_zone: Tuple[float, float]


@dataclass
class PurpleLine:
    price: float
    is_above: bool
    candle_index: int
    timeframe: str


# ============================================================
# بخش ۲: آنالیز اندازه کندل و سایه‌ها
# ============================================================


class ShadowAnalyzer:

    @staticmethod
    def is_long_shadow(
        candle: Candle,
        candle_size: CandleSize,
        timeframe: str,
        shadow_type: str,
    ) -> bool:
        body = candle.body_size
        if body == 0:
            return True

        shadow = (
            candle.upper_shadow if shadow_type == "upper" else candle.lower_shadow
        )

        if timeframe in ["monthly", "weekly"]:
            if candle_size in [CandleSize.VERY_LONG, CandleSize.LONG]:
                return shadow >= body
            else:
                return shadow >= (2.0 * body)
        else:  # daily, 4h, 1h
            if candle_size in [CandleSize.VERY_LONG, CandleSize.LONG]:
                return shadow >= (1.5 * body)
            else:
                return shadow >= (2.5 * body)


class CandleSizeCalculator:

    LOOKBACK_PERIODS = {"monthly": 12, "weekly": 24, "daily": 30}

    @staticmethod
    def calculate(
        candles: List[Candle], timeframe: str
    ) -> Tuple[CandleSize, float]:
        n = CandleSizeCalculator.LOOKBACK_PERIODS.get(timeframe, 30)
        recent = candles[-n:] if len(candles) >= n else candles

        if len(recent) < 2:
            return CandleSize.SHORT, 0.0

        analysis_candle = recent[-1]
        bodies = [c.body_size for c in recent]
        sorted_bodies = sorted(bodies, reverse=True)
        top_two_avg = sum(sorted_bodies[:2]) / 2.0

        if top_two_avg == 0:
            return CandleSize.VERY_SHORT, 0.0

        ratio = analysis_candle.body_size / top_two_avg

if ratio >= 0.6:
            return CandleSize.VERY_LONG, ratio
        elif 0.4 <= ratio < 0.6:
            return CandleSize.LONG, ratio
        elif 0.1 <= ratio < 0.4:
            return CandleSize.SHORT, ratio
        else:
            return CandleSize.VERY_SHORT, ratio


# ============================================================
# بخش ۳: رسم خطوط نارنجی (پوشش کامل تمامی حالات)
# ============================================================


class OrangeLineDrawer:

    @staticmethod
    def draw(
        candle: Candle, candle_size: CandleSize, timeframe: str
    ) -> OrangeLines:
        body = candle.body_size
        upper_long = ShadowAnalyzer.is_long_shadow(
            candle, candle_size, timeframe, "upper"
        )
        lower_long = ShadowAnalyzer.is_long_shadow(
            candle, candle_size, timeframe, "lower"
        )

        if candle.direction == CandleDirection.BULLISH:
            # خط اول (پایینی یا بدنه)
            if candle_size == CandleSize.VERY_LONG:
                line1 = candle.close - (0.25 * body)
            elif candle_size == CandleSize.LONG:
                line1 = candle.open + (0.50 * body)
            else:  # SHORT or VERY_SHORT
                line1 = (
                    (candle.low + 0.5 * candle.lower_shadow)
                    if lower_long
                    else candle.low
                )

            # خط دوم (بالایی)
            if candle_size in [CandleSize.VERY_LONG, CandleSize.LONG]:
                line2 = (
                    (candle.close + 0.5 * candle.upper_shadow)
                    if upper_long
                    else candle.high
                )
            else:
                line2 = (
                    (candle.high - 0.5 * candle.upper_shadow)
                    if upper_long
                    else candle.high
                )

        else:  # BEARISH
            # خط اول (بالایی یا بدنه)
            if candle_size == CandleSize.VERY_LONG:
                line1 = candle.close + (0.25 * body)
            elif candle_size == CandleSize.LONG:
                line1 = candle.open - (0.50 * body)
            else:  # SHORT or VERY_SHORT
                line1 = (
                    (candle.high - 0.5 * candle.upper_shadow)
                    if upper_long
                    else candle.high
                )

            # خط دوم (پایینی)
            if candle_size in [CandleSize.VERY_LONG, CandleSize.LONG]:
                line2 = (
                    (candle.close - 0.5 * candle.lower_shadow)
                    if lower_long
                    else candle.low
                )
            else:
                line2 = (
                    (candle.low + 0.5 * candle.lower_shadow)
                    if lower_long
                    else candle.low
                )

        return OrangeLines(upper=max(line1, line2), lower=min(line1, line2))


# ============================================================
# بخش ۴: محاسبه خطوط بنفش با افت به تایم‌فریم پایین‌تر
# ============================================================


class PurpleLineCalculator:

    LOWER_TF_MAP = {"monthly": "weekly", "weekly": "daily", "daily": "4h"}

    @staticmethod
    def find_purple_lines_recursive(
        multi_tf_data: Dict[str, List[Candle]],
        current_tf: str,
        orange: OrangeLines,
    ) -> List[PurpleLine]:
        candles = multi_tf_data.get(current_tf, [])
        if not candles:
            return []

        purple_candidates = []
        similar_count = 0

        for i in range(len(candles) - 2, -1, -1):
            if similar_count >= 5:
                break
            c = candles[i]
            exited_up = (c.high > orange.upper) and (c.open < orange.upper)
            exited_down = (c.low < orange.lower) and (c.open > orange.lower)

            if exited_up or exited_down:
                next_c = candles[i + 1] if i + 1 < len(candles) else None
                if not next_c:
                    continue

# بررسی ۴ مدل برگشت / دفع
                direction = "up" if exited_up else "down"
                if PurpleLineCalculator._check_condition_2(
                    c, next_c, orange, direction
                ):
                    price = c.high if exited_up else c.low
                    purple_candidates.append(
                        PurpleLine(
                            price=price,
                            is_above=exited_up,
                            candle_index=i,
                            timeframe=current_tf,
                        )
                    )
                    similar_count += 1

        # فیلتر و بررسی فاصله معتبر (بین ۰.۲ تا ۲.۰ برابر منطقه احتیاط)
        valid_lines = []
        zone_h = orange.height

        for p in purple_candidates:
            ref_price = orange.upper if p.is_above else orange.lower
            dist = abs(p.price - ref_price)
            if (0.20 * zone_h) <= dist <= (2.0 * zone_h):
                valid_lines.append(p)

        # اگر خط معتبری یافت نشد، ارجاع به تایم‌فریم پایین‌تر
        if not valid_lines and current_tf in PurpleLineCalculator.LOWER_TF_MAP:
            lower_tf = PurpleLineCalculator.LOWER_TF_MAP[current_tf]
            return PurpleLineCalculator.find_purple_lines_recursive(
                multi_tf_data, lower_tf, orange
            )

        return valid_lines

    @staticmethod
    def _check_condition_2(
        candle: Candle, next_candle: Candle, orange: OrangeLines, direction: str
    ) -> bool:
        # مدل ۱: برگشت در بدنه خودش
        if orange.lower <= candle.close <= orange.upper:
            return True
        # مدل ۲: دفع در سایه (سایه بلند)
        if (
            direction == "up"
            and candle.upper_shadow >= candle.body_size * 2
        ) or (
            direction == "down"
            and candle.lower_shadow >= candle.body_size * 2
        ):
            return True
        # مدل ۳: برگشت ۵۰٪ در بدنه مجاور
        if direction == "up" and next_candle.close < next_candle.open:
            if (candle.close - next_candle.close) >= 0.5 * candle.body_size:
                return True
        elif direction == "down" and next_candle.close > next_candle.open:
            if (next_candle.close - candle.close) >= 0.5 * candle.body_size:
                return True
        # مدل ۴: برگشت ۵۰٪ در سایه مجاور
        if (
            direction == "up"
            and (candle.close - next_candle.low) >= 0.5 * candle.body_size
        ):
            return True
        elif (
            direction == "down"
            and (next_candle.high - candle.close) >= 0.5 * candle.body_size
        ):
            return True

        return False


# ============================================================
# بخش ۵: رصد بازار و تعیین پویای مناطق ورود (مانیتورینگ)
# ============================================================


class MarketMonitor:

    @staticmethod
    def evaluate_monitoring(
        monitor_candles: List[Candle], orange: OrangeLines
    ) -> Dict:
        first_touched = None
        break_type = BreakType.NONE
        outside_closes = 0

        for c in monitor_candles:
            # تشخیص اولین تاچ
            if first_touched is None:
                if c.high >= orange.upper:
                    first_touched = "upper"
                elif c.low <= orange.lower:
                    first_touched = "lower"

            if c.close > orange.upper or c.close < orange.lower:
                outside_closes += 1

        if outside_closes >= 2:
            break_type = BreakType.COMPLETE
        elif first_touched is not None:
            break_type = BreakType.INITIAL

        # تعیین مناطق معاملاتی بر اساس جهت تاچ
        step = orange.height / 3.0
        div1 = orange.lower + step
        div2 = orange.lower + (2.0 * step)

if first_touched == "upper":  # الگوی صعودی
            near = (div2, orange.upper)
            middle = (div1, div2)
            far = (orange.lower, div1)
            pattern_dir = "صعودی"
        else:  # الگوی نزولی یا پیش‌فرض
            near = (orange.lower, div1)
            middle = (div1, div2)
            far = (div2, orange.upper)
            pattern_dir = "نزولی"

        zones = TradingZones(near_zone=near, middle_zone=middle, far_zone=far)

        return {
            "first_touched": first_touched,
            "break_type": break_type,
            "pattern_direction": pattern_dir,
            "zones": zones,
        }


# ============================================================
# بخش ۶: مدیریت ریسک و ماژول اتصال به متاتریدر ۵ (MT5)
# ============================================================


class RiskManager:

    MAX_PORTFOLIO_RISK = 0.40  # حداکثر ۴۰٪ درگیری کل سرمایه

    @staticmethod
    def validate_risk(
        current_used_margin: float,
        account_balance: float,
        new_trade_margin: float,
    ) -> bool:
        total_risk = (current_used_margin + new_trade_margin) / account_balance
        return total_risk <= RiskManager.MAX_PORTFOLIO_RISK


class MT5Executor:
    """ارتباط مستقیم با کارگزار از طریق MetaTrader 5"""

    def init(self):
        self.connected = False
        if MT5_AVAILABLE:
            if mt5.initialize():
                self.connected = True
                print("✅ اتصال به متاتریدر ۵ با موفقیت برقرار شد.")
            else:
                print("❌ خطا در اتصال به متاتریدر ۵.")

    def get_candles(
        self, symbol: str, timeframe_str: str, count: int = 100
    ) -> List[Candle]:
        if not self.connected:
            return []

        tf_mapping = {
            "monthly": mt5.TIMEFRAME_MN1,
            "weekly": mt5.TIMEFRAME_W1,
            "daily": mt5.TIMEFRAME_D1,
            "4h": mt5.TIMEFRAME_H4,
            "1h": mt5.TIMEFRAME_H1,
        }
        mt5_tf = tf_mapping.get(timeframe_str, mt5.TIMEFRAME_D1)
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)

        if rates is None or len(rates) == 0:
            return []

        candles = []
        for r in rates:
            dt = datetime.fromtimestamp(r["time"])
            candles.append(
                Candle(
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    volume=r["tick_volume"],
                    time=dt,
                )
            )
        return candles

    def send_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: float,
        sl: float,
        tp: float,
    ) -> bool:
        if not self.connected:
            print(f"[شبیه‌سازی] ثبت سفارش {order_type} برای {symbol} در قیمت {price}")
            return True

        action_type = (
            mt5.ORDER_TYPE_BUY_LIMIT
            if order_type == "BUY_LIMIT"
            else mt5.ORDER_TYPE_SELL_LIMIT
        )
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": action_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": "SupplyDemand_Robot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ خطا در ثبت سفارش: {result.comment}")
            return False
        print(f"✅ سفارش {order_type} با موفقیت در MT5 ثبت شد.")
        return True

    def close_all_positions_at_timeframe_end(self, symbol: str):

"""بستن اجباری تمام پوزیشن‌ها در انتهای تایم‌فریم انتخاب شده"""
        if not self.connected:
            return
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            for pos in positions:
                tick = mt5.symbol_info_tick(symbol)
                type_dict = (
                    mt5.ORDER_TYPE_SELL
                    if pos.type == mt5.ORDER_TYPE_BUY
                    else mt5.ORDER_TYPE_BUY
                )
                price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": pos.ticket,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": type_dict,
                    "price": price,
                    "deviation": 10,
                    "magic": 123456,
                    "comment": "Timeframe End Close",
                }
                mt5.order_send(request)
                print(f"🔒 معامله {pos.ticket} در انتهای تایم‌فریم بسته شد.")


# ============================================================
# بخش ۷: اجرای کامل تحلیل و مدیریت خروجی اکسل
# ============================================================


class StrategyController:

    def init(self, symbols: List[str]):
        self.symbols = symbols
        self.executor = MT5Executor()

    def run_analysis(self) -> pd.DataFrame:
        report_data = []

        for symbol in self.symbols:
            for tf in ["monthly", "weekly", "daily"]:
                multi_data = {
                    tf: self.executor.get_candles(symbol, tf, 100),
                    "weekly": self.executor.get_candles(symbol, "weekly", 100),
                    "daily": self.executor.get_candles(symbol, "daily", 100),
                    "4h": self.executor.get_candles(symbol, "4h", 100),
                    "1h": self.executor.get_candles(symbol, "1h", 100),
                }

                candles = multi_data[tf]
                if not candles or len(candles) < 2:
                    continue

                analysis_candle = candles[-1]
                size_cat, ratio = CandleSizeCalculator.calculate(candles, tf)
                orange = OrangeLineDrawer.draw(analysis_candle, size_cat, tf)

                # خطوط بنفش با افت به تایم‌فریم پایین‌تر
                purples = PurpleLineCalculator.find_purple_lines_recursive(
                    multi_data, tf, orange
                )

                # مانیتورینگ
                monitor_tf = {"monthly": "daily", "weekly": "4h", "daily": "1h"}[tf]
                monitor_candles = multi_data[monitor_tf]
                eval_res = MarketMonitor.evaluate_monitoring(
                    monitor_candles, orange
                )

                # تعیین حد سود و ضرر
                above_purples = [p for p in purples if p.is_above]
                below_purples = [p for p in purples if not p.is_above]

                sl = below_purples[0].price if below_purples else orange.lower
                tp1 = (
                    orange.upper
                    if eval_res["pattern_direction"] == "صعودی"
                    else orange.lower
                )
                tp2 = (
                    above_purples[0].price
                    if above_purples
                    else (orange.upper + orange.height)
                )

                report_data.append(
                    {
                        "نماد": symbol,
                        "تایم‌فریم": tf,
                        "اندازه کندل": size_cat.value,
                        "جهت الگوی مانیتور": eval_res["pattern_direction"],
                        "نوع شکست": eval_res["break_type"].value,
                        "خط نارنجی بالا": round(orange.upper, 5),
"خط نارنجی پایین": round(orange.lower, 5),
                        "ارتفاع احتیاط": round(orange.height, 5),
                        "ناحیه نزدیک": f"{round(eval_res['zones'].near_zone[0], 5)} - {round(eval_res['zones'].near_zone[1], 5)}",
                        "ناحیه میانی": f"{round(eval_res['zones'].middle_zone[0], 5)} - {round(eval_res['zones'].middle_zone[1], 5)}",
                        "ناحیه دور": f"{round(eval_res['zones'].far_zone[0], 5)} - {round(eval_res['zones'].far_zone[1], 5)}",
                        "حد سود ۱ (TP1)": round(tp1, 5),
                        "حد سود ۲ (TP2)": round(tp2, 5),
                        "حد ضرر (SL)": round(sl, 5),
                    }
                )

        df = pd.DataFrame(report_data)
        df.to_excel("Trading_Analysis_Report.xlsx", index=False)
        print("📄 فایل اکسل گزارش تحلیل با موفقیت ذخیره شد: Trading_Analysis_Report.xlsx")
        return df


# ============================================================
# نقطه ورود اصلی برنامه
# ============================================================

if name == "main":
    symbols_list = ["EURUSD", "GBPUSD", "USDJPY"]
    controller = StrategyController(symbols_list)
    report_df = controller.run_analysis()
    print(report_df.head())
pip install MetaTrader5 pandas openpyxl numpy
