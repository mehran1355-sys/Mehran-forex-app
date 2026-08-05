# backend/api.py

from fastapi import FastAPI, HTTPException
from strategy_engine import run_strategy
from risk_manager import RiskManager
from chart_generator import generate_chart
from server_registery import ServerRegistry
from strategy_router import StrategyRouter

app = FastAPI(title="Mehran Forex App Backend")

risk_manager = RiskManager()
server_registry = ServerRegistry()
strategy_router = StrategyRouter()


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
@app.post("/server_heartbeat")
def server_heartbeat(server_name: str):
    server_registry.heartbeat(server_name)
    return {"status": "alive", "server": server_name}

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
