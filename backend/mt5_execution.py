# backend/mt5_execution.py

from risk_manager import RiskManager

risk_manager = RiskManager()


def open_trade(symbol, direction, position_size, stop_loss, take_profit_1, take_profit_2):
    """
    این تابع جای اجرای واقعی دستور MT5 است.
    فعلاً فقط نمایشی است؛ بعداً کد MetaTrader5 اینجا می‌آید.
    """
    print(f"باز کردن پوزیشن: {symbol} | جهت: {direction} | حجم: {position_size}")
    print(f"SL: {stop_loss} | TP1: {take_profit_1} | TP2: {take_profit_2}")


def open_trade_with_risk(symbol, direction, entry, stop_loss,
                         take_profit_1, take_profit_2,
                         account_equity, contract_size, user_risk_percent):
    """
    باز کردن پوزیشن با در نظر گرفتن مدیریت ریسک.
    اگر مجموع ریسک از حد مجاز عبور کند، نیاز به تأیید کاربر است.
    """

    risk_manager.set_user_risk_limit(user_risk_percent)

    new_risk = risk_manager.calculate_position_risk(
        entry=entry,
        stop_loss=stop_loss,
        account_equity=account_equity,
        contract_size=contract_size,
    )

    allowed, status = risk_manager.can_open_position(new_risk)

    if allowed and status == "auto_allowed":
        position_size = 1  # بعداً بر اساس new_risk و SL دقیق محاسبه می‌شود

        open_trade(symbol, direction, position_size, stop_loss, take_profit_1, take_profit_2)
        risk_manager.add_position(new_risk)

        return {
            "status": "opened_auto",
            "message": "پوزیشن به صورت خودکار باز شد.",
            "new_risk": new_risk,
            "current_risk": risk_manager.current_risk,
        }

    elif status == "need_user_confirmation":
        return {
            "status": "need_confirmation",
            "message": "مدیریت ریسک اجازه اتومات نمی‌دهد؛ نیاز به تأیید کاربر است.",
            "new_risk": new_risk,
            "current_risk": risk_manager.current_risk,
            "user_risk_limit": risk_manager.user_risk_limit,
        }

    else:
        return {
            "status": "risk_limit_not_set",
            "message": "ابتدا حد ریسک کاربر باید تنظیم شود.",
        }
