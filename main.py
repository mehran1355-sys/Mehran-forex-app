import flet as ft
import datetime
import urllib.request
import urllib.parse
import json
import os
import traceback

# ------------------------------------------------------------------
# سیستم مدیریت فایل تنظیمات بومی پایتون
# ------------------------------------------------------------------
SETTINGS_FILE = "mehran_trader_settings.json"

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_settings_to_file(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return True
    except Exception:
        return False

# ------------------------------------------------------------------
# دریافت داده‌های زنده بازار از API اختصاصی با urllib
# ------------------------------------------------------------------
def fetch_live_ohlc(symbol: str, timeframe: str):
    """
    دریافت کندل‌های واقعی بازار بدون نیاز به کتابخانه‌های سنگین جانبی
    """
    # نگاشت تایم‌فریم‌ها به استانداردهای سرویس داده
    tf_map = {
        "MN1": ("1mo", "5y"),
        "W1": ("1wk", "2y"),
        "D1": ("1d", "1y"),
    }
    interval, period = tf_map.get(timeframe, ("1d", "1y"))

    # تنظیم تبدیل نمادها (مثلا XAUUSD به XAUUSD=X)
    formatted_symbol = symbol.strip().upper()
    if formatted_symbol == "XAUUSD":
        formatted_symbol = "XAUUSD=X"
    elif not formatted_symbol.endswith("=X") and len(formatted_symbol) == 6:
        formatted_symbol = f"{formatted_symbol}=X"

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_symbol}?interval={interval}&range={period}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise Exception(f"خطا در دریافت داده: کد status {response.status}")
        
        data = json.loads(response.read().decode('utf-8'))
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]

        opens = quote['open']
        highs = quote['high']
        lows = quote['low']
        closes = quote['close']

        # حذف داده‌های خالی (None)
        clean_dates, clean_open, clean_high, clean_low, clean_close = [], [], [], [], []
        for i in range(len(timestamps)):
            if closes[i] is not None and opens[i] is not None:
                clean_dates.append(datetime.datetime.fromtimestamp(timestamps[i]))
                clean_open.append(opens[i])
                clean_high.append(highs[i])
                clean_low.append(lows[i])
                clean_close.append(closes[i])

        if not clean_close:
            raise Exception("داده‌های معتبری برای این نماد یافت نشد.")

        return {
            'time': clean_dates,
            'open': clean_open,
            'high': clean_high,
            'low': clean_low,
            'close': clean_close
        }

# ------------------------------------------------------------------
# فراخوانی ایمن ماژول‌ها یا استفاده از موتور داخلی مستقل برای اندروید
# ------------------------------------------------------------------
try:
    from strategy_engine import SupplyDemandEngine
