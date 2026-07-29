import flet as ft

def main(page: ft.Page):
    page.title = "Mehran Forex Trading App"
    page.theme_mode = "dark"
    page.padding = 15
    page.scroll = "adaptive"

    # ---------------------------------------------------------
    # تب ۱: ماشین‌حساب و مدیریت ریسک
    # ---------------------------------------------------------
    calc_lot = ft.TextField(
        label="حجم معامله (Lot)",
        keyboard_type="number",
        width=320,
        border_color="amber"
    )
    calc_pip = ft.TextField(
        label="میزان پیپ (Pip)",
        keyboard_type="number",
        width=320,
        border_color="amber"
    )
    calc_result = ft.Text(size=16, weight="bold", color="amber")

    def on_calculate(e):
        try:
            lots = float(calc_lot.value)
            pips = float(calc_pip.value)
            profit = lots * pips * 10
            calc_result.value = f"تخمین سود/زیان: {profit:,.2f} $"
            calc_result.color = "green" if profit >= 0 else "red"
        except (ValueError, TypeError):
            calc_result.value = "لطفاً مقادیر عددی معتبر وارد کنید."
            calc_result.color = "amber"
        page.update()

    tab1_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("ماشین‌حساب مدیریت ریسک", size=20, weight="bold", color="amber"),
                calc_lot,
                calc_pip,
                ft.ElevatedButton(
                    content=ft.Text("محاسبه سود / زیان", size=16),
                    style=ft.ButtonStyle(color="black", bgcolor="amber", padding=12),
                    on_click=on_calculate,
                    width=320
                ),
                ft.Divider(height=20, color="transparent"),
                calc_result
            ],
            horizontal_alignment="center",
            spacing=15
        ),
        padding=10
    )

    # ---------------------------------------------------------
    # تب ۲: استراتژی و سیگنال‌ها
    # ---------------------------------------------------------
    body_input = ft.TextField(
        label="طول بدنه کندل",
        keyboard_type="number",
        width=320,
        border_color="amber"
    )
    shadow_input = ft.TextField(
        label="طول سایه کندل",
        keyboard_type="number",
        width=320,
        border_color="amber"
    )
    strategy_result = ft.Text("وضعیت: در انتظار تحلیل ورودی‌ها...", size=15, color="bluegrey200")

    def on_analyze(e):
        try:
            b = float(body_input.value)
            s = float(shadow_input.value)
            if s >= b * 2:
                strategy_result.value = "سیگنال: سایه بلند شناسایی شد (۵۰٪ طول سایه لحاظ می‌شود)"
                strategy_result.color = "green"
            else:
                strategy_result.value = "سیگنال: کندل عادی / الگوی استاندارد"
                strategy_result.color = "amber"
        except (ValueError, TypeError):
            strategy_result.value = "لطفاً مقادیر بدنه و سایه را وارد کنید."
            strategy_result.color = "red"
        page.update()

    tab2_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("تحلیل استراتژی و کندل‌ها", size=20, weight="bold", color="amber"),
                body_input,
                shadow_input,
                ft.ElevatedButton(
                    content=ft.Text("بررسی شرایط استراتژی", size=16),
                    style=ft.ButtonStyle(color="black", bgcolor="amber", padding=12),
                    on_click=on_analyze,
                    width=320
                ),
                ft.Divider(height=20, color="transparent"),
                strategy_result
            ],
            horizontal_alignment="center",
            spacing=15
        ),
        padding=10
    )

    # ---------------------------------------------------------
    # تب ۳: تنظیمات
    # ---------------------------------------------------------
    max_risk_input = ft.TextField(
        label="سقف ریسک کل معاملات باز (%)",
        value="40",
        keyboard_type="number",
        width=320,
        border_color="amber"
    )
    settings_status = ft.Text(size=14, color="green")

    def on_save_settings(e):
        settings_status.value = f"تنظیمات ذخیره شد (حد ریسک کل: {max_risk_input.value}٪)"
        page.update()

    tab3_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("تنظیمات سیستم", size=20, weight="bold", color="amber"),
                max_risk_input,
                ft.ElevatedButton(
                    content=ft.Text("ذخیره تنظیمات", size=16),
                    style=ft.ButtonStyle(color="black", bgcolor="amber", padding=12),
                    on_click=on_save_settings,
                    width=320
                ),
                ft.Divider(height=15, color="transparent"),
                settings_status
            ],
            horizontal_alignment="center",
            spacing=15
        ),
        padding=10
    )

    # ---------------------------------------------------------
    # ساختاربندی تب‌ها بدون آرگومان text
    # ---------------------------------------------------------
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                tab_content=ft.Text("ماشین حساب"),
                icon="calculate",
                content=tab1_content
            ),
            ft.Tab(
                tab_content=ft.Text("استراتژی"),
                icon="analytics",
                content=tab2_content
            ),
            ft.Tab(
                tab_content=ft.Text("تنظیمات"),
                icon="settings",
                content=tab3_content
            ),
        ],
        expand=True
    )

    page.add(tabs)

ft.app(target=main)
