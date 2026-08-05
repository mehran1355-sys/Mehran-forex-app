# backend/error_monitor.py

import json
import time
import os
from telegram_notifier import TelegramNotifier

class ErrorMonitor:
    def __init__(self, log_file="error_log.json"):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f)
        self.telegram = TelegramNotifier()

    def log_error(self, source: str, message: str, extra: dict = None, notify: bool = True):
        data = {
            "timestamp": time.time(),
            "source": source,
            "message": message,
            "extra": extra or {}
        }

        with open(self.log_file, "r") as f:
            logs = json.load(f)

        logs.append(data)

        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

        if notify:
            self.telegram.send(
                f"⚠️ خطا در سیستم\n"
                f"منبع: {source}\n"
                f"پیام: {message}"
            )

        return {"status": "logged"}

    def get_errors(self):
        with open(self.log_file, "r") as f:
            return json.load(f)
