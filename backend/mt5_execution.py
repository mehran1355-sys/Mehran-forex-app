from risk_manager import RiskManager

risk_manager = RiskManager()

def open_trade(symbol, direction, position_size, stop_loss, tp1, tp2):
    print(f"پوزیشن باز شد: {symbol} | جهت: {direction} | حجم: {position_size}")
    print(f"SL: {stop_loss} | TP1: {tp1} | TP2: {tp2}")

def open_trade_with_risk(symbol, direction, entry, stop_loss,
                         tp1, tp2, account_equity, contract_size, user_risk_percent):

    risk_manager.set_user_risk_limit(user_risk_percent)

    new_risk = risk_manager.calculate_position_risk(
        entry=entry,
        stop_loss=stop_loss,
        account_equity=account_equity,
        contract_size=contract_size,
    )

    allowed, status = risk_manager.can_open_position(new_risk)

    if allowed and status == "auto_allowed":
        position_size = 1  # بعداً دقیق محاسبه می‌شود
        open_trade(symbol, direction, position_size, stop_loss, tp1, tp2)
        risk_manager.add_position(new_risk)

        return {
            "executed": True,
            "position_size": position_size,
            "new_risk": new_risk,
            "current_risk": risk_manager.current_risk
        }

    elif status == "need_user_confirmation":
        return {
            "executed": False,
            "need_confirmation": True,
            "new_risk": new_risk,
            "current_risk": risk_manager.current_risk,
            "user_risk_limit": risk_manager.user_risk_limit
        }

    return {
        "executed": False,
        "error": "risk_limit_not_set"
    }
