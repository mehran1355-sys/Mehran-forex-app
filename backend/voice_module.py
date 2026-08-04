from strategy_router import get_strategy_from_voice
from strategy_engine import run_strategy

def handle_voice_command(text: str, df_dict=None):
    strategy_key = get_strategy_from_voice(text)
    if strategy_key is None:
        return "روش یا بازار نامعتبر است. لطفاً دوباره بگو."

    result = run_strategy(strategy_key, df_dict)
    return result
