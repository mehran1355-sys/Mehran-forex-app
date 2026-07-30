import flet as ft
import datetime
import random
import urllib.request
import json
import os
import traceback

# فراخوانی موتور استراتژی
try:
    from strategy_engine import SupplyDemandEngine
except ImportError:
    SupplyDemandEngine = None

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
                if "history" not in data:
                    data["history"] = []
                return data
    except Exception:
        pass
    return {"symbols": DEFAULT_SYMBOLS, "history": []}

def save_settings_to_file(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# ------------------------------------------------------------------
# دریافت داده‌های زنده yFinance
# ------------------------------------------------------------------
def fetch_live_ohlc(symbol: str, timeframe: str):
    tf_map = {
        "MN1": ("1mo", "10y"),
        "W1": ("1wk", "10y"),
        "D1": ("1d", "2y"),
    }
    interval, period = tf_map.get(timeframe, ("1d", "2y"))

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quote = result['indicators']['quote'][0]

                opens, highs, lows, closes = quote['open'], quote['high'], quote['low'], quote['close']

                clean_dates, clean_open, clean_high, clean_low, clean_close = [], [], [], [], []
                for i in range(len(timestamps)):
                    if closes[i] is not None and opens[i] is not None and highs[i] is not None and lows[i] is not None:
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

    # شبیه‌سازی داده در صورت عدم اتصال
    now = datetime.datetime.now()
    count = 120 if timeframe == "MN1" else (520 if timeframe == "W1" else 500)
    dates = [now - datetime.timedelta(days=i) for i in range(count)]
    dates.reverse()
    base_price = 2350.0 if "XAU" in symbol else 1.0800
    closes = [base_price + random.uniform(-20, 20) for _ in range(count)]
    return {
        'time': dates,
        'open': closes,
        'high': [c + 10 for c in closes],
        'low': [c - 10 for c in closes],
        'close': closes,
        'is_live': False
    }

# ------------------------------------------------------------------
# رابط کاربری Flet
# ------------------------------------------------------------------
def main(page: ft.Page):
    try:
        page.title = "Mehran Trader - روانشناسی عرضه و تقاضا"
        page.theme_mode = "dark"
        page.rtl = True
        page.padding = 12
        page.scroll = "auto"

        saved_data = load_settings()
        symbols_list = saved_data.get("symbols", DEFAULT_SYMBOLS)
        analysis_history = saved_data.get("history", [])

        saved_symbol = saved_data.get("saved_symbol", symbols_list[0]["code"] if symbols_list else "XAUUSD")
        saved_tf = saved_data.get("saved_tf", "D1")
        saved_token = saved_data.get("saved_token", "")
        saved_chat_id = saved_data.get("saved_chat_id", "")
        saved_risk = saved_data.get("saved_risk", "40")
        saved_auto_trade = saved_data.get("saved_auto_trade", False)

        # ------------------------------------------------------------------
        # عناصر منوی اصلی
        # ------------------------------------------------------------------
        symbol_dropdown = ft.Dropdown(
            label="انتخاب نماد معاملاتی",
            width=260,
            value=saved_symbol,
            options=[ft.dropdown.Option(item["code"], item["name"]) for item in symbols_list],
        )

        tf_dropdown = ft.Dropdown(
            label="تایم‌فریم تحلیل",
            width=160,
            value=saved_tf,
            options=[
                ft.dropdown.Option("MN1", "ماهانه (MN1)"),
                ft.dropdown.Option("W1", "هفتگی (W1)"),
                ft.dropdown.Option("D1", "روزانه (D1)"),
            ],
        )

        # ورودی‌های افزودن نماد جدید
        new_symbol_code = ft.TextField(label="کد نماد (مثلاً USDCHF)", width=180)
        new_symbol_name = ft.TextField(label="نام فارسی (مثلاً دلار/فرانک)", width=220)

        # ورودی‌های تنظیمات
        bot_token_input = ft.TextField(label="Bot Token تلگرام", value=saved_token, password=True, can_reveal_password=True, width=260)
        chat_id_input = ft.TextField(label="Chat ID تلگرام", value=saved_chat_id, width=150)
        risk_input = ft.TextField(label="سقف ریسک (%)", value=saved_risk, width=120)
        auto_trade_switch = ft.Switch(label="معامله خودکار", value=saved_auto_trade)

        log_box = ft.Text(value="سیستم آماده به کار است.\n", color="#81C784", size=12)
        log_container = ft.Container(
            content=ft.Column([log_box], scroll="auto"),
            bgcolor="#1A1A1A",
            border_radius=8,
            padding=10,
            height=120,
        )

        results_list_column = ft.Column([], spacing=10)
        history_list_column = ft.Column([], spacing=10)

        def write_log(message: str, is_error: bool = False):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix = "❌ " if is_error else "🔹 "
            log_box.value += f"[{timestamp}] {prefix}{message}\n"
            page.update()

        def save_state():
            saved_data["saved_symbol"] = symbol_dropdown.value
            saved_data["saved_tf"] = tf_dropdown.value
            saved_data["saved_token"] = bot_token_input.value.strip()
            saved_data["saved_chat_id"] = chat_id_input.value.strip()
            saved_data["saved_risk"] = risk_input.value.strip()
            saved_data["saved_auto_trade"] = auto_trade_switch.value
            saved_data["symbols"] = symbols_list
            saved_data["history"] = analysis_history
            save_settings_to_file(saved_data)

        # ------------------------------------------------------------------
        # افزودن نماد جدید
        # ------------------------------------------------------------------
        def add_new_symbol_action(e):
            code = new_symbol_code.value.strip().upper()
            name = new_symbol_name.value.strip()

            if not code or not name:
                write_log("لطفاً کد و نام نماد را وارد کنید.", is_error=True)
                return

            if any(s["code"] == code for s in symbols_list):
                write_log(f"نماد {code} قبلاً در لیست موجود است.", is_error=True)
                return

            new_item = {"code": code, "name": f"{name} ({code})"}
            symbols_list.append(new_item)
            
            # به‌روزرسانی منوی کشویی
            symbol_dropdown.options.append(ft.dropdown.Option(new_item["code"], new_item["name"]))
            symbol_dropdown.value = code
            
            new_symbol_code.value = ""
            new_symbol_name.value = ""
            
            save_state()
            write_log(f"✅ نماد جدید {code} با موفقیت اضافه و ذخیره شد.")
            page.update()

        # ------------------------------------------------------------------
        # ایجاد کارت نمایش تحلیل
        # ------------------------------------------------------------------
        def build_analysis_card(data_dict):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"📌 {data_dict['symbol']} [{data_dict['timeframe']}] ➔ مانیتورینگ: [{data_dict['monitoring_tf']}]", size=14, weight="bold", color="#FFD700"),
                        ft.Text(f"⏱ {data_dict['date_str']}", size=11, color="#B0BEC5"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"💰 آخرین قیمت: {data_dict['last_price']:.4f}", size=13, color="#64B5F6", weight="bold"),
                    ft.Text(f"🏷 دسته کندل تحلیلی: {data_dict['category']}", size=13, color="#FFFFFF"),
                    ft.Text(f"🟧 خط نارنجی بالا: {data_dict['top_orange']:.4f}", size=13, color="#FFA726"),
                    ft.Text(f"🟧 خط نارنجی پایین: {data_dict['bottom_orange']:.4f}", size=13, color="#FFA726"),
                    ft.Text(f"🟢 ۱/۳ نزدیک: {data_dict['near'][0]:.4f} تا {data_dict['near'][1]:.4f}", size=12, color="#81C784"),
                    ft.Text(f"🟡 ۱/۳ میانی: {data_dict['mid'][0]:.4f} تا {data_dict['mid'][1]:.4f}", size=12, color="#FFF176"),
                    ft.Text(f"🔴 ۱/۳ دور: {data_dict['far'][0]:.4f} تا {data_dict['far'][1]:.4f}", size=12, color="#E57373"),
                    ft.Text(f"🟪 حد سود دوم (TP2): {data_dict['purple_top']:.4f} (یافت‌شده: {data_dict.get('top_count', 0)})", size=13, color="#BA68C8"),
                    ft.Text(f"⛔ حد ضرر (SL): {data_dict['purple_bottom']:.4f} (یافت‌شده: {data_dict.get('bot_count', 0)})", size=13, color="#E57373"),
                ], spacing=5),
                bgcolor="#212121",
                padding=12,
                border_radius=8,
                border=ft.Border(
                    top=ft.BorderSide(1, "#424242"), bottom=ft.BorderSide(1, "#424242"),
                    left=ft.BorderSide(1, "#424242"), right=ft.BorderSide(1, "#424242")
                )
            )

        # بازنویسی کارت‌های تاریخچه
        def refresh_history_ui():
            history_list_column.controls.clear()
            if not analysis_history:
                history_list_column.controls.append(
                    ft.Text("هیچ تحلیلی در تاریخچه ثبت نشده است.", color="#757575", size=13)
                )
            else:
                for item in reversed(analysis_history):
                    history_list_column.controls.append(build_analysis_card(item))

        refresh_history_ui()

        # ------------------------------------------------------------------
        # اجرای تحلیل
        # ------------------------------------------------------------------
        def run_analysis_action(e):
            symbol = symbol_dropdown.value
            timeframe = tf_dropdown.value

            write_log(f"📡 در حال دریافت داده‌ها و تحلیل {symbol} [{timeframe}]...")

            current_df = fetch_live_ohlc(symbol, timeframe)
            last_price = current_df['close'][-1]

            if SupplyDemandEngine is not None:
                engine = SupplyDemandEngine(symbol, timeframe)
                orange_info = engine.calculate_orange_lines(current_df)
                zones = engine.calculate_zones(orange_info, touched_top_first=True)
                purples = engine.find_purple_lines(current_df, orange_info)
                monitoring_tf = engine.get_monitoring_timeframe()
            else:
                orange_info = {"category": "تستی", "top_orange": last_price*1.01, "bottom_orange": last_price*0.99}
                zones = {"near": (last_price*0.99, last_price*0.995), "mid": (last_price*0.995, last_price*1.0), "far": (last_price*1.0, last_price*1.01)}
                purples = {"purple_top": last_price*1.02, "purple_bottom": last_price*0.98, "top_found_count": 0, "bottom_found_count": 0}
                monitoring_tf = "H1"

            record = {
                "symbol": symbol,
                "timeframe": timeframe,
                "monitoring_tf": monitoring_tf,
                "date_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_price": last_price,
                "category": orange_info["category"],
                "top_orange": orange_info["top_orange"],
                "bottom_orange": orange_info["bottom_orange"],
                "near": zones["near"],
                "mid": zones["mid"],
                "far": zones["far"],
                "purple_top": purples["purple_top"],
                "purple_bottom": purples["purple_bottom"],
                "top_count": purples.get("top_found_count", 0),
                "bot_count": purples.get("bottom_found_count", 0),
            }

            # ذخیره در آرشیو
            analysis_history.append(record)
            save_state()

            # به روز رسانی لیست فعلی و تاریخچه
            results_list_column.controls.insert(0, build_analysis_card(record))
            refresh_history_ui()

            write_log(f"✅ تحلیل {symbol} ذخیره شد.")
            page.update()

        # ------------------------------------------------------------------
        # تب‌های برنامه
        # ------------------------------------------------------------------
        tab_main = ft.Tab(
            label="📈 تحلیل و سیگنال",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("۱. انتخاب یا افزودن نماد معاملاتی", size=14, weight="bold"),
                    ft.Row([symbol_dropdown, tf_dropdown], wrap=True),
                    
                    # بخش جدید افزودن نماد
                    ft.Container(
                        content=ft.Column([
                            ft.Text("➕ افزودن نماد جدید به لیست:", size=13, color="#FFB74D"),
                            ft.Row([new_symbol_code, new_symbol_name, ft.ElevatedButton("ثبت نماد", on_click=add_new_symbol_action)], wrap=True),
                        ]),
                        bgcolor="#1E1E1E", padding=10, border_radius=6
                    ),

                    ft.Divider(),
                    ft.Text("۲. تنظیمات مدیریت ریسک", size=14, weight="bold"),
                    ft.Row([risk_input, auto_trade_switch], wrap=True),
                    ft.Row([bot_token_input, chat_id_input], wrap=True),
                    ft.ElevatedButton("💾 ذخیره تنظیمات", on_click=lambda e: save_state()),

                    ft.Divider(),
                    ft.ElevatedButton("🔍 تحلیل و محاسبه زون‌ها", on_click=run_analysis_action, bgcolor="#2E7D32", color="#FFFFFF"),

                    ft.Divider(),
                    ft.Text("📊 نتیجه آخرین تحلیل:", size=15, weight="bold", color="#FFD700"),
                    results_list_column,

                    ft.Divider(),
                    ft.Text("📜 لاگ عملیات:", size=13, weight="bold"),
                    log_container,
                ], spacing=10),
                padding=10
            )
        )

        tab_history = ft.Tab(
            label="🗂 تاریخچه تحلیل‌ها",
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("📋 آرشیو تمام تحلیل‌های انجام‌شده:", size=15, weight="bold", color="#FFD700"),
                        ft.ElevatedButton("🧹 پاک‌سازی تاریخچه", on_click=lambda e: (analysis_history.clear(), save_state(), refresh_history_ui(), page.update()))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    history_list_column,
                ], spacing=10),
                padding=10
            )
        )

        tabs_control = ft.Tabs(selected_index=0, animation_duration=300, tabs=[tab_main, tab_history], expand=True)

        page.add(
            ft.Text("Mehran Trader - مدیریت عرضه و تقاضا", size=18, weight="bold", color="#FFD700"),
            tabs_control
        )

    except Exception:
        err_msg = traceback.format_exc()
        page.clean()
        page.add(
            ft.Text("⚠️ خطایی در اجرا رخ داده است:", color="#FF5252", size=15, weight="bold"),
            ft.Text(err_msg, color="#FFFFFF", size=11, selectable=True)
        )
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
