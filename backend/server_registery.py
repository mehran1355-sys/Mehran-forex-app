# backend/server_registery.py

import time

class ServerRegistry:
    def __init__(self):
        # ساختار ذخیره‌سازی سرورها
        self.servers = {}  
        # مثال ساختار:
        # {
        #   "Laptop1": {
        #       "ip": "192.168.1.10",
        #       "last_seen": 1723456789,
        #       "status": "online"
        #   }
        # }

    def register(self, server_name: str, ip: str):
        """ثبت سرور جدید یا آپدیت سرور قبلی"""
        self.servers[server_name] = {
            "ip": ip,
            "last_seen": time.time(),
            "status": "online"
        }

    def heartbeat(self, server_name: str):
        """آپدیت زمان آخرین اتصال سرور"""
        if server_name in self.servers:
            self.servers[server_name]["last_seen"] = time.time()
            self.servers[server_name]["status"] = "online"

    def mark_offline(self, server_name: str):
        """علامت‌گذاری سرور به عنوان آفلاین"""
        if server_name in self.servers:
            self.servers[server_name]["status"] = "offline"

    def get_all(self):
        """برگرداندن لیست کامل سرورها"""
        return self.servers

    def get_active_servers(self):
        """برگرداندن سرورهای آنلاین"""
        active = {
            name: info
            for name, info in self.servers.items()
            if info["status"] == "online"
        }
        return active

    def get_best_server(self):
        """انتخاب بهترین سرور (ساده‌ترین نسخه: اولین سرور آنلاین)"""
        active = self.get_active_servers()
        if not active:
            return None

        # انتخاب اولین سرور آنلاین
        for name, info in active.items():
            return {"server": name, "ip": info["ip"]}

        return None
