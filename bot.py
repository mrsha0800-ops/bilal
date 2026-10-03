import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ----------------- الإعدادات -----------------
TOKEN = "8951262809:AAGEKKWwo2wFSlld0wpHzDCF98Ek96BeLEg"

# تم وضع الأيدي الخاص بك هنا لتصلك إشعارات الشحن
ADMIN_CHAT_ID = 8453606067  

# حالات المحادثة (Steps) لعملية الشحن
WAIT_OP_NUMBER, WAIT_AMOUNT = range(2)

# ----------------- دالة البداية -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # النص المماثل للصورة
    text = (
        "❞ قائمة الخيارات الرئيسية ❝\n\n"
        "💰 الرصيد الحالي: 0 SYP\n"
        f"🆔 أيدي حسابك: {user.id}"
    )

    # تصميم الأزرار تماماً كما في صورتك
    keyboard = [
        [InlineKeyboardButton("⚡️ حساب اشانسي وشحنه", callback_data="dummy")],
        [
            InlineKeyboardButton("📤 شحن رصيد في البوت", callback_data="charge_balance"),
            InlineKeyboardButton("📥 سحب رصيد من البوت", callback_data="dummy")
        ],
        [
            InlineKeyboardButton("🏆 كود جائزة", callback_data="dummy"),
            InlineKeyboardButton("🎁 إهداء صديق", callback_data="dummy")
        ],
        [InlineKeyboardButton("💰 الإحالات", callback_data="dummy")],
        [
            InlineKeyboardButton("💬 إرسال رسالة للدعم", callback_data="dummy"),
            InlineKeyboardButton("🗂 السجلات", callback_data="dummy")
        ],
        [
            InlineKeyboardButton("↗️ اشانسي", callback_data="dummy"),
            InlineKeyboardButton("🎮 للتسلية", callback_data="dummy")
        ],
        [InlineKeyboardButton("💸 استرداد آخر طلب سحب", callback_data="dummy")],
        [
            InlineKeyboardButton("⚠️ شروط الاستخدام", callback_data="dummy"),
            InlineKeyboardButton("🎁 العروض النشطة", callback_data="dummy")
        ],
        [InlineKeyboardButton("🎉 عجلة الفرصة", callback_data="dummy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # التحقق مما إذا كان الطلب من رسالة جديدة أو رجوع من زر
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

# ----------------- عملية الشحن -----------------

# 1. عند الضغط على زر الشحن
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

# 2. استقبال رقم العملية
async def receive_op_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['op_number'] = update.message.text
    
    msg = "ممتاز! 👏\nالآن **أرسل كمية المبلغ** الذي قمت بتحويله (بالليرة السورية):"
    await update.message.reply_text(msg, parse_mode="Markdown")
    return WAIT_AMOUNT

# 3. استقبال المبلغ وإرسال الإشعار للإدارة
async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text
    op_number = context.user_data.get('op_number')
    user = update.effective_user

    # رسالة تأكيد للمستخدم
    await update.message.reply_text("✅ **تم استلام طلبك بنجاح!**\nتم إرسال التفاصيل للإدارة وسيتم إضافة الرصيد لحسابك بعد التحقق.", parse_mode="Markdown")

    # تجهيز الإشعار الذي سيصل إليك كأدمن
    admin_msg = (
        "🔔 **طلب شحن رصيد جديد** 🔔\n\n"
        f"👤 المستخدم: {user.first_name} (@{user.username if user.username else 'لا يوجد معرف'})\n"
        f"🆔 أيدي المستخدم: `{user.id}`\n\n"
        f"🔢 رقم العملية: `{op_number}`\n"
        f"💰 المبلغ المحول: `{amount}` SYP"
    )
    
    try:
        # إرسال الإشعار إليك
        if ADMIN_CHAT_ID != 0:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown")
        else:
            print("تنبيه: لم تقم بوضع ADMIN_CHAT_ID، لذلك لم تصلك رسالة الإشعار.")
    except Exception as e:
        print(f"حدث خطأ أثناء إرسال الإشعار إليك: {e}")

    # إرجاع المستخدم للقائمة الرئيسية
    await start(update, context)
    return ConversationHandler.END

# 4. إلغاء العملية
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء عملية الشحن.")
    await start(update, context)
    return ConversationHandler.END

# 5. استجابة الأزرار غير المبرمجة بعد
async def dummy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("هذا الزر قيد التطوير حالياً! ⏳", show_alert=True)

# ----------------- التشغيل -----------------
def main():
    # بناء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # نظام المحادثة لعملية الشحن
    charge_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(charge_start, pattern='^charge_balance$')],
        states={
            WAIT_OP_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_op_number)],
            WAIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # ربط الأوامر
    app.add_handler(CommandHandler('start', start))
    app.add_handler(charge_conv_handler)
    app.add_handler(CallbackQueryHandler(dummy_button, pattern='^dummy$'))

    print("البوت يعمل الآن... اضغط Ctrl+C للإيقاف.")
    # تشغيل البوت
    app.run_polling()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    main()
