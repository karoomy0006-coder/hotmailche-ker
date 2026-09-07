import os
from pathlib import Path

BOT_TOKEN = "8872535321:AAHltagg4XJv-86JJNhdK5Jxz_7TTZ54fdA"
ADMIN_IDS = [8703458182]

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "bot.db"))

MAX_CONCURRENT_CHECKS = int(os.getenv("MAX_CONCURRENT_CHECKS", "500"))
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "10"))
PROXY_CHECK_TIMEOUT = int(os.getenv("PROXY_CHECK_TIMEOUT", "5"))
PROGRESS_UPDATE_INTERVAL = int(os.getenv("PROGRESS_UPDATE_INTERVAL", "3"))

PROXY_VALIDATE_HOST = os.getenv("PROXY_VALIDATE_HOST", "gmail-smtp-in.l.google.com")
PROXY_VALIDATE_PORT = int(os.getenv("PROXY_VALIDATE_PORT", "25"))

TELEGRAM_PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY", "")
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
USDT_TRC20_DEPOSIT_ADDRESS = os.getenv("USDT_TRC20_DEPOSIT_ADDRESS", "YOUR_TRON_ADDRESS")

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
YOOKASSA_WEBHOOK_SECRET = os.getenv("YOOKASSA_WEBHOOK_SECRET", "")

TIERS = {
    "3days": {"name_en": "3 Days", "name_ar": "3 أيام", "stars": 50, "usdt": 2.0, "duration_days": 3},
    "1week": {"name_en": "1 Week", "name_ar": "أسبوع", "stars": 100, "usdt": 5.0, "duration_days": 7},
    "1month": {"name_en": "1 Month", "name_ar": "شهر", "stars": 300, "usdt": 15.0, "duration_days": 30},
    "3months": {"name_en": "3 Months", "name_ar": "3 أشهر", "stars": 750, "usdt": 40.0, "duration_days": 90},
    "lifetime": {"name_en": "Lifetime", "name_ar": "مدى الحياة", "stars": 2500, "usdt": 150.0, "duration_days": 36500},
}

STICKER_PROCESSING = ""
STICKER_SUCCESS = ""
STICKER_ERROR = ""

DISCLAIMER = (
    "This tool is intended solely for educational and security testing purposes, "
    "with explicit written consent from account owners. Unauthorised access to "
    "accounts is illegal and strictly prohibited. Use at your own risk."
)
