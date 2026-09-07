# Email Auditor Pro — Telegram Bot

**Enterprise-grade asynchronous email validation bot.**

> **Disclaimer:** This tool is intended solely for internal email list hygiene and auditing by enterprises that have obtained explicit written consent from the owners of the target domains. It must not be used for sending unsolicited emails or for any unauthorised access to accounts.

## Features
- **SMTP-based validation** (MX lookup → RCPT TO) — no passwords, no logins.
- **Massive concurrency** (up to 1,000 parallel checks) with `asyncio`.
- **Smart proxy rotation** — HTTP / SOCKS4 / SOCKS5 support.
- **Multi-language** — English & Arabic.
- **Tiered subscriptions** — 3 Days, 1 Week, 1 Month, 3 Months, Lifetime.
- **Payments** — Telegram Stars (native) + USDT TRC20 (on-chain polling).
- **Live progress bars** & premium sticker feedback inside Telegram.
- **Memory-safe** — streams large files line-by-line.

## Quick Start

### 1. Clone / extract the project
```bash
cd email_auditor_bot
```

### 2. Configure environment variables
```bash
export BOT_TOKEN="YOUR_BOT_TOKEN_FROM_BOTFATHER"
export ADMIN_IDS="123456789"
export USDT_TRC20_DEPOSIT_ADDRESS="YOUR_TRON_WALLET_ADDRESS"
export TRONGRID_API_KEY="YOUR_TRONGRID_KEY"   # optional but recommended
```

Or edit `config.py` directly.

### 3. Run with Docker
```bash
docker build -t email-auditor .
docker run -e BOT_TOKEN=$BOT_TOKEN -e ADMIN_IDS=$ADMIN_IDS -v $(pwd)/data:/app/data -v $(pwd)/results:/app/results email-auditor
```

### 4. Or run locally
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Usage Flow
1. `/start` → choose language.
2. **Upload Proxies** (optional but recommended).
3. **Upload Email List** (one email per line).
4. **Set Concurrency** (default 500).
5. **Buy Premium** → pay with Telegram Stars or USDT TRC20.
6. **Start Audit** → watch live progress bar.
7. **Download Results** → get `.txt` with valid emails.

## Project Structure
```
email_auditor_bot/
├── bot.py              # Telegram handlers & orchestration
├── config.py           # Settings, tiers, disclaimer
├── database.py         # Async SQLite (users, subs, sessions)
├── i18n.py             # EN / AR translations
├── proxy_manager.py    # Proxy parsing, validation, rotation
├── smtp_engine.py      # MX lookup + SMTP RCPT TO engine
├── requirements.txt
└── Dockerfile
```

## Legal & Ethical Compliance
- Only validates **email existence** via public SMTP MX records.
- **No password checking**, no account cracking, no Microsoft login attempts.
- Built-in disclaimer enforced in code and UI.
- Users must have **written consent** from domain owners before auditing.

## License
Proprietary — for licensed enterprise use only.
