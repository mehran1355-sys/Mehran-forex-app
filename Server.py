from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import MetaTrader5 as mt5
import datetime

from strategy_engine import SupplyDemandEngine

app = FastAPI(title="Mehran MT5 Supply/Demand Server")


class AnalyzeRequest(BaseModel):
    symbol: str
    timeframe: str  # MN1, W1, D1


class AnalyzeResponse(BaseModel):
    symbol: str
    timeframe: str
    monitoring_tf: str
    date_str: str
    last_price: float
    category: str
    top_orange: float
    bottom_orange: float
    near: tuple
    mid: tuple
    far: tuple
    purple_top: float
    purple_bottom: float
    top_count: int
    bottom_count: int
    breakout_type: str


TIMEFRAME_MAP = {
    "MN1": mt5.TIMEFRAME_MN1,
    "W1": mt5.TIMEFRAME_W1,
    "D1": mt5.TIMEFRAME_D1,
    "H4": mt5.TIMEFRAME_H4,
    "H1": mt5.TIMEFRAME_H1,
}


def connect_mt5():
    if not mt5.initialize():
        raise RuntimeError("اتصال به MT5 برقرار نشد. لطفاً MT5 را باز و لاگین کن.")


def fetch_mt5_ohlc(symbol: str, timeframe: str, count: int = 500):
    tf = TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_D1)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None:
        return None

    df = {
        "time": [datetime.datetime.fromtimestamp(r['time']) for r in rates],
        "open": [r['open'] for r in rates],
        "high": [r['high'] for r in rates],
        "low": [r['low'] for r in rates],
        "close": [r['close'] for r in rates],
        "is_live": True,
    }
    return df


@app.on_event("startup")
def startup_event():
    connect_mt5()


@app.get("/symbols")
def list_symbols():
    symbols = mt5.symbols_get()
    return [
        {"code": s.name, "description": s.description}
        for s in symbols
    ]


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    symbol = req.symbol.upper()
    timeframe = req.timeframe

    info = mt5.symbol_info(symbol)
    if info is None:
        raise HTTPException(status_code=400, detail="این نماد در MT5 وجود ندارد.")

    df = fetch_mt5_ohlc(symbol, timeframe)
    if df is None or not df["close"]:
        raise HTTPException(status_code=500, detail="داده‌ای از MT5 دریافت نشد.")

    last_price = df["close"][-1]

    engine = SupplyDemandEngine(symbol, timeframe)
    orange_info = engine.calculate_orange_lines(df)
    breakout_type, touched_top_first = engine.detect_breakout(df, orange_info)
    zones = engine.calculate_zones(orange_info, touched_top_first)
    purples = engine.find_purple_lines(df, orange_info)
    monitoring_tf = engine.get_monitoring_timeframe()

    record = AnalyzeResponse(
        symbol=symbol,
        timeframe=timeframe,
        monitoring_tf=monitoring_tf,
        date_str=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        last_price=last_price,
        category=orange_info["category"],
        top_orange=orange_info["top_orange"],
        bottom_orange=orange_info["bottom_orange"],
        near=zones["near"],
        mid=zones["mid"],
        far=zones["far"],
        purple_top=purples["purple_top"],
        purple_bottom=purples["purple_bottom"],
        top_count=purples.get("top_found_count", 0),
        bottom_count=purples.get("bottom_found_count", 0),
        breakout_type=breakout_type,
    )

    return record
