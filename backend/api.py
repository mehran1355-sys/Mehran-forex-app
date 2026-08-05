# backend/api.py

from fastapi import FastAPI, HTTPException
import requests

from strategy_engine import run_strategy
from risk_manager import RiskManager
from chart_generator import generate_chart
from server_registery import ServerRegistry
from strategy_router import StrategyRouter
from trade_logger import TradeLogger
from telegram_notifier import (
    TelegramNotifier,
    notify_trade_execution,
    notify_server_offline
)
from voice_alert import VoiceAlert
from error_monitor import ErrorMonitor


app = FastAPI(title="Mehran Forex App Backend")

risk_manager = RiskManager()
server_registry = ServerRegistry()
strategy_router = StrategyRouter()
trade_logger = TradeLogger()
telegram = TelegramNotifier()
voice = VoiceAlert()
error_monitor = ErrorMonitor()


# ============================
#   Root
# ============================

@app.get("/")
def root():
    return {"status": "running", "message": "Mehran Forex Backend Active"}


# ============================
#   Register Device (Mobile)
# ============================

@app.post("/register_device")
def register_device(device_id: str):
    return {"status": "ok", "device_id": device_id}


# ============================
#   Register Server (Laptop)
# ============================

@app.post("/register_server")
def register_server(server_name: str, ip: str):
    server_registry.register(server_name, ip)
    return {"status": "registered", "server": server_name, "ip": ip}


@app.get("/servers")
def list_servers():
    return server_registry.get_all()


# ============================
#   Heartbeat
# ============================

@app.post("/server_heartbeat")
def server_heartbeat(server_name: str):
    server_registry.heartbeat(server_name)
    return {"status": "alive", "server": server_name}


# ============================
#   Server Status
# ============================

@app.get("/server_status")
def server_status():
    return server_registry.get_all()


# ============================
#   Best Server
# ============================

@app.get("/best_server")
def best_server():
    best = server_registry.get_best_server()
    if best is None:
        return {"status": "no_active_server"}
    return best


# ============================
#   Failover
# ============================

@app.get("/failover")
def failover(primary
