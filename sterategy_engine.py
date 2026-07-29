import pandas as pd
import numpy as np

class SupplyDemandEngine:
    """
    موتور محاسباتی استراتژی روانشناسی عرضه و تقاضا
    طراحی شده برای تایم‌فریم‌های ماهانه (MN1)، هفتگی (W1) و روزانه (D1)
    """

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe.upper()  # MN1, W1, D1
        
    def get_lookback_count(self) -> int:
        """تعیین تعداد کندل‌های دوره ارزیابی بر اساس تایم‌فریم تحلیل"""
        if self.timeframe == "MN1":
            return 12
        elif self.timeframe == "W1":
            return 24
        elif self.timeframe == "D1":
            return 30
        return 30

    def get_monitoring_timeframe(self) -> str:
        """تعیین تایم‌فریم مانیتورینگ (دو تایم‌فریم پایین‌تر)"""
        mapping = {
            "MN1": "D1",
            "W1": "H4",
            "D1": "H1"
        }
        return mapping.get(self.timeframe, "H1")

    # ------------------------------------------------------------------
    # ۱. دسته‌بندی اندازه کندل و سنجش سایه‌ها
    # ------------------------------------------------------------------
    def classify_candle_size(self, df: pd.DataFrame) -> dict:
        """
        محاسبه نسبت بدنه کندل تحلیلی به میانگین ۲ کندل بزرگ دوره اخیر
        و دسته‌بندی آن به ۴ گروه: خیلی بلند، بلند، کوچک، خیلی کوچک
        """
        lookback = self.get_lookback_count()
        recent_df = df.tail(lookback).copy()
        
        recent_df['body'] = (recent_df['close'] - recent_df['open']).abs()
        
        # پیدا کردن دو کندل با بزرگ‌ترین بدنه در دوره
        sorted_bodies = recent_df['body'].sort_values(ascending=False).values
        if len(sorted_bodies) >= 2:
            top2_avg = (sorted_bodies[0] + sorted_bodies[1]) / 2.0
        else:
            top2_avg = sorted_bodies[0] if len(sorted_bodies) > 0 else 1.0

        last_candle = recent_df.iloc[-1]
        last_body = last_candle['body']
        
        ratio = last_body / top2_avg if top2_avg > 0 else 0.0

        if ratio >= 0.6:
            category = "VERY_LONG"
        elif 0.4 <= ratio < 0.6:
            category = "LONG"
        elif 0.1 <= ratio < 0.4:
            category = "SHORT"
        else:
            category = "VERY_SHORT"

        return {
            "category": category,
            "ratio": ratio,
            "candle": last_candle,
            "top2_avg": top2_avg
        }

    def is_shadow_long(self, shadow_len: float, body_len: float, category: str) -> bool:
        """بررسی بلند بودن سایه طبق قوانین تایم‌فریم و نوع کندل"""
        effective_body = body_len if body_len > 0 else 0.00001

        if self.timeframe in ["MN1", "W1"]:
            if category in ["VERY_LONG", "LONG"]:
                return shadow_len >= effective_body
            else:  # SHORT, VERY_SHORT
                return shadow_len >= (2.0 * effective_body)
        else:  # D1
            if category in ["VERY_LONG", "LONG"]:
                return shadow_len >= (1.5 * effective_body)
            else:  # SHORT, VERY_SHORT
                return shadow_len >= (2.5 * effective_body)

    # ------------------------------------------------------------------
    # ۲. رسم خطوط نارنجی و تعیین منطقه احتیاط
    # ------------------------------------------------------------------
    def calculate_orange_lines(self, df: pd.DataFrame) -> dict:
        """محاسبه دقیق خطوط نارنجی و مرزهای منطقه احتیاط"""
        classification = self.classify_candle_size(df)
        category = classification["category"]
        candle = classification["candle"]

        open_p = float(candle['open'])
        close_p = float(candle['close'])
        high_p = float(candle['high'])
        low_p = float(candle['low'])

        body_len = abs(close_p - open_p)
        up_shadow = high_p - max(open_p, close_p)
        low_shadow = min(open_p, close_p) - low_p
        is_bullish = close_p >= open_p

        up_shadow_long = self.is_shadow_long(up_shadow, body_len, category)
        low_shadow_long = self.is_shadow_long(low_shadow, body_len, category)

        orange1 = 0.0
        orange2 = 0.0

        if is_bullish:
            if category == "VERY_LONG":
                orange1 = close_p - (0.25 * body_len)
                orange2 = (high_p - 0.5 * up_shadow) if up_shadow_long else high_p
            elif category == "LONG":
                orange1 = close_p - (0.50 * body_len)
                orange2 = (high_p - 0.5 * up_shadow) if up_shadow_long else high_p
            else:  # SHORT / VERY_SHORT
                orange1 = (high_p - 0.5 * up_shadow) if up_shadow_long else high_p
                orange2 = (low_p + 0.5 * low_shadow) if low_shadow_long else low_p
        else:  # کندل نزولی
            if category == "VERY_LONG":
                orange1 = close_p + (0.25 * body_len)
                orange2 = (low_p + 0.5 * low_shadow) if low_shadow_long else low_p
            elif category == "LONG":
                orange1 = close_p + (0.50 * body_len)
                orange2 = (low_p + 0.5 * low_shadow) if low_shadow_long else low_p
            else:  # SHORT / VERY_SHORT
                orange1 = (high_p - 0.5 * up_shadow) if up_shadow_long else high_p
                orange2 = (low_p + 0.5 * low_shadow) if low_shadow_long else low_p

        top_orange = max(orange1, orange2)
        bottom_orange = min(orange1, orange2)
        caution_width = top_orange - bottom_orange

        return {
            "category": category,
            "is_bullish": is_bullish,
            "top_orange": top_orange,
            "bottom_orange": bottom_orange,
            "caution_width": caution_width,
            "zone_step": caution_width / 3.0
        }

    # ------------------------------------------------------------------
    # ۳. تقسیم‌بندی نواحی سه‌گانه (نزدیک، میانی، دور)
    # ------------------------------------------------------------------
    def calculate_zones(self, orange_info: dict, touched_top_first: bool) -> dict:
        """تقسیم منطقه احتیاط به ۳ بخش مساوی بر اساس خط تاچ شده اولیه"""
        top_o = orange_info["top_orange"]
        bot_o = orange_info["bottom_orange"]
        step = orange_info["zone_step"]

        if touched_top_first:
            # تاچ خط بالا: نزدیک بالا، میانی وسط، دور پایین
            near_zone = (top_o - step, top_o)
            mid_zone = (top_o - 2 * step, top_o - step)
            far_zone = (bot_o, top_o - 2 * step)
        else:
            # تاچ خط پایین: نزدیک پایین، میانی وسط، دور بالا
            near_zone = (bot_o, bot_o + step)
            mid_zone = (bot_o + step, bot_o + 2 * step)
            far_zone = (bot_o + 2 * step, top_o)

        return {
            "near": near_zone,
            "mid": mid_zone,
            "far": far_zone
        }

    # ------------------------------------------------------------------
    # ۴. تعیین خطوط بنفش (حد سود و حد ضرر) + قانون ۲۵٪ جایگزین
    # ------------------------------------------------------------------
    def find_purple_lines(self, df: pd.DataFrame, orange_info: dict) -> dict:
        """
        بررسی ۵ کندل واجد شرایط قبلی طبق مدل‌های ۴گانه برگشت
        و اعمال شرط فاصله ۲۰٪ تا ۲۰۰٪ یا جایگزینی ۲۵٪ عرض منطقه احتیاط
        """
        top_orange = orange_info["top_orange"]
        bot_orange = orange_info["bottom_orange"]
        caution_width = orange_info["caution_width"]

        # محدوده‌های مجاز فاصله خط بنفش تا خط نارنجی
        min_distance = 0.20 * caution_width
        max_distance = 2.00 * caution_width

        valid_purple_above = []
        valid_purple_below = []

        # بررسی تاریخی کندل‌ها از قبل از کندل تحلیلی
        candles = df.iloc[:-1].iloc[::-1]  # حرکت به سمت گذشته
        count = 0

        for idx in range(len(candles)):
            if count >= 5:
                break

            curr = candles.iloc[idx]
            high_p, low_p = float(curr['high']), float(curr['low'])
            open_p, close_p = float(curr['open']), float(curr['close'])

            # شرط اول: خارج شدن از محدوده احتیاط
            condition_1 = (high_p > top_orange and open_p < top_orange) or \
                          (low_p < bot_orange and open_p > bot_orange)

            if not condition_1:
                continue

            # شرط دوم: چک کردن مدل‌های برگشت ۴گانه
            has_reversal = False
            
            # مدل اول: برگشت در بدنه خود (ورود/خروج با سایه، کلوز درون محدوده)
            if (open_p >= bot_orange and open_p <= top_orange) and \
               (close_p >= bot_orange and close_p <= top_orange):
                has_reversal = True

            # مدل سوم و چهارم: نیازمند کندل مجاور (راستی)
            elif idx > 0:
                prev_in_time = candles.iloc[idx - 1]  # کندل سمت راست
                prev_close = float(prev_in_time['close'])
                prev_body = abs(prev_close - float(prev_in_time['open']))
                curr_body = abs(close_p - open_p)

                # برگشت ۵۰٪ بدنه یا سایه کندل مجاور
                if prev_body >= 0.5 * curr_body:
                    has_reversal = True

            if has_reversal:
                count += 1
                if high_p > top_orange:
                    dist = high_p - top_orange
                    if min_distance <= dist <= max_distance:
                        valid_purple_above.append(high_p)
                if low_p < bot_orange:
                    dist = bot_orange - low_p
                    if min_distance <= dist <= max_distance:
                        valid_purple_below.append(low_p)

        # انتخاب نزدیک‌ترین خط بنفش معتبر به خطوط نارنجی
        purple_top = min(valid_purple_above, key=lambda x: x - top_orange) if valid_purple_above else None
        purple_bottom = max(valid_purple_below, key=lambda x: bot_orange - x) if valid_purple_below else None

        # اعمال قانون جایگزین (Fallback 25%) در صورت عدم یافتن خط بنفش معتبر
        if purple_top is None:
            purple_top = top_orange + (0.25 * caution_width)
            
        if purple_bottom is None:
            purple_bottom = bot_orange - (0.25 * caution_width)

        return {
            "purple_top": purple_top,
            "purple_bottom": purple_bottom
        }

    # ------------------------------------------------------------------
    # ۵. قیمت‌گذاری سفارش‌های لیمیت (Limit Orders)
    # ------------------------------------------------------------------
    def calculate_limit_orders(self, zone_tuple: tuple, total_volume: float, steps: int = 3) -> list:
        """
        محاسبه قیمت سفارشات پله‌ای:
        سفارش اول دقیقاً روی مرز ورود ناحیه و مابقی متوازن در عمق ناحیه
        """
        start_p, end_p = zone_tuple
        prices = np.linspace(start_p, end_p, steps)
        vol_per_step = total_volume / steps

        orders = []
        for idx, price in enumerate(prices):
            orders.append({
                "step": idx + 1,
                "price": round(float(price), 5),
                "volume": round(vol_per_step, 2)
            })
        return orders
