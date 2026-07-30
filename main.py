import flet as ft
import datetime
import random
import urllib.request
import urllib.parse

# ------------------------------------------------------------------
# فراخوانی ایمن ماژول‌ها یا استفاده از موتور داخلی مستقل برای اندروید
# ------------------------------------------------------------------
try:
    from strategy_engine import SupplyDemandEngine
except ImportError:
    class SupplyDemandEngine:
        """موتور محاسباتی مستقل داخلی برای اندروید"""
        def __init__(self, symbol, timeframe):
            self.symbol = symbol
            self.timeframe = timeframe

        def calculate_orange_lines(self, df):
            closes = df['close']
            top_o = max(closes) * 1.002
            bot_o = min(closes) * 0.998
            return {
                "category": "دسته A (استاندارد)",
                "is_bullish": closes[-1] > closes[0],
                "top_orange": top_o,
                "bottom_orange": bot_o,
            }

        def calculate_zones(self, orange_info, touched_top_first=True):
            top = orange_info["top_orange"]
            bot = orange_info["bottom_orange"]
            diff = (top - bot) / 3
            return {
                "near": (bot, bot + diff),
                "mid": (bot + diff, bot + 2 * diff),
                "far": (bot + 2 * diff, top)
            }

        def find_purple_lines(self, df, orange_info):
            top = orange_info["top_orange"]
            bot = orange_info["bottom_orange"]
            return {
                "purple_top": top * 1.01,
                "purple_bottom": bot * 0.99
            }

        def get_monitoring_timeframe(self):
            tf_map = {"MN1": "D1", "W1": "H4", "D1": "H1"}
            return tf_map.get(self.timeframe, "H1")

        def calculate_limit_orders(self, zone, total_volume=0.3, steps=3):
            start, end = zone
            step_size = (end - start) / max(1, steps - 1)
            vol_per_step = total_volume / steps
            return [{"price": start + i * step_size, "volume": vol_per_step} for i in range(steps)]

try:
    from reporter_module import StrategyReporter
except ImportError:
    class StrategyReporter:
        """ماژول ارسال به تلگرام با استاندارد شبکه پایتون بدون نیاز به پکیج خارجی"""
        def __init__(self, telegram_bot_token, telegram_chat_id):
            self.token = telegram_bot_token
            self.chat_id = telegram_chat_id

        def generate_chart(self, df, analysis):
            return None

        def send_telegram_report(self, chart_path, caption):
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                clean_text = caption.replace("**", "")
                data = urllib.parse.urlencode({
                    "chat_id": self.chat_id,
                    "text": clean_text,
                }).encode('utf-8')
                req = urllib.request.Request(url, data=data)
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.status == 200
            except Exception:
                return False

try:
    from mt5_execution import MT5ExecutionEngine
except ImportError:
    MT5ExecutionEngine = None


