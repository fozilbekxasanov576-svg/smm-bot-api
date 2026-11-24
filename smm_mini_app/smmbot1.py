import telebot
import sqlite3
import time
import threading
import uuid
from datetime import datetime
from telebot import types
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

BOT_TOKEN = "9009367032:AAHdL3K6EG0Zna4rElYDct1T2E6VH41ZnNU"
ADMIN_IDS = []
ADMIN_USERNAME = "@Xasan0v"
WEBAPP_URL = "https://sizning-veb-saytingiz.com" # Vercel'dan olgan link

bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance REAL DEFAULT 0, total_spent REAL DEFAULT 0, referrer_id INTEGER, referral_balance REAL DEFAULT 0, joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_banned BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, price_per_1000 REAL, min_order INTEGER DEFAULT 100, max_order INTEGER DEFAULT 100000, description TEXT, is_active BOOLEAN DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_number TEXT UNIQUE, user_id INTEGER, service_id INTEGER, link TEXT, quantity INTEGER, total_price REAL, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, payment_id TEXT UNIQUE, user_id INTEGER, amount REAL, method TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    services = [('👥 Instagram Followers', 'Instagram', 15000, 100, 100000, 'Premium sifatli obunachilar'), ('❤️ Instagram Likes', 'Instagram', 8000, 100, 50000, 'Post uchun layklar'), ('👀 Instagram Views', 'Instagram', 3000, 1000, 1000000, 'Video korishlar'), ('👥 Telegram Members', 'Telegram', 20000, 100, 100000, 'Kanal azolari'), ('👀 Telegram Views', 'Telegram', 5000, 1000, 1000000, 'Post korishlar'), ('👀 YouTube Views', 'YouTube', 5000, 1000, 1000000, 'Video korishlar'), ('👥 YouTube Subscribers', 'YouTube', 45000, 50, 50000, 'Kanal obunachilari'), ('👥 TikTok Followers', 'TikTok', 12000, 100, 100000, 'TikTok obunachilari'), ('❤️ TikTok Likes', 'TikTok', 8000, 100, 100000, 'Video layklari'), ('👀 TikTok Views', 'TikTok', 3000, 1000, 1000000, 'Video korishlar'), ('👍 Facebook Likes', 'Facebook', 10000, 100, 50000, 'Sahifa layklari'), ('👥 Twitter Followers', 'Twitter', 20000, 100, 50000, 'Twitter obunachilari')]
    c.executemany('INSERT OR IGNORE INTO services (name, category, price_per_1000, min_order, max_order, description) VALUES (?, ?, ?, ?, ?, ?)', services)
    conn.commit()
    return conn

db = init_db()

def get_user(user_id):
    c = db.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return c.fetchone()

def create_user(user_id, username, first_name, referrer_id=None):
    c = db.cursor()
    try:
        c.execute('INSERT INTO users (user_id, username, first_name, referrer_id) VALUES (?, ?, ?, ?)', (user_id, username, first_name, referrer_id))
        if referrer_id: c.execute('UPDATE users SET referral_balance = referral_balance + 1000 WHERE user_id = ?', (referrer_id,))
        db.commit()
        return True
    except: return False

def main_menu():
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    webapp_btn = types.KeyboardButton(text="🚀 Ilovani ochish", web_app=types.WebAppInfo(url=WEBAPP_URL))
    kb.add(webapp_btn)
    kb.add(types.KeyboardButton("🛒 Xizmatlar"), types.KeyboardButton("💰 Balans"), types.KeyboardButton("📊 Buyurtmalarim"), types.KeyboardButton("👥 Referal"), types.KeyboardButton("💳 Tolov"), types.KeyboardButton("ℹ️ Profil"), types.KeyboardButton("💬 Yordam"), types.KeyboardButton("📞 Admin"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    user = get_user(uid)
    if not user: create_user(uid, message.from_user.username or "", message.from_user.first_name or "User")
    
    kb_inline = types.InlineKeyboardMarkup()
    kb_inline.add(types.InlineKeyboardButton("🚀 Ilovani ochish", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    
    txt = f"🎉 Assalomu alaykum, {message.from_user.first_name}!\n\n🚀 SMM Pro Bot - zamonaviy ilova!\n\nPastdagi tugma orqali ilovani oching."
    bot.send_message(uid, txt, reply_markup=main_menu())
    bot.send_message(uid, "👇 Ilovani ochish uchun bosing:", reply_markup=kb_inline)

@bot.message_handler(commands=['setapp'])
def set_app_cmd(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        url = message.text.split()[1]
        bot.set_chat_menu_button(chat_id=message.from_user.id, menu_button=types.MenuButtonWebApp(type="web_app", text="🚀 Ilovani ochish", web_app=types.WebAppInfo(url=url)))
        bot.send_message(message.from_user.id, f"✅ Web App sozlandi: {url}")
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Xato: {e}")

# Qolgan handlerlar (xizmatlar, balans va h.k.) o'zgarishsiz qoladi...

if __name__ == "__main__":
    print("🤖 SMM Pro Bot ishga tushmoqda...")
    while True:
        try: bot.polling(none_stop=True, timeout=60)
        except Exception as e: logger.error(f"Bot error: {e}"); time.sleep(15)
