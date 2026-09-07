"""
Email Auditor Pro — Telegram Bot (python-telegram-bot v20+)

Mandatory Disclaimer:
This tool is intended solely for internal email list hygiene and auditing by enterprises
that have obtained explicit written consent from the owners of the target domains.
It must not be used for sending unsolicited emails or for any unauthorised access to accounts.
"""
import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
)

import config
from i18n import t
from database import db
from proxy_manager import ProxyManager
from smtp_engine import BulkAuditor

# ─── Logging ───
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── In-memory user state ───
# Tracks per-user ephemeral data (uploads, pending payments, etc.)
user_data_store: Dict[int, dict] = {}

# ─── Helpers ───
def _ud(update: Update) -> int:
    """Shorthand for user_id."""
    return update.effective_user.id


def _lang(update: Update) -> str:
    """Fetch user language from DB or default to en."""
    # Fire-and-forget sync wrapper not possible; we pass lang explicitly in async handlers
    return "en"


def render_progress_bar(percent: float, length: int = 18) -> str:
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


def fmt_seconds(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


# ─── Keyboards ───
def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")]
    ])


def main_menu_keyboard(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_upload_proxies", lang), callback_data="menu_proxies"),
         InlineKeyboardButton(t("btn_upload_emails", lang), callback_data="menu_emails")],
        [InlineKeyboardButton(t("btn_start_audit", lang), callback_data="menu_audit"),
         InlineKeyboardButton(t("btn_download_results", lang), callback_data="menu_download")],
        [InlineKeyboardButton(t("btn_subscription", lang), callback_data="menu_sub"),
         InlineKeyboardButton(t("btn_buy_premium", lang), callback_data="menu_buy")],
        [InlineKeyboardButton(t("btn_set_concurrency", lang), callback_data="menu_concurrency"),
         InlineKeyboardButton(t("btn_language", lang), callback_data="menu_lang")],
    ])


def back_keyboard(lang: str, data: str = "menu_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_back", lang), callback_data=data)]
    ])


def tiers_keyboard(lang: str):
    rows = []
    for key, info in config.TIERS.items():
        name = info["name_en"] if lang == "en" else info["name_ar"]
        label = f"{name} — ⭐{info['stars']} / ${info['usdt']}"
        rows.append([InlineKeyboardButton(label, callback_data=f"tier_{key}")])
    rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data="menu_main")])
    return InlineKeyboardMarkup(rows)


def payment_keyboard(lang: str, tier_key: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Telegram Stars", callback_data=f"pay_stars_{tier_key}")],
        [InlineKeyboardButton("💎 USDT (TRC20)", callback_data=f"pay_usdt_{tier_key}")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="menu_buy")],
    ])


# ─── /start ───
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = _ud(update)
    await db.get_or_create_user(uid, update.effective_user.username)
    await update.message.reply_text(
        t("welcome", "en", disclaimer=config.DISCLAIMER),
        reply_markup=lang_keyboard(),
        parse_mode="HTML",
    )


