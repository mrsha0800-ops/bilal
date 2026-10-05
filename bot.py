import logging
import sqlite3
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

# ----------------- الإعدادات -----------------
TOKEN = "8951262809:AAGEKKWwo2wFSlld0wpHzDCF98Ek96BeLEg"  # ضع توكين البوت الجديد هنا
ADMIN_CHAT_ID = 0                 # ضع أيدي حسابك الرقمي هنا

# حالات المحادثة (Conversation States)
WAIT_OP_NUMBER, WAIT_AMOUNT = range(2)
WAIT_REDEEM_CODE = 2
WAIT_TRANSFER_ID, WAIT_TRANSFER_AMOUNT = range(3, 5)
WAIT_SUPPORT_MSG = 5


# ----------------- التعامل مع قاعدة البيانات -----------------
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # جدول المستخدمين والأرصدة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    # جدول أكواد الهدايا
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
    return WAIT_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip()
    if not text_input.isdigit():
        await update.message.reply_text("⚠️ يرجى كتابة المبلغ بالأرقام فقط:")
        return WAIT_AMOUNT

    amount = int(text_input)
    op_number = context.user_data.get('op_number')
    user = update.effective_user

    await update.message.reply_text("✅ **تم استلام طلبك بنجاح!**\nسيتم مراجعة الطلب وإضافة الرصيد قريباً.", parse_mode="Markdown")

    admin_keyboard = [[
        InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{user.id}_{amount}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user.id}_{amount}")
    ]]
    admin_msg = (
        "🔔 **طلب شحن رصيد جديد** 🔔\n\n"
        f"👤 المستخدم: {user.first_name} (@{user.username or 'لا يوجد'})\n"
        f"🆔 أيدي: `{user.id}`\n"
        f"🔢 رقم العملية: `{op_number}`\n"
        f"💰 المبلغ: `{amount:,}` SYP"
    )
    if ADMIN_CHAT_ID != 0:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(admin_keyboard), parse_mode="Markdown")

    await start(update, context)
    return ConversationHandler.END


# ----------------- 2. كود الجائزة -----------------
async def redeem_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎁 **أدخل كود الجائزة الخاص بك هنا:**", parse_mode="Markdown")
    return WAIT_REDEEM_CODE

async def process_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_input = update.message.text.strip()
    user_id = update.effective_user.id

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT amount, is_used FROM promo_codes WHERE code = ?", (code_input,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("❌ **الكود غير صحيح أو غير موجود.**", parse_mode="Markdown")
    elif row[1] == 1:
        await update.message.reply_text("⚠️ **هذا الكود تم استخدامه من قبل!**", parse_mode="Markdown")
    else:
        amount = row[0]
        cursor.execute("UPDATE promo_codes SET is_used = 1 WHERE code = ?", (code_input,))
        conn.commit()
        update_balance(user_id, amount)
        await update.message.reply_text(f"🎉 **مبروك!** تم إضافة `{amount:,} SYP` إلى رصيدك بنجاح.", parse_mode="Markdown")

    conn.close()
    await start(update, context)
    return ConversationHandler.END

# أمر خاص للأدمن لإنشاء كود: /make_code CODE AMOUNT
async def admin_make_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    try:
        code = context.args[0]
        amount = int(context.args[1])
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO promo_codes (code, amount) VALUES (?, ?)", (code, amount))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ تم إنشاء الكود `{code}` بمبلغ `{amount:,} SYP` بنجاح!", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ الصيغة خاطئة. الاستخدام: `/make_code CODE AMOUNT`", parse_mode="Markdown")


# ----------------- 3. إهداء صديق (تحويل رصيد) -----------------
async def transfer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👤 **أرسل أيدي (ID) الحساب الذي تريد تحويل الرصيد إليه:**", parse_mode="Markdown")
    return WAIT_TRANSFER_ID

async def receive_transfer_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ يرجى إدخال أيدي رقمي صحيح:")
        return WAIT_TRANSFER_ID

    target_id = int(text)
    if target_id == update.effective_user.id:
        await update.message.reply_text("❌ لا يمكنك تحويل الرصيد لنفسك!")
        return WAIT_TRANSFER_ID

    context.user_data['target_id'] = target_id
    await update.message.reply_text("💸 **أدخل المبلغ الذي تريد تحويله:**", parse_mode="Markdown")
    return WAIT_TRANSFER_AMOUNT

