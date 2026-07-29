import MetaTrader5 as mt5
import pandas as pd

class MT5ExecutionEngine:
    """
    ماژول مدیریت معاملات، محاسبه ریسک کل و ارسال سفارش‌ها به متاتریدر ۵
    """

    def __init__(self, max_total_risk_percent: float = 40.0):
        self.max_total_risk_percent = max_total_risk_percent
        self.is_connected = False

    def connect(self) -> bool:
        """برقراری ارتباط با نرم‌افزار متاتریدر ۵"""
        if not mt5.initialize():
            print(f"❌ خطا در اتصال به متاتریدر ۵: {mt5.last_error()}")
            self.is_connected = False
            return False
        
        self.is_connected = True
        return True

    def disconnect(self):
        """قطع ارتباط با متاتریدر ۵"""
        mt5.shutdown()
        self.is_connected = False

    # ------------------------------------------------------------------
    # ۱. محاسبه ریسک کل درگیر (مجموع تمام معاملات باز)
    # ------------------------------------------------------------------
    def calculate_current_total_risk(() -> float:
        """
        محاسبه درصد ریسک کل معاملات باز شده روی حساب
        (منظور ۴۰٪ کل معاملات باز شده است)
        """
        account_info = mt5.account_info()
        if account_info is None:
            return 0.0

        equity = account_info.equity
        if equity <= 0:
            return 0.0

        positions = mt5.positions_get()
        if not positions:
            return 0.0

        total_risk_money = 0.0

        for pos in positions:
            # محاسبه میزان ریسک بر اساس فاصله قیمت ورود تا حد ضرر (SL)
            sl = pos.sl
            if sl > 0:
                price_open = pos.price_open
                volume = pos.volume
                symbol_info = mt5.symbol_info(pos.symbol)
                
                if symbol_info:
                    point = symbol_info.point
                    tick_value = symbol_info.trade_tick_value
                    
                    if point > 0:
                        dist_points = abs(price_open - sl) / point
                        risk_money = dist_points * tick_value * volume
                        total_risk_money += risk_money

        used_risk_percent = (total_risk_money / equity) * 100.0
        return used_risk_percent

    # ------------------------------------------------------------------
    # ۲. ارسال سفارش‌های لیمیت پله‌ای
    # ------------------------------------------------------------------
    def place_limit_orders(self, symbol: str, order_type: str, orders_plan: list, sl_price: float, tp1_price: float, tp2_price: float) -> dict:
        """
        ثبت سفارش‌های Buy Limit یا Sell Limit به‌صورت پله‌ای در زون تعیین شده
        """
        if not self.is_connected:
            if not self.connect():
                return {"success": False, "message": "عدم اتصال به متاتریدر ۵"}

        # کنترل سقف ریسک کل ۴۰٪
        current_risk = self.calculate_current_total_risk()
        if current_risk >= self.max_total_risk_percent:
            return {
                "success": False,
                "message": f"⚠️ هشدار: ریسک درگیر فعلی ({current_risk:.2f}%) برابر یا بیشتر از سقف مجاز ({self.max_total_risk_percent}%) است."
            }

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None or not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        mt5_order_type = mt5.ORDER_TYPE_BUY_LIMIT if order_type == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
        placed_orders = []

        for item in orders_plan:
            price = item["price"]
            volume = item["volume"]

            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": float(volume),
                "type": mt5_order_type,
                "price": float(price),
                "sl": float(sl_price),
                "tp": float(tp2_price),  # تارگت اصلی
                "deviation": 10,
                "magic": 100200,
                "comment": "SupplyDemand_Strategy",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                placed_orders.append(result.order)
            else:
                print(f"❌ خطا در ثبت سفارش پله {item['step']}: {result.comment}")

        return {
            "success": True,
            "placed_count": len(placed_orders),
            "orders": placed_orders
        }

    # ------------------------------------------------------------------
    # ۳. ریست کامل در انتهای تایم‌فریم (بستن پوزیشن‌ها و لغو اوردرها)
    # ------------------------------------------------------------------
    def close_all_and_cancel_pendings(self, symbol: str = None) -> dict:
        """
        بستن تمامی پوزیشن‌های فعال و لغو تمامی سفارش‌های معلق (Pending Orders)
        در انتهای تایم‌فریم معاملاتی
        """
        if not self.is_connected:
            self.connect()

        cancelled_orders = 0
        closed_positions = 0

        # ۱. لغو تمام سفارش‌های معلق (Pending Orders)
        orders = mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get()
        if orders:
            for ord_item in orders:
                req = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": ord_item.ticket
                }
                res = mt5.order_send(req)
                if res.retcode == mt5.TRADE_RETCODE_DONE:
                    cancelled_orders += 1

        # ۲. بستن تمامی پوزیشن‌های فعال به قیمت مارکت
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions:
            for pos in positions:
                tick = mt5.symbol_info_tick(pos.symbol)
                close_price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY

                req = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "position": pos.ticket,
                    "price": close_price,
                    "deviation": 20,
                    "magic": 100200,
                    "comment": "Timeframe_End_Reset",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                }
                res = mt5.order_send(req)
                if res.retcode == mt5.TRADE_RETCODE_DONE:
                    closed_positions += 1

        return {
            "closed_positions": closed_positions,
            "cancelled_orders": cancelled_orders
        }
