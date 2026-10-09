from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# بيانات البوت والمسؤول
BOT_TOKEN = "8747417167:AAEvOBVFAW0bb_hkLXG94LyuuQpSTGB6Qcc"
ADMIN_LINK = "https://t.me/srheiwk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["مكالمات فيديو"],
        ["حجز واقعي"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('أهلاً بك! اختر من الأزرار أدناه:', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "مكالمات فيديو":
        keyboard = [
            ["تحويل شام كاش"],
            ["سيريتيل كاش"],
            ["الرجوع للقائمة الرئيسية"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('اختر طريقة الدفع:', reply_markup=reply_markup)
        
    elif text == "حجز واقعي":
        msg = f"لإتمام الحجز الواقعي، يرجى التواصل مباشرة مع الإدارة عبر الرابط التالي:\n{ADMIN_LINK}"
        await update.message.reply_text(msg)
        
    elif text == "تحويل شام كاش":
        sham_code = "80b363fb29781a600ed48c02f6fc77fb"
        msg = (
            f"رمز تحويل شام كاش:\n`{sham_code}`\n\n"
            f"بعد إتمام التحويل، ي
