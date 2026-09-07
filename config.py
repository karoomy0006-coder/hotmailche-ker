"""
Email Auditor Pro — Configuration Module
Mandatory Disclaimer: This tool is intended solely for internal email list hygiene
and auditing by enterprises that have obtained explicit written consent from the
owners of the target domains. It must not be used for sending unsolicited emails
or for any unauthorised access to accounts.
"""
import os
from pathlib import Path

# ─── Bot Core ───
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

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
PROGRESS_UPDATE_INTERVAL = int(os.getenv("PROGRESS_UPDATE_INTERVAL", "3"))  # seconds

# ─── Proxy Test Target ───
# We validate proxies by opening a TCP connection to a well-known mail server.
PROXY_VALIDATE_HOST = os.getenv("PROXY_VALIDATE_HOST", "gmail-smtp-in.l.google.com")
PROXY_VALIDATE_PORT = int(os.getenv("PROXY_VALIDATE_PORT", "25"))

# ─── Payments ───
# Telegram Stars use currency="XTR" — no provider token required.
TELEGRAM_PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# USDT TRC20 — configure your TronGrid API key for deposit listening
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY", "")
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Official USDT contract
USDT_TRC20_DEPOSIT_ADDRESS = os.getenv("USDT_TRC20_DEPOSIT_ADDRESS", "YOUR_TRON_ADDRESS")

# Stripe / YooKassa webhooks (optional)
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
YOOKASSA_WEBHOOK_SECRET = os.getenv("YOOKASSA_WEBHOOK_SECRET", "")

# ─── Subscription Tiers ───
# Prices: Stars are integer amounts. USDT prices are float.
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

# ─── Stickers (replace with your premium sticker file_ids) ───
STICKER_PROCESSING = os.getenv("STICKER_PROCESSING", "")
STICKER_SUCCESS = os.getenv("STICKER_SUCCESS", "")
STICKER_ERROR = os.getenv("STICKER_ERROR", "")

# ─── Legal ───
DISCLAIMER = (
    "This tool is intended solely for internal email list hygiene and auditing by enterprises "
    "that have obtained explicit written consent from the owners of the target domains. "
    "It must not be used for sending unsolicited emails or for any unauthorised access to accounts."
)
