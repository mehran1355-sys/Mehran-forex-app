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

    # آیا callback query وجود دارد؟
    if "callback_query" not in data:
        return {"status": "ignored"}

    callback = data["callback_query"]
    user_choice = callback["data"]  # CONFIRM_OPEN یا CANCEL_OPEN

    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]

    # آخرین سیگنال ذخیره شده
    signal = LAST_SIGNAL_CACHE.copy()

    if not signal:
        telegram.send("❗ هیچ سیگنالی برای اجرا وجود ندارد.")
        return {"status": "no_signal"}

    # اگر کاربر تأیید کرد
    if user_choice == "CONFIRM_OPEN":
        telegram.send("✔️ کاربر تأیید کرد: پوزیشن باز می‌شود.")

        # ساخت payload معامله
        payload = {
            "symbol": signal["symbol"],
            "volume": 0.1,  # بعداً از مدیریت ریسک می‌گیریم
            "order_type": "buy" if signal["direction"] == "buy" else "sell",
            "entry": signal["entry"],
            "stop_loss": signal["stop_loss"],
            "take_profit": signal["take_profit_1"],
            "strategy_key": "telegram_confirmed"
        }

        # ارسال به API اصلی برای اجرای معامله
        try:
            response = requests.post("http://127.0.0.1:8000/execute_trade", json=payload)
            result = response.json()
            telegram.send(f"نتیجه اجرای معامله:\n{result}")
        except Exception as e:
            telegram.send(f"❌ خطا در اجرای معامله: {e}")

    # اگر کاربر لغو کرد
    elif user_choice == "CANCEL_OPEN":
        telegram.send("❌ کاربر پوزیشن را لغو کرد.")

    return {"status": "ok"}
