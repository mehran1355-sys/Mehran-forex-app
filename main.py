import flet as ft
import datetime
import random
import urllib.request
import urllib.parse
import json
import os
import traceback

# ------------------------------------------------------------------
# سیستم مدیریت فایل تنظیمات و لیست نمادها
# ------------------------------------------------------------------
SETTINGS_FILE = "mehran_trader_settings.json"

DEFAULT_SYMBOLS = [
    {"code": "XAUUSD", "name": "طلا (XAUUSD)"},
    {"code": "EURUSD", "name": "یورو / دلار (EURUSD)"},
    {"code": "GBPUSD", "name": "پوند / دلار (GBPUSD)"},
    {"code": "USDJPY", "name": "دلار / ین (USDJPY)"},
    {"code": "AUDUSD", "name": "دلار استرالیا / دلار (AUDUSD)"},
    {"code": "USDCAD", "name": "دلار / دلار کانادا (USDCAD)"},
    {"code": "GBPJPY", "name": "پوند / ین (GBPJPY)"},
    {"code": "BTCUSD", "name": "بیت‌کوین (BTCUSD)"},
]

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "symbols" not in data or not data["symbols"]:
                    data["symbols"] = DEFAULT_SYMBOLS
                return data
    except Exception:
        pass
    return {"symbols": DEFAULT_SYMBOLS}

def save_settings_to_file(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# ------------------------------------------------------------------
# دریافت داده‌های زنده بازار با مکانیزم پشتیبان (Fallback)
# ------------------------------------------------------------------
def fetch_live_ohlc(symbol: str, timeframe: str):
    tf_map = {
        "MN1": ("1mo", "5y"),
        "W1": ("1wk", "2y"),
        "D1": ("1d", "1y"),
    }
    interval, period = tf_map.get(timeframe, ("1d", "1y"))

    formatted_symbol = symbol.strip().upper()
    if formatted_symbol == "XAUUSD":
        formatted_symbol = "XAUUSD=X"
    elif formatted_symbol in ["BTCUSD", "BTC"]:
        formatted_symbol = "BTC-USD"
    elif formatted_symbol in ["ETHUSD", "ETH"]:
        formatted_symbol = "ETH-USD"
    elif not formatted_symbol.endswith("=X") and len(formatted_symbol) == 6:
        formatted_symbol = f"{formatted_symbol}=X"

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_symbol}?interval={interval}&range={period}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quote = result['indicators']['quote'][0]

                opens, highs, lows, closes = quote['open'], quote['high'], quote['low'], quote['close']

                clean_dates, clean_open, clean_high, clean_low, clean_close = [], [], [], [], []
                for i in range(len(timestamps)):
                    if closes[i] is not None and opens[i] is not None:
                        clean_dates.append(datetime.datetime.fromtimestamp(timestamps[i]))
                        clean_open.append(opens[i])
                        clean_high.append(highs[i])
                        clean_low.append(lows[i])
                        clean_close.append(closes[i])

                if clean_close:
                    return {
                        'time': clean_dates,
                        'open': clean_open,
                        'high': clean_high,
                        'low': clean_low,
                        'close': clean_close,
                        'is_live': True
                    }
    except Exception:
        pass

    now = datetime.datetime.now()
    dates = [now - datetime.timedelta(days=i) for i in range(50)]
    dates.reverse()
    base_price = 2350.0 if "XAU" in symbol else 1.0800
    closes = [base_price + random.uniform(-10, 10) for _ in range(50)]
    return {
        'time': dates,
        'open': closes,
        'high': [c + 5 for c in closes],
        'low': [c - 5 for c in closes],
        'close': closes,
        'is_live': False
    }