# ─── Language selection ───
async def cb_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    uid = _ud(update)
    await db.set_language(uid, lang)
    await query.edit_message_text(
        t("lang_changed", lang),
        parse_mode="HTML",
    )
    await asyncio.sleep(0.5)
    await query.message.reply_text(
        t("main_menu", lang),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


# ─── Main Menu Router ───
async def cb_menu_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await db.get_language(_ud(update))
    await query.edit_message_text(
        t("main_menu", lang),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


async def cb_menu_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await db.get_language(_ud(update))
    user_data_store[_ud(update)] = {"state": "waiting_proxies"}
    await query.edit_message_text(
        t("upload_proxies_prompt", lang),
        reply_markup=back_keyboard(lang),
        parse_mode="HTML",
    )


async def cb_menu_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await db.get_language(_ud(update))
    user_data_store[_ud(update)] = {"state": "waiting_emails"}
    await query.edit_message_text(
        t("upload_emails_prompt", lang),
        reply_markup=back_keyboard(lang),
        parse_mode="HTML",
    )


# ─── Document Upload Handler ───
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = _ud(update)
    lang = await db.get_language(uid)
    state = user_data_store.get(uid, {}).get("state", "idle")

    doc = update.message.document
    if not doc or not doc.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please send a .txt file.")
        return

    file = await context.bot.get_file(doc.file_id)
    text = (await file.download_as_bytearray()).decode("utf-8", errors="ignore")

    if state == "waiting_proxies":
        pm = ProxyManager()
        count = pm.load_from_text(text)
        msg = await update.message.reply_text(
            t("proxies_uploaded", lang, count=count),
            parse_mode="HTML",
        )
        # Validate in background so Telegram doesn't timeout
        async def _validate():
            await pm.validate_all()
            user_data_store[uid]["proxy_manager"] = pm
            await msg.edit_text(
                t("proxies_validated", lang, valid=pm.valid_count, total=pm.total_raw, invalid=pm.invalid_count),
                reply_markup=back_keyboard(lang),
                parse_mode="HTML",
            )
            if config.STICKER_SUCCESS:
                await context.bot.send_sticker(uid, config.STICKER_SUCCESS)
        asyncio.create_task(_validate())
        user_data_store[uid]["state"] = "idle"

    elif state == "waiting_emails":
        emails = [line.strip() for line in text.splitlines() if "@" in line]
        emails = list(dict.fromkeys(emails))  # dedupe preserving order
        user_data_store[uid]["emails"] = emails
        user_data_store[uid]["state"] = "idle"
        await update.message.reply_text(
            t("emails_uploaded", lang, count=len(emails)),
            reply_markup=back_keyboard(lang),
            parse_mode="HTML",
        )
        if config.STICKER_SUCCESS:
            await context.bot.send_sticker(uid, config.STICKER_SUCCESS)

    else:
        await update.message.reply_text(t("error_generic", lang))


# ─── Concurrency ───
async def cb_menu_concurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await db.get_language(_ud(update))
    user_data_store[_ud(update)]["state"] = "waiting_concurrency"
    await query.edit_message_text(
        t("concurrency_prompt", lang),
        reply_markup=back_keyboard(lang),
        parse_mode="HTML",
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = _ud(update)
    lang = await db.get_language(uid)
    state = user_data_store.get(uid, {}).get("state", "idle")
    text = update.message.text.strip()

    if state == "waiting_concurrency":
        try:
            limit = max(10, min(1000, int(text)))
            user_data_store[uid]["concurrency"] = limit
            user_data_store[uid]["state"] = "idle"
            await update.message.reply_text(
                t("concurrency_set", lang, limit=limit),
                reply_markup=back_keyboard(lang),
                parse_mode="HTML",
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid number.")
        return


# ─── Subscription ───
async def cb_menu_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _ud(update)
    lang = await db.get_language(uid)
    sub = await db.get_active_subscription(uid)
    if sub:
        expires = sub["expires_at"]
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires)
        tier_name = config.TIERS.get(sub["tier"], {}).get("name_en" if lang == "en" else "name_ar", sub["tier"])
        await query.edit_message_text(
            t("subscription_active", lang,
              tier=tier_name,
              expires=expires.strftime("%Y-%m-%d %H:%M UTC"),
              status="✅ Active"),
            reply_markup=back_keyboard(lang),
            parse_mode="HTML",
        )
    else:
        await query.edit_message_text(
            t("subscription_expired", lang),
            reply_markup=back_keyboard(lang),
            parse_mode="HTML",
        )


# ─── Buy Premium ───
async def cb_menu_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await db.get_language(_ud(update))
    await query.edit_message_text(
        t("buy_premium_title", lang),
        reply_markup=tiers_keyboard(lang),
        parse_mode="HTML",
    )


async def cb_tier_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _ud(update)
    lang = await db.get_language(uid)
    tier_key = query.data.split("_", 1)[1]
    user_data_store[uid]["pending_tier"] = tier_key
    await query.edit_message_text(
        t("buy_premium_title", lang) + "\n\n" + t("select_payment", lang, default="Select payment method:"),
        reply_markup=payment_keyboard(lang, tier_key),
        parse_mode="HTML",
    )


# ─── Telegram Stars Payment ───
async def cb_pay_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _ud(update)
    lang = await db.get_language(uid)
    tier_key = query.data.split("_", 2)[2]
    tier = config.TIERS[tier_key]

    title = f"Premium — {tier['name_en']}"
    description = f"Unlock email auditing for {tier['name_en']}."
    payload = f"stars_{tier_key}_{uid}_{int(time.time())}"
    currency = "XTR"  # Telegram Stars
    prices = [LabeledPrice(label=tier["name_en"], amount=tier["stars"])]

    await context.bot.send_invoice(
        chat_id=uid,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Not needed for Stars
        currency=currency,
        prices=prices,
        start_parameter="premium_stars",
    )


async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve all pre-checkout queries (Stars)."""
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant subscription after successful Stars payment."""
    uid = _ud(update)
    lang = await db.get_language(uid)
    payload = update.message.successful_payment.invoice_payload
    try:
        _, tier_key, user_id_str, _ = payload.split("_", 3)
        tier = config.TIERS[tier_key]
        await db.add_subscription(
            user_id=uid,
            tier=tier_key,
            duration_days=tier["duration_days"],
            payment_method="telegram_stars",
            tx_id=update.message.successful_payment.telegram_payment_charge_id,
        )
        expires = datetime.utcnow() + timedelta(days=tier["duration_days"])
        await update.message.reply_text(
            t("payment_success", lang, tier=tier["name_en"], expires=expires.strftime("%Y-%m-%d %H:%M UTC")),
            parse_mode="HTML",
        )
        if config.STICKER_SUCCESS:
            await context.bot.send_sticker(uid, config.STICKER_SUCCESS)
    except Exception as exc:
        logger.error(f"Payment post-process error: {exc}")
        await update.message.reply_text(t("error_generic", lang))


# ─── USDT TRC20 Payment ───
async def cb_pay_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _ud(update)
    lang = await db.get_language(uid)
    tier_key = query.data.split("_", 2)[2]
    tier = config.TIERS[tier_key]
    memo = f"ORD{uid}{int(time.time())}"
    amount = tier["usdt"]

    user_data_store[uid]["pending_usdt"] = {
        "tier": tier_key,
        "amount": amount,
        "memo": memo,
        "started": time.time(),
    }

    await query.edit_message_text(
        t("pay_usdt_instructions", lang,
          amount=amount,
          address=config.USDT_TRC20_DEPOSIT_ADDRESS,
          memo=memo),
        reply_markup=back_keyboard(lang),
        parse_mode="HTML",
    )

    # Start background monitor
    asyncio.create_task(_monitor_usdt_deposit(uid, context))


async def _monitor_usdt_deposit(uid: int, context: ContextTypes.DEFAULT_TYPE):
    """Poll TronGrid for USDT deposit (simplified)."""
    pending = user_data_store.get(uid, {}).get("pending_usdt")
    if not pending:
        return

    tier_key = pending["tier"]
    amount = pending["amount"]
    started = pending["started"]
    lang = await db.get_language(uid)
    headers = {}
    if config.TRONGRID_API_KEY:
        headers["TRON-PRO-API-KEY"] = config.TRONGRID_API_KEY

    poll_url = (
        f"https://api.trongrid.io/v1/accounts/{config.USDT_TRC20_DEPOSIT_ADDRESS}/transactions/trc20"
        f"?limit=20&contract_address={config.USDT_TRC20_CONTRACT}"
    )

    # Poll for up to 30 minutes
    for _ in range(60):
        await asyncio.sleep(30)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(poll_url, headers=headers, timeout=15) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    txs = data.get("data", [])
                    for tx in txs:
                        # USDT has 6 decimals
                        value = int(tx.get("value", 0)) / 1_000_000
                        to_addr = tx.get("to", "")
                        tx_time = tx.get("block_timestamp", 0) / 1000
                        if (
                            to_addr.lower() == config.USDT_TRC20_DEPOSIT_ADDRESS.lower()
                            and value >= amount * 0.99  # allow tiny slippage
                            and tx_time >= started - 60
                        ):
                            # Grant subscription
                            tier = config.TIERS[tier_key]
                            await db.add_subscription(
                                user_id=uid,
                                tier=tier_key,
                                duration_days=tier["duration_days"],
                                payment_method="usdt_trc20",
                                tx_id=tx.get("transaction_id", "unknown"),
                            )
                            expires = datetime.utcnow() + timedelta(days=tier["duration_days"])
                            await context.bot.send_message(
                                uid,
                                t("payment_success", lang,
                                  tier=tier["name_en"],
                                  expires=expires.strftime("%Y-%m-%d %H:%M UTC")),
                                parse_mode="HTML",
                            )
                            if config.STICKER_SUCCESS:
                                await context.bot.send_sticker(uid, config.STICKER_SUCCESS)
                            user_data_store[uid].pop("pending_usdt", None)
                            return
        except Exception as exc:
            logger.warning(f"USDT poll error for {uid}: {exc}")

    # Expired
    await context.bot.send_message(
        uid,
        "⏳ USDT deposit window expired. If you already sent funds, contact support.",
    )
    user_data_store[uid].pop("pending_usdt", None)


# ─── Audit Engine ───
async def cb_menu_audit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _ud(update)
    lang = await db.get_language(uid)

    # Permission check
    if not await db.is_subscribed(uid):
        await query.edit_message_text(
            t("no_subscription", lang),
            reply_markup=back_keyboard(lang),
            parse_mode="HTML",
        )
        return

    emails = user_data_store.get(uid, {}).get("emails", [])
    if not emails:
        await query.edit_message_text(
            t("no_emails_warning", lang),
            reply_markup=back_keyboard(lang),
            parse_mode="HTML",
        )
        return

    pm = user_data_store.get(uid, {}).get("proxy_manager")
    if pm is None:
        pm = ProxyManager()  # empty
        await query.message.reply_text(t("no_proxies_warning", lang))

    concurrency = user_data_store.get(uid, {}).get("concurrency", config.MAX_CONCURRENT_CHECKS)

    # Create DB session
    session_id = await db.create_session(uid, len(emails))

    # Progress message
    progress_msg = await query.message.reply_text(
        t("audit_started", lang, total=len(emails), concurrency=concurrency, timeout=config.SMTP_TIMEOUT),
        parse_mode="HTML",
    )

    if config.STICKER_PROCESSING:
        await context.bot.send_sticker(uid, config.STICKER_PROCESSING)

    # Launch background audit
    asyncio.create_task(
        _run_audit(uid, lang, emails, pm, concurrency, progress_msg, session_id, context)
    )


async def _run_audit(
    uid: int,
    lang: str,
    emails: list,
    pm: ProxyManager,
    concurrency: int,
    progress_msg,
    session_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Background task that runs the bulk audit and updates Telegram progress."""
    start_time = time.time()
    last_edit = 0
    final_stats = {}

    async def _progress(**kwargs):
        nonlocal last_edit
        now = time.time()
        if now - last_edit < config.PROGRESS_UPDATE_INTERVAL and not kwargs.get("final"):
            return
        last_edit = now
        total = kwargs["total"]
        processed = kwargs["processed"]
        percent = (processed / total * 100) if total else 0
        bar = render_progress_bar(percent)
        try:
            await progress_msg.edit_text(
                t("audit_progress", lang,
                  progress_bar=bar,
                  percent=percent,
                  valid=kwargs["valid"],
                  invalid=kwargs["invalid"],
                  grey=kwargs["grey"],
                  timeout=kwargs["timeout"],
                  speed=kwargs["speed"],
                  elapsed=fmt_seconds(kwargs["elapsed"])),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug(f"Progress edit failed: {exc}")

    auditor = BulkAuditor(pm, concurrency=concurrency, progress_callback=_progress)
    # Store auditor reference so user can cancel (optional extension)
    user_data_store.setdefault(uid, {})["auditor"] = auditor

    try:
        results = await auditor.run(emails)
    except Exception as exc:
        logger.exception("Audit crashed")
        await progress_msg.edit_text(f"❌ Audit failed: {exc}")
        return

    elapsed = time.time() - start_time

    # Count results
    valid = sum(1 for r in results if r["status"] == "Valid")
    invalid = sum(1 for r in results if r["status"] == "Invalid")
    grey = sum(1 for r in results if r["status"] == "Grey-listed/Retry")
    timeout = sum(1 for r in results if r["status"] == "Timeout")

    await db.update_session_counts(session_id, valid, invalid, grey, timeout)

    # Write result file
    result_path = config.RESULTS_DIR / f"audit_{uid}_{session_id}.txt"
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("# Email Auditor Pro Results\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}\n")
        f.write(f"# Total: {len(results)} | Valid: {valid} | Invalid: {invalid} | Grey: {grey} | Timeout: {timeout}\n")
        f.write("-" * 60 + "\n")
        for r in results:
            f.write(f"{r['status']:20} | {r['email']} | MX: {r['mx']} | {r['detail']}\n")

    await db.complete_session(session_id, str(result_path))

    # Final message
    await progress_msg.edit_text(
        t("audit_complete", lang,
          total=len(results),
          valid=valid,
          invalid=invalid,
          grey=grey,
          timeout=timeout,
          elapsed=fmt_seconds(elapsed)),
        parse_mode="HTML",
    )

    if config.STICKER_SUCCESS:
        await context.bot.send_sticker(uid, config.STICKER_SUCCESS)

    # Auto-send valid-only file
    valid_path = config.RESULTS_DIR / f"valid_{uid}_{session_id}.txt"
    with open(valid_path, "w", encoding="utf-8") as f:
        for r in results:
            if r["status"] == "Valid":
                f.write(r["email"] + "\n")
    if valid > 0:
        await context.bot.send_document(
            uid,
            document=open(valid_path, "rb"),
            caption=t("results_ready", lang),
            parse_mode="HTML",
        )


# ─── Download Results ───
async def cb_menu_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _ud(update)
    lang = await db.get_language(uid)
    session = await db.get_latest_session(uid)
    if session and session.get("result_file"):
        path = session["result_file"]
        if os.path.exists(path):
            await query.message.reply_document(
                document=open(path, "rb"),
                caption=t("results_ready", lang),
            )
            return
    await query.edit_message_text(
        t("no_results", lang),
        reply_markup=back_keyboard(lang),
        parse_mode="HTML",
    )


# ─── Admin /stats ───
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = _ud(update)
    if uid not in config.ADMIN_IDS:
        await update.message.reply_text("🚫 Admins only.")
        return
    stats = await db.get_stats()
    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\n\n"
        f"Users: <b>{stats['users']}</b>\n"
        f"Subscriptions: <b>{stats['subscriptions']}</b>\n"
        f"Audit Sessions: <b>{stats['sessions']}</b>",
        parse_mode="HTML",
    )


# ─── Main ───
def main():
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("stats", cmd_stats))

    # Callbacks
    application.add_handler(CallbackQueryHandler(cb_lang, pattern=r"^lang_"))
    application.add_handler(CallbackQueryHandler(cb_menu_main, pattern=r"^menu_main$"))
    application.add_handler(CallbackQueryHandler(cb_menu_proxies, pattern=r"^menu_proxies$"))
    application.add_handler(CallbackQueryHandler(cb_menu_emails, pattern=r"^menu_emails$"))
    application.add_handler(CallbackQueryHandler(cb_menu_audit, pattern=r"^menu_audit$"))
    application.add_handler(CallbackQueryHandler(cb_menu_sub, pattern=r"^menu_sub$"))
    application.add_handler(CallbackQueryHandler(cb_menu_buy, pattern=r"^menu_buy$"))
    application.add_handler(CallbackQueryHandler(cb_menu_download, pattern=r"^menu_download$"))
    application.add_handler(CallbackQueryHandler(cb_menu_concurrency, pattern=r"^menu_concurrency$"))
    application.add_handler(CallbackQueryHandler(cb_tier_selected, pattern=r"^tier_"))
    application.add_handler(CallbackQueryHandler(cb_pay_stars, pattern=r"^pay_stars_"))
    application.add_handler(CallbackQueryHandler(cb_pay_usdt, pattern=r"^pay_usdt_"))

    # Payments
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    # Documents & text
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Init DB
    asyncio.get_event_loop().run_until_complete(db.init())

    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
