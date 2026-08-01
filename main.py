import flet as ft
import datetime
import json
import os
import traceback
import requests
import socket

SETTINGS_FILE = "mehran_trader_settings.json"


def discover_server(port=8000):
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        base = ".".join(local_ip.split(".")[:-1])

        for i in range(1, 255):
            test_ip = f"{base}.{i}"
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                result = sock.connect_ex((test_ip, port))
                sock.close()

                if result == 0:
                    print(f"Server found at: {test_ip}:{port}")
                    return f"http://{test_ip}:{port}"
            except:
                pass

        return None
    except Exception as e:
        print("Discovery Error:", e)
        return None


API_URL = discover_server()

if API_URL is None:
    print("❌ سرور پیدا نشد. لطفاً مطمئن شوید سرور روشن است.")
else:
    print("✅ سرور پیدا شد:", API_URL)


def analyze_from_server(symbol, timeframe):
    if API_URL is None:
        return None
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"symbol": symbol, "timeframe": timeframe},
            timeout=10,
        )
        return response.json()
    except Exception as e:
        print("Server Error:", e)
        return None


def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "symbols" not in data:
                    data["symbols"] = []
                if "history" not in data:
                    data["history"] = []
                return data
    except Exception:
        pass
    return {"symbols": [], "history": []}


