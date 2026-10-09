import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- خادم وهمي لإرضاء منصة Render لتخطي خطأ الـ Port ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def log_message(self, format, *args):
        pass # إخفاء السجلات غير الضرورية

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

# تشغيل الخادم الوهمي في الخلفية
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- كود البوت ---
BOT_TOKEN = "8747417167:AAEFLo-4vvMvJuKwA_ZOAxKMtOtNSt8mYmA"
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
            f"بعد إتمام التحويل، يرجى إرسال إشعار التحويل للإدارة عبر الرابط:\n{ADMIN_LINK}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "سيريتيل كاش":
        msg = f"لإتمام الدفع عبر سيريتيل كاش، يرجى التواصل مع الإدارة:\n{ADMIN_LINK}"
        await update.message.reply_text(msg)

    elif text == "الرجوع للقائمة الرئيسية":
        await start(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
