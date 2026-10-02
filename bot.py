from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="مرحباً! أنا بوت للرد التلقائي وخدمات الشحن. كيف يمكنني مساعدتك اليوم؟"
    )

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_text = f"أهلاً {update.effective_user.first_name}، لقد تلقيت رسالتك: '{update.message.text}'. سأرد عليك قريباً."
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_text
    )

async def recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="لشحن رصيدك، يرجى إرسال المبلغ إلى المعرف التالي: @PaymentAdmin، ثم أرسل صورة الإيصال."
    )

if __name__ == '__main__':
    TOKEN = '8842428587:AAEwfrQitnFO8ZDA1P2NfZ0NFbhtxMs0l-k'
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    recharge_handler = CommandHandler('recharge', recharge)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), auto_reply)

    application.add_handler(start_handler)
    application.add_handler(recharge_handler)
    application.add_handler(echo_handler)
    
    application.run_polling()