def save_settings_to_file(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def main(page: ft.Page):
    try:
        page.title = "Mehran Trader - MT5"
        page.theme_mode = "dark"
        page.rtl = True
        page.padding = 12
        page.scroll = "auto"

        saved_data = load_settings()
        symbols_list = saved_data.get("symbols", [])
        analysis_history = saved_data.get("history", [])

        saved_symbol = saved_data.get("saved_symbol", symbols_list[0]["code"] if symbols_list else "")
        saved_tf = saved_data.get("saved_tf", "D1")
        saved_token = saved_data.get("saved_token", "")
        saved_chat_id = saved_data.get("saved_chat_id", "")
        saved_risk = saved_data.get("saved_risk", "40")
        saved_auto_trade = saved_data.get("saved_auto_trade", False)

        symbol_dropdown = ft.Dropdown(
            label="انتخاب نماد معاملاتی",
            width=260,
            value=saved_symbol if saved_symbol else None,
            options=[
                ft.dropdown.Option(item["code"], item["name"]) for item in symbols_list
            ],
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

        new_symbol_code = ft.TextField(label="کد نماد (مثلاً EURUSD)", width=180)
        new_symbol_name = ft.TextField(label="نام فارسی (مثلاً یورو/دلار)", width=220)

        bot_token_input = ft.TextField(
            label="Bot Token تلگرام",
            value=saved_token,
            password=True,
            can_reveal_password=True,
            width=260,
        )
        chat_id_input = ft.TextField(
            label="Chat ID تلگرام",
            value=saved_chat_id,
            width=150,
        )
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

        def add_new_symbol_action(e):
            code = new_symbol_code.value.strip().upper()
            name = new_symbol_name.value.strip()

            if not code or not name:
                write_log("⚠️ کد و نام نماد را وارد کنید.", is_error=True)
                return

            new_item = {"code": code, "name": f"{name} ({code})"}
            symbols_list.append(new_item)

            symbol_dropdown.options.append(
                ft.dropdown.Option(new_item["code"], new_item["name"])
            )
            symbol_dropdown.value = code

            new_symbol_code.value = ""
            new_symbol_name.value = ""

            save_state()
            write_log(f"✅ نماد {code} با موفقیت اضافه شد.")
            page.update()

        def remove_symbol_action(e):
            code = symbol_dropdown.value
            if not code:
                write_log("⚠️ نمادی برای حذف انتخاب نشده است.", is_error=True)
                return

            symbols_list[:] = [s for s in symbols_list if s["code"] != code]
            symbol_dropdown.options[:] = [
                ft.dropdown.Option(s["code"], s["name"]) for s in symbols_list
            ]
            symbol_dropdown.value = symbols_list[0]["code"] if symbols_list else None

            save_state()
            write_log(f"🗑 نماد {code} حذف شد.")
            page.update()

        def build_analysis_card(data_dict):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    f"📌 {data_dict['symbol']} [{data_dict['timeframe']}] ➔ مانیتورینگ: [{data_dict['monitoring_tf']}]",
                                    size=14,
                                    weight="bold",
                                    color="#FFD700",
                                ),
                                ft.Text(
                                    f"⏱ {data_dict['date_str']}",
                                    size=11,
                                    color="#B0BEC5",
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(
                            f"💰 آخرین قیمت: {data_dict['last_price']:.5f}",
                            size=13,
                            color="#64B5F6",
                            weight="bold",
                        ),
                        ft.Text(
                            f"🏷 دسته کندل تحلیلی: {data_dict['category']}",
                            size=13,
                            color="#FFFFFF",
                        ),
                        ft.Text(
                            f"🟧 خط نارنجی بالا: {data_dict['top_orange']:.5f}",
                            size=13,
                            color="#FFA726",
                        ),
                        ft.Text(
                            f"🟧 خط نارنجی پایین: {data_dict['bottom_orange']:.5f}",
                            size=13,
                            color="#FFA726",
                        ),
                        ft.Text(
                            f"🟢 ۱/۳ نزدیک: {data_dict['near'][0]:.5f} تا {data_dict['near'][1]:.5f}",
                            size=12,
                            color="#81C784",
                        ),
                        ft.Text(
                            f"🟡 ۱/۳ میانی: {data_dict['mid'][0]:.5f} تا {data_dict['mid'][1]:.5f}",
                            size=12,
                            color="#FFF176",
                        ),
                        ft.Text(
                            f"🔴 ۱/۳ دور: {data_dict['far'][0]:.5f} تا {data_dict['far'][1]:.5f}",
                            size=12,
                            color="#E57373",
                        ),
                        ft.Text(
                            f"🟪 حد سود دوم (TP2): {data_dict['purple_top']:.5f}",
                            size=13,
                            color="#BA68C8",
                        ),
                        ft.Text(
                            f"⛔ حد ضرر (SL): {data_dict['purple_bottom']:.5f}",
                            size=13,
                            color="#E57373",
                        ),
                        ft.Text(
                            f"📉 نوع شکست: {data_dict['breakout_type']}",
                            size=12,
                            color="#90CAF9",
                        ),
                    ],
                    spacing=5,
                ),
                bgcolor="#212121",
                padding=12,
                border_radius=8,
            )

        def refresh_history_ui():
            history_list_column.controls.clear()
            if not analysis_history:
                history_list_column.controls.append(
                    ft.Text(
                        "هیچ تحلیلی در تاریخچه ثبت نشده است.",
                        color="#757575",
                        size=13,
                    )
                )
            else:
                for item in reversed(analysis_history):
                    history_list_column.controls.append(build_analysis_card(item))

        refresh_history_ui()

        def run_analysis_action(e):
            symbol = symbol_dropdown.value
            timeframe = tf_dropdown.value

            if not symbol:
                write_log("⚠️ ابتدا یک نماد انتخاب کنید.", is_error=True)
                return

            if API_URL is None:
                write_log("❌ سرور پیدا نشد. لطفاً مطمئن شوید سرور روشن است.", is_error=True)
                return

            write_log(f"📡 در حال ارسال درخواست تحلیل به سرور...")

            result = analyze_from_server(symbol, timeframe)

            if result is None:
                write_log("❌ ارتباط با سرور برقرار نشد.", is_error=True)
                return

            record = result
            analysis_history.append(record)
            save_state()

            results_list_column.controls.insert(0, build_analysis_card(record))
            refresh_history_ui()

            write_log(f"✅ تحلیل {symbol} ذخیره شد.")
            page.update()

        main_tab_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("۱. انتخاب یا افزودن نماد معاملاتی", size=14, weight="bold"),
                    ft.Row(
                        [
                            symbol_dropdown,
                            tf_dropdown,
                            ft.ElevatedButton("🗑 حذف نماد انتخاب‌شده", on_click=remove_symbol_action),
                        ],
                        wrap=True,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("➕ افزودن نماد جدید به لیست:", size=13, color="#FFB74D"),
                                ft.Row(
                                    [
                                        new_symbol_code,
                                        new_symbol_name,
                                        ft.ElevatedButton("ثبت نماد", on_click=add_new_symbol_action),
                                    ],
                                    wrap=True,
                                ),
                            ]
                        ),
                        bgcolor="#1E1E1E",
                        padding=10,
                        border_radius=6,
                    ),
                    ft.Divider(),
                    ft.Text("۲. تنظیمات مدیریت ریسک و تلگرام", size=14, weight="bold"),
                    ft.Row([risk_input, auto_trade_switch], wrap=True),
                    ft.Row([bot_token_input, chat_id_input], wrap=True),
                    ft.ElevatedButton("💾 ذخیره تنظیمات", on_click=lambda e: save_state()),
                    ft.Divider(),
                    ft.ElevatedButton(
                        "🔍 تحلیل و محاسبه زون‌ها",
                        on_click=run_analysis_action,
                        bgcolor="#2E7D32",
                        color="#FFFFFF",
                    ),
                    ft.Divider(),
                    ft.Text("📊 نتیجه آخرین تحلیل:", size=15, weight="bold", color="#FFD700"),
                    results_list_column,
                    ft.Divider(),
                    ft.Text("📜 لاگ عملیات:", size=13, weight="bold"),
                    log_container,
                ],
                spacing=10,
            ),
            padding=10,
        )

        history_tab_content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "📋 آرشیو تمام تحلیل‌های انجام‌شده:",
                                size=15,
                                weight="bold",
                                color="#FFD700",
                            ),
                            ft.ElevatedButton(
                                "🧹 پاک‌سازی تاریخچه",
                                on_click=lambda e: (
                                    analysis_history.clear(),
                                    save_state(),
                                    refresh_history_ui(),
                                    page.update(),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    history_list_column,
                ],
                spacing=10,
            ),
            padding=10,
        )

        tabs = [
            ft.Tab(label=ft.Text("📈 تحلیل و سیگنال")),
            ft.Tab(label=ft.Text("🗂 تاریخچه تحلیل‌ها")),
        ]

        tabs_control = ft.Tabs(
            selected_index=0,
            length=2,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(tabs=tabs),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            main_tab_content,
                            history_tab_content,
                        ],
                    ),
                ],
            ),
        )

        page.add(
            ft.Text(
                "Mehran Trader - MT5 Supply/Demand",
                size=18,
                weight="bold",
                color="#FFD700",
            ),
            tabs_control,
        )

    except Exception:
        err_msg = traceback.format_exc()
        page.clean()
        page.add(
            ft.Text(
                "⚠️ خطایی در اجرا رخ داده است:",
                color="#FF5252",
                size=15,
                weight="bold",
            ),
            ft.Text(
                err_msg,
                color="#FFFFFF",
                size=11,
                selectable=True,
            ),
        )
        page.update()


if __name__ == "__main__":
    ft.app(target=main)
