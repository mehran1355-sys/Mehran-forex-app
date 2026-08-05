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
    def get_balanced_server(self):
        """انتخاب سرور به صورت Load Balancing (Round-Robin)"""

        self.check_offline()
        active = self.get_active_servers()

        if not active:
            return {"status": "no_active_server"}

        # تبدیل دیکشنری به لیست
        active_list = list(active.items())

        # اگر قبلاً سروری انتخاب نشده، اولین سرور را انتخاب کن
        if not hasattr(self, "lb_index"):
            self.lb_index = 0

        # انتخاب سرور بر اساس lb_index
        name, info = active_list[self.lb_index]

        # برو به سرور بعدی
        self.lb_index = (self.lb_index + 1) % len(active_list)

        return {
            "server": name,
            "ip": info["ip"],
            "load_balancing": True
        }
def update_health(self, server_name: str, cpu: float, ram: float, mt5: bool, latency: float):
        """آپدیت وضعیت سلامت سرور"""

        if server_name not in self.servers:
            return {"status": "server_not_registered"}

        self.servers[server_name]["health"] = {
            "cpu": cpu,
            "ram": ram,
            "mt5": mt5,
            "latency": latency,
            "score": self.calculate_score(cpu, ram, mt5, latency)
        }

        # آپدیت زمان آخرین اتصال
        self.servers[server_name]["last_seen"] = time.time()
        self.servers[server_name]["status"] = "online"

        return {"status": "updated", "server": server_name}

    def calculate_score(self, cpu, ram, mt5, latency):
        """محاسبه امتیاز سلامت سرور"""

        score = 100

        # CPU
        if cpu > 80:
            score -= 30
        elif cpu > 60:
            score -= 15

        # RAM
        if ram > 80:
            score -= 30
        elif ram > 60:
            score -= 15

        # MT5
        if not mt5:
            score -= 40

        # Latency
        if latency > 300:
            score -= 20
        elif latency > 150:
            score -= 10

        return max(score, 0)

    def get_best_health_server(self):
        """انتخاب بهترین سرور بر اساس سلامت"""

        self.check_offline()

        best_server = None
        best_score = -1

        for name, info in self.servers.items():
            if info["status"] == "online" and "health" in info:
                score = info["health"]["score"]
                if score > best_score:
                    best_score = score
                    best_server = {"server": name, "ip": info["ip"], "score": score}

        if best_server is None:
            return {"status": "no_active_server"}

        return best_server
