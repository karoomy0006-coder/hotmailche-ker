"""
Email Auditor Pro — Configuration Module
Outlook/Hotmail Account Checker (email:pass)

Mandatory Disclaimer:
This tool is intended solely for educational and security testing purposes,
with explicit written consent from account owners. Unauthorised access to
accounts is illegal and strictly prohibited. Use at your own risk.
"""
import os
from pathlib import Path

# ─── Bot Core ───
BOT_TOKEN = "8872535321:AAHltagg4XJv-86JJNhdK5Jxz_7TTZ54fdA"

# ⚠️ ADMIN_IDS يجب أن تكون قائمة (List) من الأرقام، وليس نصاً
ADMIN_IDS = [8703458182]   # ضع معرفك هنا (رقم فقط)

# ─── Paths ───
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "bot.db"))

# ─── Performance ───
MAX_CONCURRENT_CHECKS = int(os.getenv("MAX_CONCURRENT_CHECKS", "500"))
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "10"))
PROXY_CHECK_TIMEOUT = int(os.getenv("PROXY_CHECK_TIMEOUT", "5"))
DEFAULT_MAIL_FROM = os.getenv("DEFAULT_MAIL_FROM", "verify@auditor.bot")
PROGRESS_UPDATE_INTERVAL = int(os.getenv("PROGRESS_UPDATE_INTERVAL", "3"))

# ─── Proxy Test Target ───
PROXY_VALIDATE_HOST = os.getenv("PROXY_VALIDATE_HOST", "gmail-smtp-in.l.google.com")
PROXY_VALIDATE_PORT = int(os.getenv("PROXY_VALIDATE_PORT", "25"))

# ─── Payments ───
TELEGRAM_PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# USDT TRC20 – العقد الصحيح لـ USDT على شبكة TRON
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY", "")
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"   # العقد الرسمي
USDT_TRC20_DEPOSIT_ADDRESS = os.getenv("USDT_TRC20_DEPOSIT_ADDRESS", "YOUR_TRON_ADDRESS")

# Stripe / YooKassa (اختياري)
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
YOOKASSA_WEBHOOK_SECRET = os.getenv("YOOKASSA_WEBHOOK_SECRET", "")

# ─── Subscription Tiers ───
TIERS = {
    "3days": {
        "name_en": "3 Days",
        "name_ar": "3 أيام",
        "stars": 50,
        "usdt": 2.0,
        "duration_days": 3,
    },
    "1week": {
        "name_en": "1 Week",
        "name_ar": "أسبوع",
        "stars": 100,
        "usdt": 5.0,
        "duration_days": 7,
    },
    "1month": {
        "name_en": "1 Month",
        "name_ar": "شهر",
        "stars": 300,
        "usdt": 15.0,
        "duration_days": 30,
    },
    "3months": {
        "name_en": "3 Months",
        "name_ar": "3 أشهر",
        "stars": 750,
        "usdt": 40.0,
        "duration_days": 90,
    },
    "lifetime": {
        "name_en": "Lifetime",
        "name_ar": "مدى الحياة",
        "stars": 2500,
        "usdt": 150.0,
        "duration_days": 36500,
    },
}

# ─── Stickers ───
# 🎯 اتركها فارغة إذا لم تحصل على المعرفات – البوت سيتخطاها تلقائياً
STICKER_PROCESSING = ""   # املأها عندما تحصل على المعرف
STICKER_SUCCESS = ""      # املأها عندما تحصل على المعرف
STICKER_ERROR = ""        # املأها عندما تحصل على المعرف

# ─── Legal ───
DISCLAIMER = (
    "This tool is intended solely for educational and security testing purposes, "
    "with explicit written consent from account owners. Unauthorised access to "
    "accounts is illegal and strictly prohibited. Use at your own risk."
)
