# strategy_router.py

STRATEGY_MAP = {
    "LONG_TERM": {
        "FOREX_STOCK": "LT_FOREX_STOCK",
        "CRYPTO": "LT_CRYPTO",
        "IRAN": "LT_IRAN",
    },
    "MID_TERM": {
        "FOREX_STOCK": "MT_FOREX_STOCK",
        "CRYPTO": "MT_CRYPTO",
        "IRAN": "MT_IRAN",
    },
    "SCALP": {
        "FOREX_STOCK": "SC_FOREX_STOCK",
        "CRYPTO": "SC_CRYPTO",
        "IRAN": "SC_IRAN",
    },
    "TICK_TOCK": {
        "FOREX_STOCK": "TT_FOREX_STOCK",
        "CRYPTO": "TT_CRYPTO",
        "IRAN": "TT_IRAN",
    },
}


VOICE_COMMANDS = {
    # بلندمدت
    "استراتژی بلندمدت فارکس": ("LONG_TERM", "FOREX_STOCK"),
    "استراتژی بلندمدت سهام": ("LONG_TERM", "FOREX_STOCK"),
    "استراتژی بلندمدت ارز دیجیتال": ("LONG_TERM", "CRYPTO"),
    "استراتژی بلندمدت بورس ایران": ("LONG_TERM", "IRAN"),

    # میان‌مدت
    "استراتژی میان‌مدت فارکس": ("MID_TERM", "FOREX_STOCK"),
    "استراتژی میان‌مدت سهام": ("MID_TERM", "FOREX_STOCK"),
    "استراتژی میان‌مدت ارز دیجیتال": ("MID_TERM", "CRYPTO"),
    "استراتژی میان‌مدت بورس ایران": ("MID_TERM", "IRAN"),

    # اسکلپ
    "استراتژی اسکلپ فارکس": ("SCALP", "FOREX_STOCK"),
    "استراتژی اسکلپ سهام": ("SCALP", "FOREX_STOCK"),
    "استراتژی اسکلپ ارز دیجیتال": ("SCALP", "CRYPTO"),
    "استراتژی اسکلپ بورس ایران": ("SCALP", "IRAN"),

    # تیک‌تاکی
    "استراتژی تیک‌تاکی فارکس": ("TICK_TOCK", "FOREX_STOCK"),
    "استراتژی تیک‌تاکی سهام": ("TICK_TOCK", "FOREX_STOCK"),
    "استراتژی تیک‌تاکی ارز دیجیتال": ("TICK_TOCK", "CRYPTO"),
    "استراتژی تیک‌تاکی بورس ایران": ("TICK_TOCK", "IRAN"),
}


def get_strategy_key(strategy_type: str, market_type: str) -> str | None:
    strategy = STRATEGY_MAP.get(strategy_type)
    if not strategy:
        return None
    return strategy.get(market_type)


def get_strategy_from_voice(phrase: str) -> str | None:
    mapping = VOICE_COMMANDS.get(phrase.strip())
    if not mapping:
        return None
    strategy_type, market_type = mapping
    return get_strategy_key(strategy_type, market_type)
