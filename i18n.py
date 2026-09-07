"""
Email Auditor Pro — Internationalisation
All UI strings in English and Arabic for the Outlook/Hotmail email:pass checker.
"""

TEXTS = {
    "en": {
        "welcome": (
            "👋 Welcome to <b>Outlook Auditor Pro</b>\n\n"
            "<i>{disclaimer}</i>\n\n"
            "🌐 Please select your language:"
        ),
        "main_menu": (
            "📋 <b>Main Menu</b>\n\n"
            "What would you like to do today?"
        ),
        "btn_upload_proxies": "📤 Upload Proxies",
        "btn_upload_combos": "📧 Upload Combos (email:pass)",
        "btn_start_check": "🚀 Start Checking",
        "btn_subscription": "💎 My Subscription",
        "btn_buy_premium": "⭐ Buy Premium",
        "btn_download_results": "📥 Download Results",
        "btn_language": "🌐 Language",
        "btn_back": "⬅️ Back",
        "btn_set_concurrency": "🧵 Concurrency",
        "select_language": "🌐 Select your preferred language:",
        "lang_changed": "✅ Language changed to <b>English</b>.",
        "upload_proxies_prompt": (
            "📤 <b>Upload Proxies</b>\n\n"
            "Send me a <code>.txt</code> file with one proxy per line.\n"
            "Supported formats:\n"
            "• <code>ip:port</code>\n"
            "• <code>user:pass@ip:port</code>\n"
            "• <code>http://ip:port</code>\n"
            "• <code>socks5://user:pass@ip:port</code>"
        ),
        "upload_emails_prompt": (
            "📧 <b>Upload Combos (email:pass)</b>\n\n"
            "Send me a <code>.txt</code> file with one <b>email:password</b> per line.\n"
            "Example: <code>user@outlook.com:MyPassword123</code>"
        ),
        "proxies_uploaded": "⏳ Uploaded <b>{count}</b> proxies. Validating…",
        "proxies_validated": (
            "✅ <b>{valid}</b> / <b>{total}</b> proxies are <b>working</b>.\n"
            "❌ <b>{invalid}</b> failed validation."
        ),
        "emails_uploaded": "✅ Loaded <b>{count}</b> email:pass combos.",
        "no_proxies_warning": (
            "⚠️ No proxies loaded. You may continue, but Outlook may rate-limit your IP."
        ),
        "no_emails_warning": "⚠️ Please upload an email:pass list first.",
        "no_subscription": (
            "🚫 <b>No Active Subscription</b>\n\n"
            "Please purchase a plan to unlock the checking engine."
        ),
        "audit_started": (
            "🚀 <b>Checking Started!</b>\n\n"
            "📊 Total combos: <b>{total}</b>\n"
            "🧵 Concurrency: <b>{concurrency}</b>\n"
            "⏱ Timeout: <b>{timeout}s</b>"
        ),
        "audit_progress": (
            "⏳ <b>Checking in Progress…</b>\n\n"
            "{progress_bar} <b>{percent:.1f}%</b>\n\n"
            "✅ Valid: <b>{valid}</b>\n"
            "❌ Invalid: <b>{invalid}</b>\n"
            "🔒 Locked/2FA: <b>{locked}</b>\n"
            "🔄 Retry: <b>{retry}</b>\n"
            "⏱ Timeout: <b>{timeout}</b>\n\n"
            "🚀 Speed: <b>{speed:.0f}</b> / min\n"
            "⏳ Elapsed: <b>{elapsed}</b>"
        ),
        "audit_complete": (
            "🎉 <b>Checking Complete!</b>\n\n"
            "📊 Total: <b>{total}</b>\n"
            "✅ Valid: <b>{valid}</b>\n"
            "❌ Invalid: <b>{invalid}</b>\n"
            "🔒 Locked/2FA: <b>{locked}</b>\n"
            "🔄 Retry: <b>{retry}</b>\n"
            "⏱ Timeout: <b>{timeout}</b>\n\n"
            "⏱ Time taken: <b>{elapsed}</b>"
        ),
        "subscription_active": (
            "💎 <b>Your Subscription</b>\n\n"
            "Tier: <b>{tier}</b>\n"
            "Expires: <b>{expires}</b>\n"
            "Status: <b>{status}</b>"
        ),
        "subscription_expired": (
            "❌ <b>Subscription Expired</b>\n\n"
            "Renew now to keep checking."
        ),
        "buy_premium_title": "⭐ <b>Select a Plan</b>",
        "select_payment": "Select a payment method:",
        "pay_usdt_instructions": (
            "Send exactly <b>{amount} USDT</b> to:\n\n"
            "<code>{address}</code>\n\n"
            "🔑 Memo / Order ID: <b>{memo}</b>\n"
            "⏳ Bot will auto-detect your deposit within 30 min."
        ),
        "payment_success": (
            "🎉 <b>Payment Confirmed!</b>\n\n"
            "Tier: <b>{tier}</b>\n"
            "Valid until: <b>{expires}</b>"
        ),
        "results_ready": "📥 Your latest results are attached below.",
        "no_results": "⚠️ No results found. Run a check first.",
        "concurrency_prompt": "🧵 Enter concurrency limit (10–1000):",
        "concurrency_set": "✅ Concurrency set to <b>{limit}</b>.",
        "error_generic": "❌ Something went wrong. Please try again.",
        "audit_cancelled": "🛑 Check cancelled by user.",
        "sticker_processing": "⏳ Working on it…",
        "sticker_success": "🎉 Done!",
        "sticker_error": "❌ Oops!",
    },
    "ar": {
        "welcome": (
            "👋 مرحبًا بك في <b>Outlook Auditor Pro</b>\n\n"
            "<i>{disclaimer}</i>\n\n"
            "🌐 الرجاء اختيار لغتك:"
        ),
        "main_menu": (
            "📋 <b>القائمة الرئيسية</b>\n\n"
            "ماذا تريد أن تفعل اليوم؟"
        ),
        "btn_upload_proxies": "📤 رفع البروكسيات",
        "btn_upload_combos": "📧 رفع الأزواج (email:pass)",
        "btn_start_check": "🚀 بدء الفحص",
        "btn_subscription": "💎 اشتراكي",
        "btn_buy_premium": "⭐ شراء بريميوم",
        "btn_download_results": "📥 تحميل النتائج",
        "btn_language": "🌐 اللغة",
        "btn_back": "⬅️ رجوع",
        "btn_set_concurrency": "🧵 التزامن",
        "select_language": "🌐 اختر لغتك المفضلة:",
        "lang_changed": "✅ تم تغيير اللغة إلى <b>العربية</b>.",
        "upload_proxies_prompt": (
            "📤 <b>رفع البروكسيات</b>\n\n"
            "أرسل ملف <code>.txt</code> يحتوي على بروكسي واحد في كل سطر.\n"
            "الصيغ المدعومة:\n"
            "• <code>ip:port</code>\n"
            "• <code>user:pass@ip:port</code>\n"
            "• <code>http://ip:port</code>\n"
            "• <code>socks5://user:pass@ip:port</code>"
        ),
        "upload_emails_prompt": (
            "📧 <b>رفع الأزواج (email:pass)</b>\n\n"
            "أرسل ملف <code>.txt</code> يحتوي على <b>بريد:كلمة مرور</b> في كل سطر.\n"
            "مثال: <code>user@outlook.com:MyPassword123</code>"
        ),
        "proxies_uploaded": "⏳ تم رفع <b>{count}</b> بروكسي. جاري التحقق…",
        "proxies_validated": (
            "✅ <b>{valid}</b> / <b>{total}</b> بروكسي يعمل.\n"
            "❌ <b>{invalid}</b> فشل التحقق."
        ),
        "emails_uploaded": "✅ تم تحميل <b>{count}</b> زوج بريد:كلمة مرور.",
        "no_proxies_warning": (
            "⚠️ لم يتم تحميل بروكسيات. يمكنك المتابعة، لكن Outlook قد يحد من IP الخاص بك."
        ),
        "no_emails_warning": "⚠️ الرجاء رفع قائمة الأزواج (email:pass) أولاً.",
        "no_subscription": (
            "🚫 <b>لا يوجد اشتراك نشط</b>\n\n"
            "يرجى شراء خطة لفتح محرك الفحص."
        ),
        "audit_started": (
            "🚀 <b>بدأ الفحص!</b>\n\n"
            "📊 إجمالي الأزواج: <b>{total}</b>\n"
            "🧵 التزامن: <b>{concurrency}</b>\n"
            "⏱ المهلة: <b>{timeout}ث</b>"
        ),
        "audit_progress": (
            "⏳ <b>الفحص جارٍ…</b>\n\n"
            "{progress_bar} <b>{percent:.1f}%</b>\n\n"
            "✅ صالح: <b>{valid}</b>\n"
            "❌ غير صالح: <b>{invalid}</b>\n"
            "🔒 مقفل/تحقق: <b>{locked}</b>\n"
            "🔄 إعادة محاولة: <b>{retry}</b>\n"
            "⏱ انتهى الوقت: <b>{timeout}</b>\n\n"
            "🚀 السرعة: <b>{speed:.0f}</b> / دقيقة\n"
            "⏳ المنقضي: <b>{elapsed}</b>"
        ),
        "audit_complete": (
            "🎉 <b>اكتمل الفحص!</b>\n\n"
            "📊 الإجمالي: <b>{total}</b>\n"
            "✅ صالح: <b>{valid}</b>\n"
            "❌ غير صالح: <b>{invalid}</b>\n"
            "🔒 مقفل/تحقق: <b>{locked}</b>\n"
            "🔄 إعادة محاولة: <b>{retry}</b>\n"
            "⏱ انتهى الوقت: <b>{timeout}</b>\n\n"
            "⏱ المدة: <b>{elapsed}</b>"
        ),
        "subscription_active": (
            "💎 <b>اشتراكك</b>\n\n"
            "الخطة: <b>{tier}</b>\n"
            "ينتهي: <b>{expires}</b>\n"
            "الحالة: <b>{status}</b>"
        ),
        "subscription_expired": (
            "❌ <b>انتهى الاشتراك</b>\n\n"
            "جدد الآن للاستمرار في الفحص."
        ),
        "buy_premium_title": "⭐ <b>اختر خطة</b>",
        "select_payment": "اختر طريقة الدفع:",
        "pay_usdt_instructions": (
            "أرسل بالضبط <b>{amount} USDT</b> إلى:\n\n"
            "<code>{address}</code>\n\n"
            "🔑 المذكرة / رقم الطلب: <b>{memo}</b>\n"
            "⏳ البوت سيكتشف الإيداع تلقائيًا خلال 30 دقيقة."
        ),
        "payment_success": (
            "🎉 <b>تم تأكيد الدفع!</b>\n\n"
            "الخطة: <b>{tier}</b>\n"
            "صالح حتى: <b>{expires}</b>"
        ),
        "results_ready": "📥 نتائج الفحص الأخيرة مرفقة أدناه.",
        "no_results": "⚠️ لا توجد نتائج. قم بتشغيل فحص أولاً.",
        "concurrency_prompt": "🧵 أدخل حد التزامن (10–1000):",
        "concurrency_set": "✅ تم تعيين التزامن على <b>{limit}</b>.",
        "error_generic": "❌ حدث خطأ ما. يرجى المحاولة مرة أخرى.",
        "audit_cancelled": "🛑 تم إلغاء الفحص من قبل المستخدم.",
        "sticker_processing": "⏳ جاري العمل…",
        "sticker_success": "🎉 تم!",
        "sticker_error": "❌ عذرًا!",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Fetch translated string and format it with kwargs."""
    return TEXTS.get(lang, TEXTS["en"]).get(key, key).format(**kwargs)
