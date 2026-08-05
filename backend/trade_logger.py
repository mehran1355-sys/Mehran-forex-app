# backend/trade_logger.py

import csv
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def log_trade(trade_data: dict):
    """
    ذخیره اطلاعات معامله در فایل CSV (قابل باز شدن در اکسل)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = LOG_DIR / f"trades_{today}.csv"

    headers = [
        "datetime",
        "strategy_key",
        "symbol",
        "timeframe",
        "direction",
        "entry",
        "stop_loss",
        "take_profit_1",
        "take_profit_2",
        "new_risk",
        "current_risk",
        "user_risk_limit",
        "status",
        "executed",
    ]

    row = [
        datetime.now().isoformat(),
        trade_data.get("strategy_key"),
        trade_data.get("symbol"),
        trade_data.get("timeframe"),
        trade_data.get("direction"),
        trade_data.get("entry"),
        trade_data.get("stop_loss"),
        trade_data.get("take_profit_1"),
        trade_data.get("take_profit_2"),
        trade_data.get("new_risk"),
        trade_data.get("current_risk"),
        trade_data.get("user_risk_limit"),
        trade_data.get("status"),
        trade_data.get("executed"),
    ]

    file_exists = file_path.exists()

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)
telegram = TelegramNotifier(
    bot_token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID"
)
