import flet as ft
import datetime
import random

# فراخوانی ماژول‌های اختصاصی پروژه
from strategy_engine import SupplyDemandEngine
from reporter_module import StrategyReporter

# فراخوانی مشروط متاتریدر جهت جلوگیری از خطا در اندروید
try:
    from mt5_execution import MT5ExecutionEngine
except ImportError:
    MT5ExecutionEngine = None


def main(page: ft.Page):
    # ------------------------------------------------------------------
    # تنظیمات عمومی و ظاهری صفحه
    # ------------------------------------------------------------------
    page.title = "Mehran Forex Trading Group - روانشناسی عرضه و تقاضا"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # متغیرهای ذخیره وضعیت تحلیل
    current_analysis = None
    current_df = None

    # ------------------------------------------------------------------
    # عناصر رابط کاربری (UI Controls)
    # ------------------------------------------------------------------
    # ۱. بخش ورودی نماد و تایم‌فریم
    symbol_input = ft.TextField(
        label="نماد معاملاتی (مثلاً XAUUSD یا EURUSD)",
        value="XAUUSD",
        width=300,
        border_color=ft.colors.GOLD,
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

    # ۲. بخش تنظیمات تلگرام و مدیریت ریسک
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

    # ۳. باکس نمایش لاگ و خروجی‌ها
    log_box = ft.Text(
        value="سیستم آماده به کار است. نماد را مشخص کرده و دکمه تحلیل را بزنید.\n",
        color=ft.colors.GREEN_300,
        size=13,
    )

    log_container = ft.Container(
        content=ft.Column([log_box], scroll=ft.ScrollMode.ALWAYS),
        bgcolor=ft.colors.BLACK54,
        border=ft.border.all(1, ft.colors.GREY_800),
        border_radius=8,
        padding=15,
        height=180,
    )

    # کارت‌های نمایش نتایج تحلیل
    result_card = ft.Column(visible=False)

    def write_log(message: str, is_error: bool = False):
        """افزودن پیام به باکس گزارش‌های متنی"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = "❌ " if is_error else "🔹 "
        log_box.value += f"[{timestamp}] {prefix}{message}\n"
        page.update()

    # ------------------------------------------------------------------
    # اکشن‌ها و توابع عملیاتی
    # ------------------------------------------------------------------

    # ۱. تابع اجرای تحلیل
    def run_analysis_action(e):
        nonlocal current_analysis, current_df
        symbol = symbol_input.value.strip().upper()
        timeframe = tf_dropdown.value

        if not symbol:
            write_log("لطفا نماد معاملاتی را وارد کنید.", is_error=True)
            return

        write_log(f"شروع تحلیل نماد {symbol} در تایم‌فریم {timeframe}...")

        # تولید داده‌های کندل شبیه‌سازی شده با پایتون خالص (بدون نیاز به pandas و numpy)
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

        # بروزرسانی کارت نتایج
        result_card.controls = [
            ft.Divider(color=ft.colors.GOLD),
            ft.Text(f"📊 نتایج تحلیل: {symbol} [{timeframe}]", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GOLD),
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
        write_log("✅ تحلیل با موفقیت انجام شد و خطوط نارنجی، بنفش و زون‌ها محاسبه شدند.")
        page.update()

    # ۲. تابع ارسال به تلگرام
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
        chart_path = reporter.generate_chart(current_df, current_analysis)

        caption = (
            f"🎯 **سیگنال استراتژی عرضه و تقاضا**\n\n"
            f"🔹 **نماد:** {current_analysis['symbol']}\n"
            f"🔹 **تایم‌فریم:** {current_analysis['timeframe']}\n"
            f"🟧 **خط بالا:** {current_analysis['orange_info']['top_orange']:.4f}\n"
            f"🟧 **خط پایین:** {current_analysis['orange_info']['bottom_orange']:.4f}\n"
            f"🟪 **تارگت اصلی:** {current_analysis['purple_lines']['purple_top']:.4f}\n"
            f"⛔ **حد ضرر:** {current_analysis['purple_lines']['purple_bottom']:.4f}\n"
        )

        success = reporter.send_telegram_report(chart_path, caption)
        if success:
            write_log("✈️ چارت تحلیلی و گزارش با موفقیت به تلگرام ارسال شد.")
        else:
            write_log("خطا در ارسال به تلگرام. توکن یا چت‌آیدی را بررسی کنید.", is_error=True)

    # ۳. تابع اجرای معامله در متاتریدر ۵
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

    # ۴. تابع بستن تمام پوزیشن‌ها (Reset)
    def reset_all_action(e):
        if MT5ExecutionEngine is None:
            write_log("⚠️ این بخش مخصوص نسخه ویندوز متصل به متاتریدر ۵ است.", is_error=True)
            return

        mt5_engine = MT5ExecutionEngine()
        res = mt5_engine.close_all_and_cancel_pendings()
        write_log(f"🧹 ریست کامل انجام شد: {res['closed_positions']} پوزیشن بسته و {res['cancelled_orders']} سفارش معلق لغو شدند.")

    # ------------------------------------------------------------------
    # چیدمان عناصر صفحه (Layout Construction)
    # ------------------------------------------------------------------
    page.add(
        ft.Column([
            # هدر برنامه
            ft.Row([
                ft.Icon(ft.icons.CANDLESTICK_CHART, color=ft.colors.GOLD, size=36),
                ft.Text("Mehran Trader - نرم‌افزار جامع مدیریت عرضه و تقاضا", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(color=ft.colors.GREY_800),

            # فرم تنظیمات ورودی
            ft.Text("۱. تنظیمات تحلیل نماد", size=15, weight=ft.FontWeight.BOLD),
            ft.Row([symbol_input, tf_dropdown]),

            ft.Text("۲. تنظیمات تلگرام و مدیریت ریسک", size=15, weight=ft.FontWeight.BOLD),
            ft.Row([bot_token_input, chat_id_input, risk_input]),

            ft.Divider(color=ft.colors.GREY_800),

            # دکمه‌های عملیاتی
            ft.Row([
                ft.ElevatedButton("🔍 تحلیل و محاسبه زون‌ها", on_click=run_analysis_action, icon=ft.icons.ANALYTICS, style=ft.ButtonStyle(color=ft.colors.BLACK, bg=ft.colors.GOLD)),
                ft.ElevatedButton("✈️ ارسال به تلگرام", on_click=send_telegram_action, icon=ft.icons.SEND, style=ft.ButtonStyle(bg=ft.colors.BLUE_700)),
                ft.ElevatedButton("⚡ اجرای پله‌ای در MT5", on_click=execute_mt5_action, icon=ft.icons.PLAY_ARROW, style=ft.ButtonStyle(bg=ft.colors.GREEN_700)),
                ft.ElevatedButton("❌ بستن تمام پوزیشن‌ها (Reset)", on_click=reset_all_action, icon=ft.icons.CANCEL, style=ft.ButtonStyle(bg=ft.colors.RED_700)),
            ], wrap=True, spacing=10),

            # نمایش نتایج و باکس لاگ
            result_card,
            ft.Divider(color=ft.colors.GREY_800),
            ft.Text("📜 گزارش عملیات و لاگ سیستم:", size=14, weight=ft.FontWeight.BOLD),
            log_container,
        ], spacing=15)
    )

if __name__ == "__main__":
    ft.app(target=main)