async def receive_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ يرجى إدخال المبلغ بالأرقام فقط:")
        return WAIT_TRANSFER_AMOUNT

    amount = int(text)
    user_id = update.effective_user.id
    current_balance = get_balance(user_id)

    if amount > current_balance or amount <= 0:
        await update.message.reply_text("❌ **رصيدك غير كافٍ لإتمام العملية!**", parse_mode="Markdown")
    else:
        target_id = context.user_data['target_id']
        update_balance(user_id, -amount)
        update_balance(target_id, amount)

        await update.message.reply_text(f"✅ **تم تحويل `{amount:,} SYP` بنجاح إلى الحساب `{target_id}`.**", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎁 **وصلتك هدية!**\nقام المستخدم `{user_id}` بتحويل `{amount:,} SYP` إلى حسابك.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await start(update, context)
    return ConversationHandler.END


# ----------------- 4. إرسال رسالة للدعم -----------------
async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💬 **اكتب رسالتك وسنكتفي بإيصالها إلى فريق الدعم الفني:**", parse_mode="Markdown")
    return WAIT_SUPPORT_MSG

async def receive_support_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user = update.effective_user

    await update.message.reply_text("✅ **تم إرسال رسالتك للدعم بنجاح!** سيتواصل معك فريقنا قريباً.")

    if ADMIN_CHAT_ID != 0:
        support_notification = (
            "📩 **رسالة دعم جديدة**\n\n"
            f"👤 من: {user.first_name} (@{user.username or 'لا يوجد'})\n"
            f"🆔 أيدي: `{user.id}`\n\n"
            f"📝 الرسالة:\n{user_msg}"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=support_notification, parse_mode="Markdown")

    await start(update, context)
    return ConversationHandler.END


# ----------------- معالجات الأزرار العامة -----------------
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, target_user_id, amount = query.data.split('_')
    target_user_id, amount = int(target_user_id), int(amount)

    if action == "approve":
        update_balance(target_user_id, amount)
        await query.edit_message_text(f"{query.message.text}\n\n✅ **تمت الموافقة وشحن {amount:,} SYP بنجاح.**", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_user_id, text=f"🎉 **تمت الموافقة على طلب الشحن!**\nتم إضافة `{amount:,} SYP` لحسابك.", parse_mode="Markdown")
        except Exception:
            pass
    elif action == "reject":
        await query.edit_message_text(f"{query.message.text}\n\n❌ **تم رفض الطلب.**", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_user_id, text="❌ **تم رفض طلب شحن الرصيد الخاص بك.**", parse_mode="Markdown")
        except Exception:
            pass

async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "terms":
        text = "⚠️ **شروط الاستخدام:**\n1. يمنع التحويلات الوهمية.\n2. التأكد من رقم العملية قبل الإرسال."
    elif query.data == "offers":
        text = "🎁 **العروض النشطة:**\nاشحن بقيمة 100,000 SYP واحصل على 10% رصيد إضافي مجاناً!"
    
    await query.message.reply_text(text, parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    await start(update, context)
    return ConversationHandler.END

async def dummy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("هذا الزر قيد التطوير حالياً! ⏳", show_alert=True)


# ----------------- التشغيل -----------------
def main():
    init_db()  # تهيئة قاعدة البيانات

    app = ApplicationBuilder().token(TOKEN).build()

    # محادثة الشحن
    charge_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(charge_start, pattern='^charge_balance$')],
        states={
            WAIT_OP_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_op_number)],
            WAIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # محادثة كود الجائزة
    redeem_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(redeem_code_start, pattern='^redeem_code_start$')],
        states={WAIT_REDEEM_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_redeem_code)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # محادثة تحويل الرصيد
    transfer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(transfer_start, pattern='^transfer_start$')],
        states={
            WAIT_TRANSFER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_transfer_id)],
            WAIT_TRANSFER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_transfer_amount)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # محادثة الدعم
    support_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(support_start, pattern='^support_start$')],
        states={WAIT_SUPPORT_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_support_msg)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # التسجيل في الهاندلر
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('make_code', admin_make_code))
    app.add_handler(charge_conv)
    app.add_handler(redeem_conv)
    app.add_handler(transfer_conv)
    app.add_handler(support_conv)
    app.add_handler(CallbackQueryHandler(handle_admin_action, pattern='^(approve|reject)_'))
    app.add_handler(CallbackQueryHandler(show_info, pattern='^(terms|offers)$'))
    app.add_handler(CallbackQueryHandler(dummy_button, pattern='^dummy$'))

    print("البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    main()