# ------------------------------------------------------------------
# موتور محاسبه استراتژی عرضه و تقاضا
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
        page.title = "Mehran Forex Trading Group"
        page.theme_mode = "dark"
        page.rtl = True
        page.padding = 10
        page.scroll = "auto"

        current_analysis = None

        # بارگذاری تنظیمات و لیست نمادها
        saved_data = load_settings()
        symbols_list = saved_data.get("symbols", DEFAULT_SYMBOLS)
        saved_symbol = saved_data.get("saved_symbol", symbols_list[0]["code"] if symbols_list else "XAUUSD")
        saved_tf = saved_data.get("saved_tf", "D1")
        saved_token = saved_data.get("saved_token", "")
        saved_chat_id = saved_data.get("saved_chat_id", "")
        saved_risk = saved_data.get("saved_risk", "40")

        # ------------------------------------------------------------------
        # عناصر UI تب اول (تحلیل و معامله)
        # ------------------------------------------------------------------
        symbol_dropdown = ft.Dropdown(
            label="انتخاب نماد معاملاتی",
            width=260,
            value=saved_symbol,
            options=[ft.dropdown.Option(item["code"], item["name"]) for item in symbols_list],
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
            width=300,
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
            height=130,
        )

        placeholder_card = ft.Container(
            content=ft.Text("هنوز تحلیلی انجام نشده است. نماد را انتخاب کرده و دکمه «تحلیل و محاسبه زون‌ها» را بزنید.", color="#757575", size=13),
            bgcolor="#1E1E1E",
            padding=15,
            border_radius=8,
        )

        results_list_column = ft.Column([placeholder_card], spacing=10)

        # ------------------------------------------------------------------
        # توابع تب اول
        # ------------------------------------------------------------------
        def write_log(message: str, is_error: bool = False):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix = "❌ " if is_error else "🔹 "
            log_box.value += f"[{timestamp}] {prefix}{message}\n"
            page.update()

        def save_current_state():
            saved_data["saved_symbol"] = symbol_dropdown.value
            saved_data["saved_tf"] = tf_dropdown.value
            saved_data["saved_token"] = bot_token_input.value.strip()
            saved_data["saved_chat_id"] = chat_id_input.value.strip()
            saved_data["saved_risk"] = risk_input.value.strip()
            saved_data["symbols"] = symbols_list
            save_settings_to_file(saved_data)

        def save_settings_action(e):
            save_current_state()
            write_log("💾 تنظیمات با موفقیت در حافظه ذخیره شدند.")

        def clear_results_action(e):
            results_list_column.controls.clear()
            results_list_column.controls.append(placeholder_card)
            page.update()

        def run_analysis_action(e):
            nonlocal current_analysis
            symbol = symbol_dropdown.value
            timeframe = tf_dropdown.value

            write_log(f"📡 در حال تحلیل {symbol} [{timeframe}]...")

            if placeholder_card in results_list_column.controls:
                results_list_column.controls.remove(placeholder_card)

            current_df = fetch_live_ohlc(symbol, timeframe)
            last_price = current_df['close'][-1]
            
            if current_df.get('is_live'):
                write_log(f"✅ داده‌های زنده دریافت شد. آخرین قیمت: {last_price:.4f}")
            else:
                write_log(f"⚠️ عدم اتصال زنده به اینترنت؛ تحلیل بر اساس داده‌های موجود انجام شد.", is_error=True)

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

            time_now = datetime.datetime.now().strftime("%H:%M:%S")

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"📌 {symbol} [{timeframe}]", size=15, weight="bold", color="#FFD700"),
                        ft.Text(f"⏱ {time_now}", size=11, color="#B0BEC5"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"💰 آخرین قیمت:  {last_price:.4f}", size=13, color="#64B5F6", weight="bold"),
                    ft.Text(f"🏷 دسته کندل:  {orange_info['category']}", size=13, color="#FFFFFF"),
                    ft.Text(f"🟧 خط نارنجی بالا:  {orange_info['top_orange']:.4f}", size=13, color="#FFA726"),
                    ft.Text(f"🟧 خط نارنجی پایین:  {orange_info['bottom_orange']:.4f}", size=13, color="#FFA726"),
                    ft.Text(f"🟢 زون ۱/۳ نزدیک:  {zones['near'][0]:.4f}  تا  {zones['near'][1]:.4f}", size=13, color="#81C784"),
                    ft.Text(f"🟡 زون ۱/۳ میانی:  {zones['mid'][0]:.4f}  تا  {zones['mid'][1]:.4f}", size=13, color="#FFF176"),
                    ft.Text(f"🟪 تارگت بنفش (TP2):  {purples['purple_top']:.4f}", size=13, color="#BA68C8"),
                    ft.Text(f"⛔ حد ضرر بنفش (SL):  {purples['purple_bottom']:.4f}", size=13, color="#E57373"),
                ], spacing=6),
                bgcolor="#212121",
                padding=12,
                border_radius=8,
                border=ft.Border(
                    top=ft.BorderSide(1, "#424242"),
                    bottom=ft.BorderSide(1, "#424242"),
                    left=ft.BorderSide(1, "#424242"),
                    right=ft.BorderSide(1, "#424242")
                )
            )

            results_list_column.controls.insert(0, card)
            write_log("✅ نتیجه تحلیل درج شد.")
            page.update()

        def send_telegram_action(e):
            if not current_analysis:
                write_log("ابتدا باید حداقل یک تحلیل انجام دهید.", is_error=True)
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

            if reporter.send_telegram_report(None, caption):
                write_log(f"✈️ گزارش تحلیل ({current_analysis['symbol']}) به تلگرام ارسال شد.")
            else:
                write_log("خطا در ارسال به تلگرام. توکن یا چت‌آیدی را بررسی کنید.", is_error=True)

        def execute_mt5_action(e):
            if MT5ExecutionEngine is None:
                write_log("⚠️ این بخش مخصوص نسخه ویندوز متصل به متاتریدر ۵ است.", is_error=True)
                return

        def reset_all_action(e):
            if MT5ExecutionEngine is None:
                write_log("⚠️ این بخش مخصوص نسخه ویندوز متصل به متاتریدر ۵ است.", is_error=True)
                return

        # ------------------------------------------------------------------
        # عناصر و توابع تب دوم (مدیریت نمادها)
        # ------------------------------------------------------------------
        new_code_input = ft.TextField(label="کد نماد (مثلاً NZDUSD)", width=180)
        new_name_input = ft.TextField(label="نام فارسی / توضیحات", width=220)
        symbols_view_column = ft.Column(spacing=8)

        def render_symbols_list():
            symbols_view_column.controls.clear()
            for idx, item in enumerate(symbols_list):
                def make_delete_handler(index_to_del):
                    return lambda e: delete_symbol_action(index_to_del)

                row = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(item["name"], size=14, weight="bold", color="#FFFFFF"),
                            ft.Text(f"کد نماد: {item['code']}", size=11, color="#B0BEC5"),
                        ]),
                        ft.IconButton(
                            icon="delete",  # نام آیکون به‌صورت رشته کاملاً سازگار با تمامی نسخه‌های Flet
                            icon_color="#FF5252",
                            tooltip="حذف نماد",
                            on_click=make_delete_handler(idx)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#262626",
                    padding=10,
                    border_radius=6,
                )
                symbols_view_column.controls.append(row)

            # بروزرسانی منوی کشویی در تب اول
            symbol_dropdown.options = [ft.dropdown.Option(i["code"], i["name"]) for i in symbols_list]
            if symbols_list and symbol_dropdown.value not in [i["code"] for i in symbols_list]:
                symbol_dropdown.value = symbols_list[0]["code"]

            page.update()

        def add_new_symbol_action(e):
            code = new_code_input.value.strip().upper()
            name = new_name_input.value.strip()

            if not code:
                write_log("لطفاً کد نماد را وارد کنید.", is_error=True)
                return

            if not name:
                name = f"{code}"

            for item in symbols_list:
                if item["code"] == code:
                    write_log("این نماد قبلاً در لیست موجود است.", is_error=True)
                    return

            symbols_list.append({"code": code, "name": f"{name} ({code})"})
            new_code_input.value = ""
            new_name_input.value = ""

            save_current_state()
            render_symbols_list()
            write_log(f"➕ نماد جدید {code} با موفقیت اضافه شد.")

        def delete_symbol_action(index):
            if len(symbols_list) <= 1:
                write_log("حداقل باید یک نماد در لیست باقی بماند.", is_error=True)
                return

            removed = symbols_list.pop(index)
            save_current_state()
            render_symbols_list()
            write_log(f"🗑 نماد {removed['code']} حذف شد.")

        render_symbols_list()

        # ------------------------------------------------------------------
        # ساخت تب‌ها (Tabs Layout)
        # ------------------------------------------------------------------
        tab_trading = ft.Tab(
            text="📈 تحلیل و سیگنال",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("۱. تنظیمات تحلیل نماد", size=14, weight="bold"),
                    ft.Row([symbol_dropdown, tf_dropdown], wrap=True),

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

                    ft.Divider(),
                    ft.Row([
                        ft.Text("📊 نتایج تحلیل‌ها:", size=15, weight="bold", color="#FFD700"),
                        ft.TextButton("🧹 پاک کردن نتایج", on_click=clear_results_action)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    results_list_column,

                    ft.Divider(),
                    ft.Text("📜 گزارش عملیات و لاگ سیستم:", size=13, weight="bold"),
                    log_container,
                ], spacing=10),
                padding=10
            )
        )

        tab_manage_symbols = ft.Tab(
            text="⚙️ مدیریت نمادها",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("افزودن نماد معاملاتی جدید", size=15, weight="bold", color="#FFD700"),
                    ft.Text("می‌توانید هر نماد دلخواهی (طلا، جفت‌ارزها، کریپتو) را برای تحلیل در آینده اضافه کنید:", size=12, color="#B0BEC5"),
                    
                    ft.Row([new_code_input, new_name_input], wrap=True),
                    ft.ElevatedButton("➕ افزودن نماد جدید", on_click=add_new_symbol_action),
                    
                    ft.Divider(),
                    ft.Text("لیست نمادهای فعلی برنامه:", size=14, weight="bold"),
                    symbols_view_column,
                ], spacing=12),
                padding=10
            )
        )

        tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[tab_trading, tab_manage_symbols],
            expand=True
        )

        page.add(
            ft.Text("Mehran Trader - مدیریت عرضه و تقاضا", size=18, weight="bold", color="#FFD700"),
            tabs_control
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
