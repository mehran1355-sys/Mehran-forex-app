import flet as ft

def main(page: ft.Page):
    page.title = "Mehran Forex Trading App"
    page.theme_mode = "dark"
    page.padding = 15
    page.scroll = "adaptive"

    # ---------------------------------------------------------
    # محتوای تب ۱: ماشین‌حساب و مدیریت ریسک
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

    tab1_view = ft.Column(
        [
            ft.Text("ماشین‌حساب مدیریت ریسک", size=18, weight="bold", color="amber"),
            calc_lot,
            calc_pip,
            ft.ElevatedButton(
                content=ft.Text("محاسبه سود / زیان", size=16),
                style=ft.ButtonStyle(color="black", bgcolor="amber", padding=12),
                on_click=on_calculate,
                width=320
            ),
            ft.Divider(height=15, color="transparent"),
            calc_result
        ],
        horizontal_alignment="center",
        spacing=12
    )

    # ---------------------------------------------------------
    # محتوای تب ۲: استراتژی و سیگنال‌ها
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
    strategy_result = ft.Text("وضعیت: در انتظار تحلیل...", size=15, color="bluegrey200")

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

    tab2_view = ft.Column(
        [
            ft.Text("تحلیل استراتژی و کندل‌ها", size=18, weight="bold", color="amber"),
            body_input,
            shadow_input,
            ft.ElevatedButton(
                content=ft.Text("بررسی شرایط استراتژی", size=16),
                style=ft.ButtonStyle(color="black", bgcolor="amber", padding=12),
                on_click=on_analyze,
                width=320
            ),
            ft.Divider(height=15, color="transparent"),
            strategy_result
        ],
        horizontal_alignment="center",
        spacing=12
    )

    # ---------------------------------------------------------
    # محتوای تب ۳: تنظیمات
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

    tab3_view = ft.Column(
        [
            ft.Text("تنظیمات سیستم", size=18, weight="bold", color="amber"),
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
        spacing=12
    )

    # ---------------------------------------------------------
    # سیستم نوار ناوبری سفارشی (Custom Tabs)
    # ---------------------------------------------------------
    main_container = ft.Container(content=tab1_view, padding=10)

    btn_tab1 = ft.ElevatedButton(
        content=ft.Text("ماشین‌حساب", size=13),
        style=ft.ButtonStyle(color="black", bgcolor="amber")
    )
    btn_tab2 = ft.ElevatedButton(
        content=ft.Text("استراتژی", size=13),
        style=ft.ButtonStyle(color="white", bgcolor="grey800")
    )
    btn_tab3 = ft.ElevatedButton(
        content=ft.Text("تنظیمات", size=13),
        style=ft.ButtonStyle(color="white", bgcolor="grey800")
    )

    def switch_tab(tab_num):
        if tab_num == 1:
            main_container.content = tab1_view
            btn_tab1.style = ft.ButtonStyle(color="black", bgcolor="amber")
            btn_tab2.style = ft.ButtonStyle(color="white", bgcolor="grey800")
            btn_tab3.style = ft.ButtonStyle(color="white", bgcolor="grey800")
        elif tab_num == 2:
            main_container.content = tab2_view
            btn_tab1.style = ft.ButtonStyle(color="white", bgcolor="grey800")
            btn_tab2.style = ft.ButtonStyle(color="black", bgcolor="amber")
            btn_tab3.style = ft.ButtonStyle(color="white", bgcolor="grey800")
        elif tab_num == 3:
            main_container.content = tab3_view
            btn_tab1.style = ft.ButtonStyle(color="white", bgcolor="grey800")
            btn_tab2.style = ft.ButtonStyle(color="white", bgcolor="grey800")
            btn_tab3.style = ft.ButtonStyle(color="black", bgcolor="amber")
        page.update()

    btn_tab1.on_click = lambda e: switch_tab(1)
    btn_tab2.on_click = lambda e: switch_tab(2)
    btn_tab3.on_click = lambda e: switch_tab(3)

    nav_row = ft.Row(
        [btn_tab1, btn_tab2, btn_tab3],
        alignment="center",
        spacing=6
    )

    page.add(
        nav_row,
        ft.Divider(height=15, color="amber"),
        main_container
    )

ft.app(target=main)
