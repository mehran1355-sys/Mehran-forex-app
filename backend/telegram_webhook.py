# backend/telegram_webhook.py

from fastapi import FastAPI, Request
from telegram_notifier import LAST_SIGNAL_CACHE
from telegram_notifier import TelegramNotifier
import requests

app = FastAPI()
telegram = TelegramNotifier()


@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "callback_query" not in data:
        return {"status": "ignored"}

    callback = data["callback_query"]
    user_choice = callback["data"]

    signal = LAST_SIGNAL_CACHE.copy()

    if not signal:
        telegram.send("❗ هیچ سیگنالی برای اجرا وجود ندارد.")
        return {"status": "no_signal"}

    if user_choice == "CONFIRM_OPEN":
        telegram.send("✔️ کاربر تأیید کرد: پوزیشن باز می‌شود.")

        payload = {
            "symbol": signal["symbol"],
            "volume": 0.1,
            "order_type": "buy" if signal["direction"] == "buy" else "sell",
            "entry": signal["entry"],
            "stop_loss": signal["stop_loss"],
            "take_profit": signal["take_profit_1"],
            "strategy_key": "telegram_confirmed"
        }

        try:
            response = requests.post("http://127.0.0.1:8000/execute_trade", json=payload)
            result = response.json()
            telegram.send(f"نتیجه اجرای معامله:\n{result}")
        except Exception as e:
            telegram.send(f"❌ خطا در اجرای معامله: {e}")

    elif user_choice == "CANCEL_OPEN":
        telegram.send("❌ کاربر پوزیشن را لغو کرد.")

    return {"status": "ok"}
