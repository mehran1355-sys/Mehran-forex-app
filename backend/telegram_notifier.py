# backend/telegram_notifier.py

import requests

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_ID = "YOUR_CHANNEL_OR_CHAT_ID"

LAST_SIGNAL_CACHE = {}

class TelegramNotifier:
    def __init__(self, bot_token: str = BOT_TOKEN, chat_id: str = CHANNEL_ID):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print("خطا در ارسال تلگرام:", e)

    def send_photo(self, image_path: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        with open(image_path, "rb") as img:
            payload = {"chat_id": self.chat_id}
            files = {"photo": img}
            try:
                requests.post(url, data=payload, files=files)
            except Exception as e:
                print("خطا در ارسال نمودار:", e)


def notify_trade_execution(trade_data: dict):
    notifier = TelegramNotifier()
    msg = (
        "✅ معامله اجرا شد\n"
        f"نماد: {trade_data.get('symbol')}\n"
        f"نوع: {trade_data.get('order_type')}\n"
        f"ورود: {trade_data.get('entry')}\n"
        f"حد ضرر: {trade_data.get('stop_loss')}\n"
        f"حد سود: {trade_data.get('take_profit')}\n"
        f"سرور: {trade_data.get('server_ip')}\n"
    )
    notifier.send(msg)


def notify_server_offline(server_name: str):
    notifier = TelegramNotifier()
    notifier.send(f"⚠️ سرور آفلاین شد: {server_name}")
