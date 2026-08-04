# risk_manager.py

class RiskManager:
    def __init__(self):
        self.user_risk_limit = None      # درصد ریسک کاربر مثل 0.20
        self.current_risk = 0.0          # مجموع ریسک پوزیشن‌های باز
        self.open_positions = []         # لیست پوزیشن‌های باز

    def set_user_risk_limit(self, percent: float):
        """
        کاربر تعیین می‌کند چند درصد از موجودی درگیر معامله شود.
        مثال: 20 یعنی 20٪
        """
        self.user_risk_limit = percent / 100

    def calculate_position_risk(self, entry, stop_loss, account_equity, contract_size):
        """
        محاسبه ریسک پوزیشن جدید بر اساس فاصله SL و حجم معامله.
        """
        pip_risk = abs(entry - stop_loss)
        risk_amount = pip_risk * contract_size
        return risk_amount / account_equity

    def can_open_position(self, new_position_risk: float):
        """
        بررسی می‌کند آیا پوزیشن جدید باعث عبور از حد مجاز ریسک می‌شود یا نه.
        """
        if self.user_risk_limit is None:
            return False, "risk_limit_not_set"

        if self.current_risk + new_position_risk <= self.user_risk_limit:
            return True, "auto_allowed"

        return False, "need_user_confirmation"

    def add_position(self, new_position_risk: float):
        """
        اضافه کردن پوزیشن جدید به لیست پوزیشن‌ها و افزایش ریسک فعلی.
        """
        self.open_positions.append(new_position_risk)
        self.current_risk += new_position_risk

    def remove_position(self, position_risk: float):
        """
        حذف پوزیشن و کاهش ریسک فعلی.
        """
        if position_risk in self.open_positions:
            self.open_positions.remove(position_risk)
            self.current_risk -= position_risk
