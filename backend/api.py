# backend/api.py

from fastapi import FastAPI
from pydantic import BaseModel

from strategy_engine import run_strategy
from mt5_execution import open_trade_with_risk
from telegram_notifier import send_signal_to_telegram

app = FastAPI()


# ============================
#   Request Model
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
#   Strategy API
# ============================

@app.post("/strategy/run")
def run_strategy_api(req: StrategyRequest):

    # اجرای استراتژی
    result = run_strategy(
        strategy_key=req.strategy_key,
        df_dict=req.df_dict,
        account_equity=req.account_equity,
        contract_size=req.contract_size,
        entry=req.entry,
        stop_loss=req.stop_loss,
        symbol=req.symbol,
        timeframe=req.timeframe
    )

    # آماده‌سازی داده برای تلگرام
    signal_data = result.copy()
    signal_data["account_equity"] = req.account_equity
    signal_data["contract_size"] = req.contract_size
    signal_data["user_risk_percent"] = req.user_risk_percent

    # ارسال سیگنال به تلگرام (متن + دکمه + نمودار)
    send_signal_to_telegram(signal_data)

    # اگر نیاز به تأیید کاربر باشد
    if result["status"] == "need_user_confirmation":
        return {
            "status": "need_confirmation",
            "analysis": result["analysis"],
            "signal": result["signal"],
            "risk": result["risk"],
            "chart_path": result.get("chart_path"),
            "explanation": result["explanation"]
        }

    # اگر اتومات اجازه دهد → معامله باز شود
    if result