except ImportError:
    class SupplyDemandEngine:
        def __init__(self, symbol, timeframe):
            self.symbol = symbol
            self.timeframe = timeframe

        def calculate_orange_lines(self, df):
            closes = df['close']
            top_o = max(closes[-20:]) * 1.002
            bot_o = min(closes[-20:]) * 0.998
            return {
                "category": "دسته A (استاندارد)",
                "is_bullish": closes[-1] > closes[-2],
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
        def __init__(self, telegram_bot_token, telegram_chat_id):
            self.token = telegram_bot_token
            self.chat_id = telegram_chat_id

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
        # تنظیمات عمومی و ظاهری صفحه
        page.title = "Mehran Forex Trading Group"
        page.theme_mode = "dark"
        page.rtl = True
        page.padding = 15
        page.scroll = "auto"

        current_analysis = None
        current_df = None

        # ------------------------------------------------------------------
        # بازیابی تنظیمات از فایل متنی
        # ------------------------------------------------------------------
        saved_data = load_settings()
        saved_symbol = saved_data.get("saved_symbol", "XAUUSD")
        saved_tf = saved_data.get("saved_tf", "D1")
        saved_token = saved_data.get("saved_token", "")
        saved_chat_id = saved_data.get("saved_chat_id", "")
        saved_risk = saved_data.get("saved_risk", "40")

        # ------------------------------------------------------------------
        # عناصر ورودی
        # ------------------------------------------------------------------
        symbol_input = ft.TextField(
            label="نماد معاملاتی (مثلاً XAUUSD)",
            value=saved_symbol,
            width=280,
        )

        tf_dropdown = ft.Dropdown(
            label="تایم‌فریم",
            width=180,
            value=saved_tf,
            options=[
                ft.dropdown.Option("MN1", "ماهانه (MN1)"),
                ft.dropdown.Option("W1", "هفتگی (W1)"),
                ft.dropdown.Option("D1", "روزانه (D1)"),
            ],
        )

        bot_token_input = ft.TextField(
            label="Bot Token تلگرام",
            value=saved_token,
            password=True,
            can_reveal_password=True,
            width=320,
        )

        chat_id_input = ft.TextField(
            label="Chat ID تلگرام",
            value=saved_chat_id,
            width=180,
        )

        risk_input = ft.TextField(
            label="سقف ریسک کل (%)",
            value=saved_risk,
            width=140,
        )

        log_box = ft.Text(
            value="سیستم آماده به کار است.\n",
            color="#81C784",
            size=12,
        )

        log_container = ft.Container(
            content=ft.Column([log_box], scroll="auto"),
            bgcolor="#1A1A1A",
            border_radius=8,
            padding=12,
            height=160,
        )

        result_card = ft.Column(visible=False)

        def write_log(message: str, is_error: bool = False):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix = "❌ " if is_error else "🔹 "
            log_box.value += f"[{timestamp}] {prefix}{message}\n"
            page.update()

        # ------------------------------------------------------------------
        # ذخیره‌سازی تنظیمات در فایل JSON
        # ------------------------------------------------------------------
        def save_settings_action(e):
            new_data = {
                "saved_symbol": symbol_input.value.strip().upper(),
                "saved_tf": tf_dropdown.value,
                "saved_token": bot_token_input.value.strip(),
                "saved_chat_id": chat_id_input.value.strip(),
                "saved_risk": risk_input.value.strip()
            }
            success = save_settings_to_file(new_data)
            if success:
                write_log("💾 تنظیمات با موفقیت در سیستم ذخیره شدند.")
            else:
                write_log("⚠️ خطا در ذخیره‌سازی اطلاعات روی حافظه گوشی.", is_error=True)

        def run_analysis_action(e):
            nonlocal current_analysis, current_df
            symbol = symbol_input.value.strip().upper()
            timeframe = tf_dropdown.value

            if not symbol:
                write_log("لطفا نماد معاملاتی را وارد کنید.", is_error=True)
                return

            write_log(f"📡 در حال دریافت کندل‌های واقعی {symbol} از اینترنت...")

            try:
                # دریافت قیمت‌های واقعی زنده
                current_df = fetch_live_ohlc(symbol, timeframe)
                last_price = current_df['close'][-1]
                write_log(f"✅ داده‌های زنده دریافت شد. قیمت آخرین کندل: {last_price:.2f}")

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
                    ft.Divider(),
                    ft.Text(f"📊 نتایج تحلیل واقعی: {symbol} [{timeframe}]", size=16, weight="bold", color="#FFD700"),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"💰 آخرین قیمت بازار:  {last_price:.4f}", size=13, color="#64B5F6", weight="bold"),
                            ft.Text(f"📌 دسته کندل:  {orange_info['category']}", size=13, color="#FFFFFF"),
                            ft.Text(f"🟧 خط نارنجی بالا:  {orange_info['top_orange']:.4f}", size=13, color="#FFA726"),
                            ft.Text(f"🟧 خط نارنجی پایین:  {orange_info['bottom_orange']:.4f}", size=13, color="#FFA726"),
                            ft.Text(f"🟢 زون ۱/۳ نزدیک:  {zones['near'][0]:.4f}  تا  {zones['near'][1]:.4f}", size=13, color="#81C784"),
                            ft.Text(f"🟡 زون ۱/۳ میانی:  {zones['mid'][0]:.4f}  تا  {zones['mid'][1]:.4f}", size=13, color="#FFF176"),
                            ft.Text(f"🟪 تارگت بنفش (TP2):  {purples['purple_top']:.4f}", size=13, color="#BA68C8"),
                            ft.Text(f"⛔ حد ضرر بنفش (SL):  {purples['purple_bottom']:.4f}", size=13, color="#E57373"),
                        ], spacing=8),
                        bgcolor="#212121",
                        padding=14,
                        border_radius=8,
                    )
                ]
                result_card.visible = True
                write_log("✅ محاسبات زون‌ها بر اساس کندل‌های زنده انجام شد.")

            except Exception as err:
                write_log(f"خطا در دریافت قیمت‌های زنده: {str(err)}", is_error=True)

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
                f"🎯 سیگنال استراتژی عرضه و تقاضا (داده زنده)\n\n"
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
                write_log("خطا در برقراری ارتباط با نرم‌افزار متاتریدر ۵ ویندوز.", is_error=True)
                return

            write_log("اتصال به متاتریدر ۵ برقرار شد. در حال محاسبه و ارسال سفارش‌های لیمیت...")
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
                write_log(f"🚀 تعداد {res['placed_count']} سفارش لیمیت پله‌ای با موفقیت روی متاتریدر ۵ ثبت شد.")
            else:
                write_log(f"خطا در ثبت سفارش: {res['message']}", is_error=True)

            mt5_engine.disconnect()

        def reset_all_action(e):
            if MT5ExecutionEngine is None:
                write_log("⚠️ این بخش مخصوص نسخه ویندوز متصل به متاتریدر ۵ است.", is_error=True)
                return

            mt5_engine = MT5ExecutionEngine()
            res = mt5_engine.close_all_and_cancel_pendings()
            write_log(f"🧹 ریست کامل انجام شد: {res['closed_positions']} پوزیشن بسته و {res['cancelled_orders']} سفارش معلق لغو شدند.")

        # چیدمان اصلی UI
        page.add(
            ft.Column([
                ft.Text("Mehran Trader - مدیریت عرضه و تقاضا", size=18, weight="bold", color="#FFD700"),
                ft.Divider(),

                ft.Text("۱. تنظیمات تحلیل نماد", size=14, weight="bold"),
                ft.Row([symbol_input, tf_dropdown], wrap=True),

                ft.Text("۲. تنظیمات تلگرام و مدیریت ریسک", size=14, weight="bold"),
                ft.Row([bot_token_input, chat_id_input, risk_input], wrap=True),
                ft.ElevatedButton("💾 ذخیره تنظیمات", on_click=save_settings_action),

                ft.Divider(),

                ft.Row([
                    ft.ElevatedButton("🔍 تحلیل و محاسبه زون‌ها", on_click=run_analysis_action),
                    ft.ElevatedButton("✈️ ارسال به تلگرام", on_click=send_telegram_action),
                    ft.ElevatedButton("⚡ اجرای پله‌ای در MT5", on_click=execute_mt5_action),
                    ft.ElevatedButton("❌ بستن تمام پوزیشن‌ها", on_click=reset_all_action),
                ], wrap=True, spacing=10),

                result_card,
                ft.Divider(),
                ft.Text("📜 گزارش عملیات و لاگ سیستم:", size=13, weight="bold"),
                log_container,
            ], spacing=12)
        )

    except Exception:
        err_msg = traceback.format_exc()
        page.clean()
        page.add(
            ft.Text("⚠️ خطایی در بارگذاری برنامه رخ داده است:", color="#FF5252", size=15, weight="bold"),
            ft.Text(err_msg, color="#FFFFFF", size=11, selectable=True)
        )
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
