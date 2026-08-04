# backend/chart_generator.py

import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

CHART_DIR = Path("charts")
CHART_DIR.mkdir(exist_ok=True)

def generate_chart(df_dict, analysis, symbol, timeframe):
    """
    رسم نمودار ساده قیمت + زون‌ها و ذخیره به صورت تصویر
    """
    times = df_dict["time"]
    closes = df_dict["close"]

    plt.figure(figsize=(10, 5))
    plt.plot(times, closes, label="Close", color="blue")

    orange = analysis.get("orange", {})
    zones = analysis.get("zones", {})

    if orange:
        plt.axhline(orange["top_orange"], color="orange", linestyle="--", label="Top Orange")
        plt.axhline(orange["bottom_orange"], color="orange", linestyle="--", label="Bottom Orange")

    if zones:
        near = zones.get("near")
        mid = zones.get("mid")
        far = zones.get("far")
        if near:
            plt.axhspan(near[0], near[1], color="green", alpha=0.2, label="Near Zone")
        if mid:
            plt.axhspan(mid[0], mid[1], color="yellow", alpha=0.2, label="Mid Zone")
        if far:
            plt.axhspan(far[0], far[1], color="red", alpha=0.2, label="Far Zone")

    plt.title(f"{symbol} - {timeframe}")
    plt.legend()
    plt.tight_layout()

    filename = f"{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    file_path = CHART_DIR / filename
    plt.savefig(file_path)
    plt.close()

    return str(file_path)
