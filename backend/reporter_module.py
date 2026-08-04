import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests

class StrategyReporter:
    """
    ماژول تولید خروجی اکسل، رسم نمودارهای تحلیلی با خطوط رنگی 
    و ارسال سیگنال و چارت به کانال تلگرام
    """

    def __init__(self, telegram_bot_token: str = None, telegram_chat_id: str = None):
        self.bot_token = telegram_bot_token
        self.chat_id = telegram_chat_id

    # ------------------------------------------------------------------
    # ۱. تولید و ذخیره جدول تحلیل در فایل اکسل
    # ------------------------------------------------------------------
    def export_to_excel(self, analysis_results: list, file_name: str = "Supply_Demand_Analysis.xlsx") -> str:
        """
        دریافت لیستی از نتایج تحلیل نمادها و خروجی گرفتن به صورت فایل اکسل
        """
        data = []
        for res in analysis_results:
            data.append({
                "نماد": res["symbol"],
                "تایم‌فریم تحلیل": res["timeframe"],
                "تایم‌فریم مانیتورینگ": res["monitoring_tf"],
                "دسته کندل": res["category"],
                "خط نارنجی بالا": res["orange_info"]["top_orange"],
                "خط نارنجی پایین": res["orange_info"]["bottom_orange"],
                "عرض منطقه احتیاط": res["orange_info"]["caution_width"],
                "ناحیه ۱/۳ نزدیک": f"{res['zones']['near'][0]:.4f} - {res['zones']['near'][1]:.4f}",
                "ناحیه ۱/۳ میانی": f"{res['zones']['mid'][0]:.4f} - {res['zones']['mid'][1]:.4f}",
                "ناحیه ۱/۳ دور": f"{res['zones']['far'][0]:.4f} - {res['zones']['far'][1]:.4f}",
                "حد سود اول (TP1)": res["tp1"],
                "حد سود دوم (TP2)": res["purple_lines"]["purple_top"] if res["is_bullish"] else res["purple_lines"]["purple_bottom"],
                "حد ضرر (SL)": res["purple_lines"]["purple_bottom"] if res["is_bullish"] else res["purple_lines"]["purple_top"],
            })

        df = pd.DataFrame(data)
        
        # ذخیره با استایل و انکودینگ مناسب
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='گزارش_تحلیل', index=False)
            
        return os.path.abspath(file_name)

    # ------------------------------------------------------------------
    # ۲. رسم نمودار کندل‌استیک و رسم خطوط استراتژی
    # ------------------------------------------------------------------
    def generate_chart(self, df: pd.DataFrame, analysis: dict, save_path: str = "chart.png") -> str:
        """
        رسم نمودار کندل‌استیک به همراه:
        - خطوط نارنجی (مرزهای احتیاط)
        - خطوط مشکی مقطع (تقسیم ۱/۳)
        - خطوط بنفش (حد سود و حد ضرر)
        """
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 7))

        # آماده‌سازی داده‌های کندل
        recent_df = df.tail(40).copy()
        recent_df = recent_df.reset_index(drop=True)
        
        # رسم کندل‌ها
        for i in range(len(recent_df)):
            open_p = recent_df.loc[i, 'open']
            close_p = recent_df.loc[i, 'close']
            high_p = recent_df.loc[i, 'high']
            low_p = recent_df.loc[i, 'low']
            
            color = '#26a69a' if close_p >= open_p else '#ef5350' # سبز و قرمز فست
            
            # سایه‌ها
            ax.plot([i, i], [low_p, high_p], color=color, linewidth=1.2)
            # بدنه
            ax.bar(i, abs(close_p - open_p), bottom=min(open_p, close_p), color=color, width=0.6)

        orange = analysis["orange_info"]
        purples = analysis["purple_lines"]
        top_o = orange["top_orange"]
        bot_o = orange["bottom_orange"]
        step = orange["zone_step"]

        # ۱. رسم خطوط نارنجی
        ax.axhline(top_o, color='orange', linestyle='-', linewidth=2, label='Orange Line (Top)')
        ax.axhline(bot_o, color='orange', linestyle='-', linewidth=2, label='Orange Line (Bottom)')

        # ۲. رسم خطوط مشکی مقطع (تقسیم ۳ گانه زون احتیاط)
        ax.axhline(top_o - step, color='gray', linestyle='--', linewidth=1, label='1/3 Zones')
        ax.axhline(top_o - (2 * step), color='gray', linestyle='--', linewidth=1)

        # ۳. رسم خطوط بنفش (TP2 / SL)
        if purples["purple_top"]:
            ax.axhline(purples["purple_top"], color='purple', linestyle='-.', linewidth=1.8, label='Purple Line (Top)')
        if purples["purple_bottom"]:
            ax.axhline(purples["purple_bottom"], color='purple', linestyle='-.', linewidth=1.8, label='Purple Line (Bottom)')

        # تنظیمات ظاهری چارت
        symbol = analysis["symbol"]
        tf = analysis["timeframe"]
        ax.set_title(f"Supply & Demand Psychology Strategy - {symbol} [{tf}]", fontsize=14, color='gold', pad=15)
        ax.grid(True, linestyle=':', alpha=0.3)
        ax.legend(loc='upper left', facecolor='#1e1e1e', edgecolor='none')

        plt.tight_layout()
        plt.savefig(save_path, dpi=200)
        plt.close()

        return save_path

    # ------------------------------------------------------------------
    # ۳. ارسال عکس چارت و متن تحلیل به تلگرام
    # ------------------------------------------------------------------
    def send_telegram_report(self, photo_path: str, caption_text: str) -> bool:
        """
        ارسال تصویر چارت به همراه توضیحات کامل سیگنال به ربات/کانال تلگرام
        """
        if not self.bot_token or not self.chat_id:
            print("⚠️ توکن یا چت‌آیدی تلگرام تنظیم نشده است.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo:
                payload = {
                    'chat_id': self.chat_id,
                    'caption': caption_text,
                    'parse_mode': 'Markdown'
                }
                files = {'photo': photo}
                response = requests.post(url, data=payload, files=files, timeout=15)
                
            return response.status_code == 200
        except Exception as e:
            print(f"❌ خطا در ارسال به تلگرام: {e}")
            return False