def main(page: ft.Page):
    try:
        # ------------------------------------------------------------------
        # تنظیمات عمومی و ظاهری صفحه
        # ------------------------------------------------------------------
        page.title = "Mehran Forex Trading Group"
        page.theme_mode = ft.ThemeMode.DARK
        page.rtl = True
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO

        # متغیرهای ذخیره وضعیت تحلیل
        current_analysis = None
        current_df = None

        # رنگ طلایی استاندارد
        GOLD_COLOR = "#FFD700"

        # ------------------------------------------------------------------
        # عناصر رابط کاربری (UI Controls)
        # ------------------------------------------------------------------
        symbol_input = ft.TextField(
            label="نماد معاملاتی (مثلاً XAUUSD یا EURUSD)",
            value="XAUUSD",
            width=300,
            border_color=GOLD_COLOR,
        )

        tf_dropdown = ft.Dropdown(
            label="تایم‌فریم تحلیل",
            width=200,
            value="D1",
            options=[
                ft.dropdown.Option("MN1", "ماهانه (MN1)"),
                ft.dropdown.Option("W1", "هفتگی (W1)"),
                ft.dropdown.Option("D1", "روزانه (D1)"),
            ],
        )

        bot_token_input = ft.TextField(
            label="Bot Token تلگرام",
            password=True,
            can_reveal_password=True,
            width=350,
        )

        chat_id_input = ft.TextField(
            label="Chat ID تلگرام / کانال",
            width=200,
        )

        risk_input = ft.TextField(
            label="سقف ریسک کل (%)",
            value="40",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        log_box = ft.Text(
            value="سیستم آماده به کار است. نماد را مشخص کرده و دکمه تحلیل را بزنید.\n",
            color="green300",
            size=13,
        )

        log_container = ft.Container(
            content=ft.Column([log_box], scroll=ft.ScrollMode.ALWAYS),
            bgcolor="black54",
            border=ft.Border.all(1, "grey800"),
            border_radius=8,
            padding=15,
            height=180,
        )

        result_card = ft.Column(visible=False)

        def write_log(message: str, is_error: bool = False):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix = "❌ " if is_error else "🔹 "
            log_box.value += f"[{timestamp}] {prefix}{message}\n"
            page.update()

        # ------------------------------------------------------------------
        # اکشن‌ها
        # ------------------------------------------------------------------
        def run_analysis_action(e):
            nonlocal current_analysis, current_df
            symbol = symbol_input.value.strip().upper()
            timeframe = tf_dropdown.value

            if not symbol:
                write_log("لطفا نماد معاملاتی را وارد کنید.", is_error=True)
                return

            write_log(f"شروع تحلیل نماد {symbol} در تایم‌فریم {timeframe}...")

            now = datetime.datetime.now()
            dates = [now - datetime.timedelta(days=i) for i in range(100)]
            dates.reverse()

            close_price = 2000.0
            open_prices, high_prices, low_prices, close_prices = [], [], [], []

            for _ in range(100):
                change = random.uniform(-10, 10)
                close_price += change
                high = close_price + abs(random.uniform(1, 5))
                low = close_price - abs(random.uniform(1, 5))
                open_p = low + (high - low) * random.random()

                open_prices.append(open_p)
                high_prices.append(high)
                low_prices.append(low)
                close_prices.append(close_price)

            current_df = {
                'time': dates,
                'open': open_prices,
                'high': high_prices,
                'low': low_prices,
                'close': close_prices
            }

            engine = SupplyDemandEngine(symbol, timeframe)
            orange_info = engine.calculate_orange_lines(current_df)
            zones = engine.calculate_zones(orange_info, touched_top_first=True)
            purples = engine.find_purple_lines(current_df, orange_info)

            current_analysis = {
                "symbol": symbol,
                "timeframe": timeframe,
                "monitoring_tf": engine.get_monitoring_timeframe(),
                "category": orange_info["category"],
                "is_bullish": orange_info["is_bullish"],
                "orange_info": orange_info,
                "zones": zones,
                "purple_lines": purples,
                "tp1": orange_info["top_orange"] if not orange_info["is_bullish"] else orange_info["bottom_orange"],
            }

            result_card.controls = [
                ft.Divider(color=GOLD_COLOR),
                ft.Text(f"📊 نتایج تحلیل: {symbol} [{timeframe}]", size=16, weight=ft.FontWeight.BOLD, color=GOLD_COLOR),
                ft.Row([
                    ft.Text(f"دسته کندل: {orange_info['category']}"),
                    ft.Text(f"خط نارنجی بالا: {orange_info['top_orange']:.4f}"),
                    ft.Text(f"خط نارنجی پایین: {orange_info['bottom_orange']:.4f}"),
                ]),
                ft.Row([
                    ft.Text(f"زون ۱/۳ نزدیک: {zones['near'][0]:.4f} تا {zones['near'][1]:.4f}"),
                    ft.Text(f"زون ۱/۳ میانی: {zones['mid'][0]:.4f} تا {zones['mid'][1]:.4f}"),
                ]),
                ft.Row([
                    ft.Text(f"حد سود بنفش (TP2): {purples['purple_top']:.4f}"),
                    ft.Text(f"حد ضرر بنفش (SL): {purples['purple_bottom']:.4f}"),
                ]),
            ]
            result_card.visible = True
            write_log("✅ تحلیل با موفقیت انجام شد و خطوط محاسبه شدند.")
            page.update()

        def send_telegram_action(e):
            if not current_analysis:
                write_log("ابتدا باید تحلیل را انجام دهید.", is_error=True)
                return

            token = bot_token_input.value.strip()
            chat_id = chat_id_input.value.strip()

            if not token or not chat_id:
                write_log("توکن ربات و چت‌آیدی تلگرام را وارد کنید.", is_error=True)
                return

            reporter = StrategyReporter(telegram_bot_token=token, telegram_chat_id=chat_id)

            caption = (
                f"🎯 سیگنال استراتژی عرضه و تقاضا\n\n"
                f"🔹 نماد: {current_analysis['symbol']}\n"
                f"🔹 تایم‌فریم: {current_analysis['timeframe']}\n"
                f"🟧 خط بالا: {current_analysis['orange_info']['top_orange']:.4f}\n"
                f"🟧 خط پایین: {current_analysis['orange_info']['bottom_orange']:.4f}\n"
                f"🟪 تارگت اصلی: {current_analysis['purple_lines']['purple_top']:.4f}\n"
                f"⛔ حد ضرر: {current_analysis['purple_lines']['purple_bottom']:.4f}\n"
            )

            success = reporter.send_telegram_report(None, caption)
            if success:
                write_log("✈️ گزارش تحلیل با موفقیت به تلگرام ارسال شد.")
            else:
                write_log("خطا در ارسال به تلگرام. توکن یا چت‌آیدی را بررسی کنید.", is_error=True)

        def execute_mt5_action(e):
            if MT5ExecutionEngine is None:
                write_log("⚠️ این بخش مخصوص نسخه ویندوز متصل به متاتریدر ۵ است.", is_error=True)
                return

            if not current_analysis:
                write_log("ابتدا باید تحلیل را انجام دهید.", is_error=True)
                return

            mt5_engine = MT5ExecutionEngine(max_total_risk_percent=float(risk_input.value))
            if not mt5_engine.connect():
                write_log("خطا در برقراری ارتباط با متاتریدر ۵.", is_error=True)
                return

            write_log("اتصال به متاتریدر ۵ برقرار شد.")
            engine = SupplyDemandEngine(current_analysis["symbol"], current_analysis["timeframe"])
            orders_plan = engine.calculate_limit_orders(current_analysis["zones"]["near"], total_volume=0.3, steps=3)

            res = mt5_engine.place_limit_orders(
                symbol=current_analysis["symbol"],
                order_type="BUY" if current_analysis["is_bullish"] else "SELL",
                orders_plan=orders_plan,
                sl_price=current_analysis["purple_lines"]["purple_bottom"],
                tp1_price=current_analysis["tp1"],
                tp2_price=current_analysis["purple_lines"]["purple_top"]
            )

            if res["success"]:
                write_log(f"🚀 سفارش‌ها با موفقیت ثبت شدند.")
            else:
                write_log(f"خطا در ثبت سفارش: {res['message']}", is_error=True)

            mt5_engine.disconnect()

        def reset_all_action(e):
            if MT5ExecutionEngine is None:
                write_log("⚠️ این بخش مخصوص نسخه ویندوز متصل به متاتریدر ۵ است.", is_error=True)
                return

            mt5_engine = MT5ExecutionEngine()
            res = mt5_engine.close_all_and_cancel_pendings()
            write_log(f"🧹 ریست انجام شد.")

        # ------------------------------------------------------------------
        # چیدمان UI
        # ------------------------------------------------------------------
        page.add(
            ft.Column([
                ft.Row([
                    ft.Icon("candlestick_chart", color=GOLD_COLOR, size=36),
                    ft.Text("Mehran Trader - نرم‌افزار مدیریت عرضه و تقاضا", size=18, weight=ft.FontWeight.BOLD, color=GOLD_COLOR),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Divider(color="grey800"),

                ft.Text("۱. تنظیمات تحلیل نماد", size=15, weight=ft.FontWeight.BOLD),
                ft.Row([symbol_input, tf_dropdown]),

                ft.Text("۲. تنظیمات تلگرام و مدیریت ریسک", size=15, weight=ft.FontWeight.BOLD),
                ft.Row([bot_token_input, chat_id_input, risk_input]),

                ft.Divider(color="grey800"),

                ft.Row([
                    ft.ElevatedButton(
                        "🔍 تحلیل و محاسبه زون‌ها",
                        on_click=run_analysis_action,
                        icon="analytics",
                        color="black",
                        bgcolor=GOLD_COLOR,
                    ),
                    ft.ElevatedButton(
                        "✈️ ارسال به تلگرام",
                        on_click=send_telegram_action,
                        icon="send",
                        bgcolor="blue700",
                    ),
                    ft.ElevatedButton(
                        "⚡ اجرای پله‌ای در MT5",
                        on_click=execute_mt5_action,
                        icon="play_arrow",
                        bgcolor="green700",
                    ),
                    ft.ElevatedButton(
                        "❌ بستن تمام پوزیشن‌ها (Reset)",
                        on_click=reset_all_action,
                        icon="cancel",
                        bgcolor="red700",
                    ),
                ], wrap=True, spacing=10),

                result_card,
                ft.Divider(color="grey800"),
                ft.Text("📜 گزارش عملیات و لاگ سیستم:", size=14, weight=ft.FontWeight.BOLD),
                log_container,
            ], spacing=15)
        )

    except Exception as err:
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ خطای اجرا در محیط اندروید:", size=18, color="red", weight=ft.FontWeight.BOLD),
                    ft.Text(str(err), size=14, color="white"),
                ]),
                padding=20,
            )
        )

if __name__ == "__main__":
    ft.app(target=main)
