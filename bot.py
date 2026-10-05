import logging
import os
import sqlite3
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ----------------- خادم الويب الخاص بـ Render -----------------
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is active and running!"

def run_web_server():
    # Render يحدد المنفذ تلقائياً عبر متغير البيئة PORT
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()


# ----------------- الإعدادات -----------------
# يمكنك وضع التوكن والأيدي هنا أو ضبطهما عبر متغيرات البيئة في Render
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_NEW_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 0))

# حالات المحادثة (Conversation States)
WAIT_OP_NUMBER, WAIT_AMOUNT = range(2)
WAIT_REDEEM_CODE = 2
WAIT_TRANSFER_ID, WAIT_TRANSFER_AMOUNT = range(3, 5)
WAIT_SUPPORT_MSG = 5


# ----------------- التعامل مع قاعدة البيانات -----------------
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            amount INTEGER,
            is_used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def update_balance(user_id: int, amount: int):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, balance) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
    """, (user_id, amount, amount))
    conn.commit()
    conn.close()


# ----------------- القائمة الرئيسية -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_balance(user.id)
    
    text = (
        "❞ قائمة الخيارات الرئيسية ❝\n\n"
        f"💰 الرصيد الحالي: {balance:,} SYP\n"
        f"🆔 أيدي حسابك: `{user.id}`"
    )

    keyboard = [
        [InlineKeyboardButton("⚡️ حساب اشانسي وشحنه", callback_data="dummy")],
        [
            InlineKeyboardButton("📤 شحن رصيد في البوت", callback_data="charge_balance"),
            InlineKeyboardButton("📥 سحب رصيد من البوت", callback_data="dummy")
        ],
        [
            InlineKeyboardButton("🏆 كود جائزة", callback_data="redeem_code_start"),
            InlineKeyboardButton("🎁 إهداء صديق", callback_data="transfer_start")
        ],
        [InlineKeyboardButton("💰 الإحالات", callback_data="dummy")],
        [
            InlineKeyboardButton("💬 إرسال رسالة للدعم", callback_data="support_start"),
            InlineKeyboardButton("🗂 السجلات", callback_data="dummy")
        ],
        [
            InlineKeyboardButton("↗️ اشانسي", callback_data="dummy"),
            InlineKeyboardButton("🎮 للتسلية", callback_data="dummy")
        ],
        [InlineKeyboardButton("💸 استرداد آخر طلب سحب", callback_data="dummy")],
        [
            InlineKeyboardButton("⚠️ شروط الاستخدام", callback_data="terms"),
            InlineKeyboardButton("🎁 العروض النشطة", callback_data="offers")
        ],
        [InlineKeyboardButton("🎉 عجلة الفرصة", callback_data="dummy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


# ----------------- 1. عملية الشحن -----------------
async def charge_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg = (
        "لشحن رصيدك، يرجى تحويل المبلغ إلى أحد الحسابات التالية:\n\n"
        "🔴 **سيريتيل كاش:** `17507658`\n"
        "🔵 **كود شام:** `d94c44b3b6df46a781c7c60b34649c73`\n\n"
        "👇 **بعد إتمام التحويل، أرسل لي رقم العملية هنا في الدردشة:**"
    )
    await query.message.reply_text(msg, parse_mode="Markdown")
    return WAIT_OP_NUMBER

async def receive_op_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['op_number'] = update.message.text
    msg = "ممتاز! 👏\nالآن **أرسل كمية المبلغ** الذي قمت بتحويله (بالليرة السورية - أرقام فقط):"
    await update.message.reply_text(msg, parse_mode="Markdown")
    return
