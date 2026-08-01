import flet as ft
import datetime
import random
import urllib.request
import json
import os
import traceback
import requests

from strategy_engine import SupplyDemandEngine

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

def send_telegram_message(token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        r = requests.post(url, json=payload)
        return r.status_code == 200
    except Exception as e:
        print("Telegram Error:", e)
        return False

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

def fetch_live_ohlc(symbol: str, timeframe: str):
    tf_map = {"MN1": ("1mo", "10y"), "W1": ("1wk", "10y"), "D1": ("1d", "2y")}
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
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                result = data["chart"]["result"][0]
                timestamps = result["timestamp"]
                quote = result["indicators"]["quote"][0]

                opens, highs, lows, closes = (
                    quote["open"],
                    quote["high"],
                    quote["low"],
                    quote["close"],
                )

                clean_dates, clean_open, clean_high, clean_low, clean_close = [], [], [], [], []
                for i in range(len(timestamps)):
                    if (
                        closes[i] is not None
                        and opens[i] is not None
                        and highs[i] is not None
                        and lows[i] is not None
                    ):
                        clean_dates.append(datetime.datetime.fromtimestamp(timestamps[i]))
                        clean_open.append(opens[i])
                        clean_high.append(highs[i])
                        clean_low.append(lows[i])
                        clean_close.append(closes[i])

                if clean_close:
                    return {
                        "time": clean_dates,
                        "open": clean_open,
                        "high": clean_high,
                        "low": clean_low,
                        "close": clean_close,
                        "is_live": True,
                    }
    except Exception:
        pass

    now = datetime.datetime.now()
    count = 120 if timeframe == "MN1" else (520 if timeframe == "W1" else 500)
    dates = [now - datetime.timedelta(days=i) for i in range(count)]
    dates.reverse()
    base_price = 2350.0 if "XAU" in symbol else 1.0800
    closes = [base_price + random.uniform(-20, 20) for _ in range(count)]
    return {
        "time": dates,
        "open": closes,
        "high": [c + 10 for c in closes],
        "low": [c - 10 for c in closes],
        "close": closes,
        "is_live": False,
    }

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

        saved_symbol = saved_data.get("saved_symbol", symbols_list[0]["code"])
        saved_tf = saved_data.get("saved_tf", "D1")
        saved_token = saved_data.get("saved_token", "")
        saved_chat_id = saved_data.get("saved_chat_id", "")
        saved_risk = saved_data.get("saved_risk", "40")
        saved_auto_trade = saved_data.get("saved_auto_trade", False)

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

        new_symbol_code = ft.TextField(label="کد نماد", width=180)
        new_symbol_name = ft.TextField(label="نام فارسی", width=220)

        bot_token_input = ft.TextField(label="Bot Token تلگرام", value=saved_token, password=True, can_reveal_password=True, width=260)
        chat_id_input = ft.TextField(label="Chat ID تلگرام", value=saved_chat_id, width=150)
        risk_input = ft.TextField(label="سقف ریسک (%)", value=saved_risk, width=120)
        auto_trade_switch = ft.Switch(label="معامله خودکار", value=saved_auto_trade)

        log_box = ft.Text(value="سیستم آماده به کار است.\n", color="#81C784", size=12)
        log_container = ft.Container(content=ft.Column([log_box], scroll="auto"), bgcolor="#1A1A1A", border_radius=8, padding=10, height=120)

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

        def add_new_symbol_action(e):
            code = new_symbol_code.value.strip().upper()
            name = new_symbol_name.value.strip()

            if not code or not name:
                write_log("لطفاً کد و نام نماد را وارد کنید.", is_error=True)
                return

            if any(s["code"] == code for s in symbols_list):
                write_log(f"نماد {code} قبلاً موجود است.", is_error=True)
                return

            new_item = {"code": code, "name": f"{name} ({code})"}
            symbols_list.append(new_item)
            symbol_dropdown.options.append(ft.dropdown.Option(new_item["code"], new_item["name"]))
            symbol_dropdown.value = code

            new_symbol_code.value = ""
            new_symbol_name.value = ""

            save_state()
            write_log(f"نماد جدید {code} اضافه شد.")
            page.update()

        def build_analysis_card(data_dict):
