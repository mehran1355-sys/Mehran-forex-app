# backend/api.py

from fastapi import FastAPI, HTTPException
import requests

from strategy_engine import run_strategy
from risk_manager import RiskManager
from chart_generator import generate_chart
from server_registery import ServerRegistry
from strategy_router import StrategyRouter
from trade_logger import TradeLogger


app = FastAPI(title="Mehran Forex App Backend")

risk_manager = RiskManager()
server_registry = ServerRegistry()
strategy_router = StrategyRouter()
trade_logger = TradeLogger()


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
#   (2) Server Heartbeat
# ============================

@app.post("/server_heartbeat")
def server_heartbeat(server_name: str):
    server_registry.heartbeat(server_name)
    return {"status": "alive", "server": server_name}


# ============================
#   (3) Server Status
# ============================

@app.get("/server_status")
def server_status():
    return server_registry.get_all()


# ============================
#   (4) Best Server
# ============================

@app.get("/best_server")
def best_server():
    best = server_registry.get_best_server()
    if best is None:
        return {"status": "no_active_server"}
    return best


# ============================
#   Failover System
# ============================

@app.get("/failover")
def failover(primary_server: str):
    return server_registry.get_failover_server(primary_server)


# ============================
#   Load Balancing
# ============================

@app.get("/balanced_server")
def balanced_server():
    return server_registry.get_balanced_server()


# ============================
#   Health Check System
# ============================

@app.post("/server_health")
def server_health(server_name: str, cpu: float, ram: float, mt5: bool, latency: float):
    return server_registry.update_health(server_name, cpu, ram, mt5, latency)


@app.get("/best_health_server")
def best_health_server():
    return server_registry.get_best_health_server()


# ============================
#   Strategy Execution
# ============================

@app.post("/run_strategy")
def run_strategy_api(
    strategy_key: str,
    symbol: str,
    timeframe: str,
    entry: float,
    stop_loss: float,
    account_equity: float,
    contract_size: float,
    df_dict: dict
):
    try:
        result = run_strategy(
            strategy_key=strategy_key,
            df_dict=df_dict,
            account_equity=account_equity,
            contract_size=contract_size,
            entry=entry,
            stop_loss=stop_loss,
            symbol=symbol,
            timeframe=timeframe
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
#   Strategy Router
# ============================

@app.post("/strategy_router")
def strategy_router_api(symbol: str, timeframe: str):
    return strategy_router.route(symbol, timeframe)


# ============================
#   Risk Info
# ============================

@app.get("/risk_info")
def risk_info():
    return {
        "current_risk": risk_manager.current_risk,
        "user_risk_limit": risk_manager.user_risk_limit
    }


# ============================
#   Generate Chart
# ============================

@app.post("/generate_chart")
def generate_chart_api(symbol: str, timeframe: str, df_dict: dict):
    try:
        path = generate_chart(df_dict, None, symbol, timeframe)
        return {"chart_path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
#   Trade Execution (Backend → Server → MT5)
# ============================

@app.post("/execute_trade")
def execute_trade(
    symbol: str,
    volume: float,
    order_type: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    strategy_key: str
):
    # انتخاب بهترین سرور بر اساس سلامت
    best = server_registry.get_best_health_server()

    if "status" in best and best["status"] == "no_active_server":
        return {"status": "failed", "reason": "no_active_server"}

    server_ip = best["ip"]

    payload = {
        "symbol": symbol,
        "volume": volume,
        "order_type": order_type,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "strategy_key": strategy_key
    }

    try:
        response = requests.post(f"http://{server_ip}:8000/mt5_execute", json=payload)
        result = response.json()
    except Exception as e:
        return {"status": "failed", "reason": str(e)}

    # ثبت معامله در Trade Logger
    trade_logger.log_trade({
        "symbol": symbol,
        "volume": volume,
        "order_type": order_type,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "strategy_key": strategy_key,
        "server_ip": server_ip,
        "result": result
    })

    return result


# ============================
#   Trade Logs
# ============================

@app.get("/trade_logs")
def trade_logs():
    return trade_logger.get_logs()
