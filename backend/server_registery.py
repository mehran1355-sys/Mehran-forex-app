# backend/server_registery.py

import time

class ServerRegistry:
    def __init__(self):
        self.servers = {}

    def register(self, server_name: str, ip: str):
        self.servers[server_name] = {
            "ip": ip,
            "last_seen": time.time(),
            "status": "online"
        }

    def heartbeat(self, server_name: str):
        if server_name in self.servers:
            self.servers[server_name]["last_seen"] = time.time()
            self.servers[server_name]["status"] = "online"

    def check_offline(self, timeout_seconds=15):
        now = time.time()
        for name, info in self.servers.items():
            if now - info["last_seen"] > timeout_seconds:
                info["status"] = "offline"

    def get_all(self):
        self.check_offline()
        return self.servers

    def get_active_servers(self):
        self.check_offline()
        return {
            name: info for name, info in self.servers.items()
            if info["status"] == "online"
        }

    def get_best_server(self):
        active = self.get_active_servers()
        for name, info in active.items():
            return {"server": name, "ip": info["ip"]}
        return None
def get_failover_server(self, primary_server: str):
        """اگر سرور اصلی آفلاین شد، سرور بعدی را انتخاب می‌کند"""
        self.check_offline()

        # اگر سرور اصلی آنلاین است → همان را برگردان
        if primary_server in self.servers:
            if self.servers[primary_server]["status"] == "online":
                return {
                    "server": primary_server,
                    "ip": self.servers[primary_server]["ip"],
                    "failover": False
                }

        # اگر سرور اصلی آفلاین بود → سرور بعدی را انتخاب کن
        active_servers = self.get_active_servers()

        if not active_servers:
            return {"status": "no_active_server"}

        # انتخاب اولین سرور آنلاین به عنوان failover
        for name, info in active_servers.items():
            return {
                "server": name,
                "ip": info["ip"],
                "failover": True
            }

        return {"status": "no_active_server"}
