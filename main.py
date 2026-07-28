import flet as ft

def main(page: ft.Page):
    page.title = "Mehran Forex Trading"
    page.theme_mode = "dark"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.padding = 20

    title_text = ft.Text(
        "MEHRAN FOREX",
        size=28,
        weight="bold",
        color="amber"
    )
    subtitle_text = ft.Text(
        "TRADING GROUP",
        size=14,
        weight="w500",
        color="bluegrey200"
    )

    lot_input = ft.TextField(
        label="حجم معامله (Lot)",
        keyboard_type="number",
        width=300,
        border_color="amber"
    )
    pip_input = ft.TextField(
        label="میزان پیپ (Pip)",
        keyboard_type="number",
        width=300,
        border_color="amber"
    )

    result_text = ft.Text(size=18, weight="bold", color="amber")

    def calculate_profit(e):
        try:
            lots = float(lot_input.value)
            pips = float(pip_input.value)
            profit = lots * pips * 10
            result_text.value = f"تخمین سود/زیان: {profit:,.2f} $"
            result_text.color = "green" if profit >= 0 else "red"
        except (ValueError, TypeError):
            result_text.value = "لطفاً مقادیر عددی معتبر وارد کنید."
            result_text.color = "amber"
        page.update()

    calc_button = ft.ElevatedButton(
        content=ft.Text("محاسبه مستقیم روی گوشی", size=16),
        style=ft.ButtonStyle(
            color="black",
            bg_color="amber",
            padding=15
        ),
        on_click=calculate_profit,
        width=300
    )

    page.add(
        title_text,
        subtitle_text,
        ft.Divider(height=30, color="transparent"),
        lot_input,
        pip_input,
        ft.Divider(height=10, color="transparent"),
        calc_button,
        ft.Divider(height=20, color="transparent"),
        result_text
    )

ft.app(target=main)
