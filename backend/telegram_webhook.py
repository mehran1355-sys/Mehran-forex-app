# backend/telegram_webhook.py

from fastapi import FastAPI, Request
from mt5_execution import open_trade_with_risk

app = FastAPI()

# این مقادیر را بعداً داینامیک از دیتابیس/حافظه می‌گیریم
LAST_SIGNAL_CACHE = {
    "symbol": None,
    "direction": None,
    "entry": None,
    "stop_loss": None,
    "take_profit_1": None,
    "take_profit_2": None,
    "account_equity": None,
    "contract_size": None,
    "user_risk_percent": None,
}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data_value = callback["data"]

        if data_value == "CONFIRM_OPEN":
            trade_result = open_trade_with_risk(
                symbol=LAST_SIGNAL_CACHE["symbol"],
                direction=LAST_SIGNAL_CACHE["direction"],
                entry=LAST_SIGNAL_CACHE["entry"],
                stop_loss=LAST_SIGNAL_CACHE["stop_loss"],
                tp1=LAST_SIGNAL_CACHE["take_profit_1"],
                tp2=LAST_SIGNAL_CACHE["take_profit_2"],
                account_equity=LAST_SIGNAL_CACHE["account_equity"],
                contract_size=LAST_SIGNAL_CACHE["contract_size"],
                user_risk_percent=LAST_SIGNAL_CACHE["user_risk_percent"],
            )

            text = "✅ پوزیشن بر اساس تأیید شما باز شد."
        elif data_value == "CANCEL_OPEN":
            text = "❌ پوزیشن بر اساس تصمیم شما باز نشد."
        else:
            text = "دستور نامشخص."

        # پاسخ به تلگرام
        import requests
        BOT_TOKEN = "YOUR_BOT_TOKEN"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        requests.post(url, json=payload)

    return {"ok": True}
