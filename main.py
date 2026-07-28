import flet as ft

def main(page: ft.Page):
    page.title = "Mehran Forex Trading"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    title_text = ft.Text(
        "MEHRAN FOREX",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.GOLD_400
    )
    subtitle_text = ft.Text(
        "TRADING GROUP",
        size=14,
        weight=ft.FontWeight.W_500,
        color=ft.Colors.BLUE_GREY_200
    )

    lot_input = ft.TextField(
        label="حجم معامله (Lot)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300,
        border_color=ft.Colors.GOLD_400
    )
    pip_input = ft.TextField(
        label="میزان پیپ (Pip)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300,
        border_color=ft.Colors.GOLD_400
    )

    result_text = ft.Text(size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)

    def calculate_profit(e):
        try:
            lots = float(lot_input.value)
            pips = float(pip_input.value)
            profit = lots * pips * 10
            result_text.value = f"تخمین سود/زیان: {profit:,.2f} $"
            result_text.color = ft.Colors.GREEN_400 if profit >= 0 else ft.Colors.RED_400
        except ValueError:
            result_text.value = "لطفاً مقادیر عددی معتبر وارد کنید."
            result_text.color = ft.Colors.AMBER_400
        page.update()

    calc_button = ft.ElevatedButton(
        content=ft.Text("محاسبه مستقیم روی گوشی", size=16),
        style=ft.ButtonStyle(
            color=ft.Colors.BLACK,
            bg_color=ft.Colors.GOLD_400,
            padding=15
        ),
        on_click=calculate_profit,
        width=300
    )

    page.add(
        title_text,
        subtitle_text,
        ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
        lot_input,
        pip_input,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        calc_button,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        result_text
    )

ft.app(target=main)
Mehran-forex-app
