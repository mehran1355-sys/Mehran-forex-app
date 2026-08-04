# backend/api.py

from fastapi import FastAPI
from pydantic import BaseModel
from strategy_engine import run_strategy
from mt5_execution import open_trade_with_risk

app = FastAPI()


# ============================
#   مدل ورودی اپ موبایل
# ============================

class StrategyRequest(BaseModel):
    strategy_key: str
    df_dict: dict
    account_equity: float
    contract_size: float
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    user_risk_percent: float
    direction: str
    symbol: str
    timeframe: str


# ============================
#   Endpoint اجرای استراتژی
# ============================

@app.post("/strategy/run")
def run_strategy_api(req: StrategyRequest):

    # اجرای تحلیل + مدیریت ریسک
    result = run_strategy(
        strategy_key=req.strategy_key,
        df_dict=req.df_dict,
        account_equity=req.account_equity,
        contract_size=req.contract_size,
        entry=req.entry,
        stop_loss=req.stop_loss
    )

    # اگر نیاز به تأیید کاربر باشد
    if result["risk"]["status"] == "need_user_confirmation":
        return {
            "status": "need_confirmation",
            "message": "مدیریت ریسک اجازه اتومات نمی‌دهد.",
            "analysis": result["analysis"],
            "risk": result["risk"]
        }

    # اگر اتومات اجازه دهد → معامله باز شود
    if result["risk"]["status"] == "auto_allowed":
        trade_result = open_trade_with_risk(
            symbol=req.symbol,
            direction=req.direction,
            entry=req.entry,
            stop_loss=req.stop_loss,
            take_profit_1=req.take_profit_1,
            take_profit_2=req.take_profit_2,
            account_equity=req.account_equity,
            contract_size=req.contract_size,
            user_risk_percent=req.user_risk_percent
        )

        return {
            "status": "opened_auto",
            "analysis": result["analysis"],
            "risk": result["risk"],
            "trade": trade_result
        }

    # اگر حد ریسک تنظیم نشده باشد
    return {
        "status": "risk_limit_not_set",
        "message": "ابتدا حد ریسک کاربر باید تنظیم شود."
    }
