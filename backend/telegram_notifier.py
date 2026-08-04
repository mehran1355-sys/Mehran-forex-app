import requests

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_ID = "YOUR_CHANNEL_OR_CHAT_ID"


def send_signal_to_telegram(signal_data: dict):
    strategy_key = signal_data.get("strategy_key")
    analysis = signal_data.get("analysis", {})
    risk = signal_data.get("risk", {})
    signal = signal_data.get("signal", {})

    text_lines = []

    text_lines.append(f"📊 سیگنال استراتژی: {strategy_key}")
    text_lines.append("")

    symbol = signal.get("symbol", "نامشخص")
    timeframe = signal.get("timeframe", "نامشخص")
    direction = signal.get("direction", "نامشخص")

    text_lines.append(f"نماد: {symbol}")
    text_lines.append(f"تایم‌فریم: {timeframe}")
    text_lines.append(f"جهت: {direction}")

    entry_zone = signal.get("entry_zone")
    if entry_zone:
        text_lines.append(f"زون ورود: {entry_zone[0]} - {entry_zone[1]}")

    sl = signal.get("stop_loss")
    tp1 = signal.get("take_profit_1")
    tp2 = signal.get("take_profit_2")

    if sl is not None:
        text_lines.append(f"حد ضرر: {sl}")
    if tp1 is not None:
        text_lines.append(f"حد سود ۱: {tp1}")
    if tp2 is not None:
        text_lines.append(f"حد سود ۲: {tp2}")

    text_lines.append("")

    if risk:
        current_risk = risk.get("current_risk", 0.0) * 100
        new_risk = risk.get("new_risk", 0.0) * 100
        user_limit = (risk.get("user_risk_limit", 0.0) or 0.0) * 100
        status = risk.get("status", "نامشخص")

        text_lines.append(f"ریسک فعلی پوزیشن‌ها: {current_risk:.2f}%")
        text_lines.append(f"ریسک پوزیشن جدید: {new_risk:.2f}%")
        text_lines.append(f"حد مجاز ریسک کاربر: {user_limit:.2f}%")
        text_lines.append(f"وضعیت مدیریت ریسک: {status}")

    text = "\n".join(text_lines)

    # اگر نیاز به تأیید کاربر باشد، دکمه‌ها را اضافه کن
    reply_markup = None
    if risk.get("status") == "need_user_confirmation":
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✔️ باز کردن پوزیشن", "callback_data": "CONFIRM_OPEN"},
                    {"text": "❌ لغو پوزیشن", "callback_data": "CANCEL_OPEN"},
                ]
            ]
        }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("خطا در ارسال تلگرام:", e)
