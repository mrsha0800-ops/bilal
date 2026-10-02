from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler

# المراحل الخاصة بمحادثة الشحن
OPERATION_ID, AMOUNT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # إرسال الرسالة الترحيبية وعرض الأزرار
    keyboard = [
        [KeyboardButton("سيريتيل كاش")],
        [KeyboardButton("شام كاش")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="أهلاً بك في خدمة الشحن. كيف يمكنني مساعدتك اليوم؟",
        reply_markup=reply_markup
    )

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text in ["سيريتيل كاش", "شام كاش"]:
        await start_recharge(update, context)
    else:
        reply_text = f"أهلاً {update.effective_user.first_name}، يرجى اختيار الخدمة المطلوبة أولاً."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)

async def start_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="يرجى إرسال رقم العملية الخاص بالتحويل.",
        reply_markup=ReplyKeyboardRemove()
    )
    return OPERATION_ID

async def get_operation_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # حفظ رقم العملية
    context.user_data['operation_id'] = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="حفظ رقم العملية. الآن، يرجى إرسال كمية الشحن."
    )
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text
    operation_id = context.user_data.get('operation_id')
    amount = context.user_data.get('amount')
    confirm_text = f"شكراً لك. تفاصيل الطلب:\n- رقم العملية: {operation_id}\n- الكمية: {amount}"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=confirm_text
    )
    # إعادة تعيين البيانات وحالة المحادثة
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="تم إلغاء العملية."
    )
    return ConversationHandler.END

if __name__ == '__main__':
    TOKEN = '8842428587:AAEWfrQitnF08ZDA1P2NfzoR8sU1aY9yG_0'
    application = ApplicationBuilder().token(TOKEN).build()
    recharge_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text("سيريتيل كاش") | filters.Text("شام كاش"), start_recharge)
        ],
        states={
            OPERATION_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_operation_id)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(recharge_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    application.run_polling()
