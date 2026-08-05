# backend/server_registery.py

import time
from telegram_notifier import notify_server_offline
from voice_alert import VoiceAlert

class ServerRegistry:
    def __init__(self):
        self.servers = {}
        self.lb_index = 0
        self.voice = VoiceAlert()

    def register(self, server_name: str, ip: str):
        self.servers[server_name] = {
            "ip": ip,
            "status": "online",
            "last_seen": time.time(),
            "health": None
        }

    def heartbeat(self, server_name: str):
        if server_name in self.servers:
            self.servers[server_name]["last_seen"] = time.time()
            self.servers[server_name]["status"] = "online"

    def check_offline(self):
        now = time.time()
        timeout_seconds = 10

        for name, info in self.servers.items():
            if now - info["last_seen"] > timeout_seconds:
                if info["status"] != "offline":
                    info["status"] = "offline"
                    notify_server_offline(name)
                    self.voice.create_alert(
                        text=f"سرور {name} آفلاین شد.",
                        filename=f"{name}_offline.mp3"
                    )

    def get_all(self):
        self.check_offline()
        return self.servers

    def get_best_server(self):
        self.check_offline()
        for name, info in self.servers.items():
            if info["status"] == "online":
                return {"server": name, "ip": info["ip"]}
        return None

    def get_failover_server(self, primary_server: str):
        self.check_offline()
        if primary_server in self.servers:
            if self.servers[primary_server]["status"] == "online":
                return {
                    "server": primary_server,
                    "ip": self.servers[primary_server]["ip"],
                    "failover": False
                }

        active = self.get_active_servers()
        if not active:
            return {"status": "no_active_server"}

        for name, info in active.items():
            return {
                "server": name,
                "ip": info["ip"],
                "failover": True
            }

        return {"status": "no_active_server"}

    def get_active_servers(self):
        self.check_offline()
        return {name: info for name, info in self.servers.items() if info["status"] == "online"}

    def get_balanced_server(self):
        active = self.get_active_servers()
        if not active:
            return {"status": "no_active_server"}

        active_list = list(active.items())
        name, info = active_list[self.lb_index]
        self.lb_index = (self.lb_index + 1) % len(active_list)

        return {
            "server": name,
            "ip": info["ip"],
            "load_balancing": True
        }

    def update_health(self, server_name: str, cpu: float, ram: float, mt5: bool, latency: float):
        if server_name not in self.servers:
            return {"status": "server_not_registered"}

        score = self.calculate_score(cpu, ram, mt5, latency)

        self.servers[server_name]["health"] = {
            "cpu": cpu,
            "ram": ram,
            "mt5": mt5,
            "latency": latency,
            "score": score
        }

        self.servers[server_name]["last_seen"] = time.time()
        self.servers[server_name]["status"] = "online"

        return {"status": "updated", "score": score}

    def calculate_score(self, cpu, ram, mt5, latency):
        score = 100
        if cpu > 80: score -= 30
        elif cpu > 60: score -= 15
        if ram > 80: score -= 30
        elif ram > 60: score -= 15
        if not mt5: score -= 40
        if latency > 300: score -= 20
        elif latency > 150: score -= 10
        return max(score, 0)

    def get_best_health_server(self):
        self.check_offline()
        best_server = None
        best_score = -1

        for name, info in self.servers.items():
            if info["status"] == "online" and info["health"]:
                score = info["health"]["score"]
                if score > best_score:
                    best_score = score
                    best_server = {
                        "server": name,
                        "ip": info["ip"],
                        "score": score
                    }

        if best_server is None:
            return {"status": "no_active_server"}

        return best_server
