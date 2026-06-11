import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google import genai

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب المفاتيح
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_KEY)

DB_FILE = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_text TEXT,
            category TEXT,
            priority TEXT
        )
    ''')
    conn.commit()
    conn.close()

# القائمة الرئيسية المدمجة (Main Menu)
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مهمة جديدة", callback_data="menu_add")],
        [InlineKeyboardButton("📋 عرض وتعديل المهام", callback_data="menu_view")],
        [InlineKeyboardButton("🧠 قسم الذكاء الاصطناعي والإنتاجية", callback_data="menu_ai")],
        [InlineKeyboardButton("🗑️ مسح كافة المهام", callback_data="menu_clear_all")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر البداية وعرض القائمة الرئيسية الاحترافية"""
    init_db()
    welcome_text = (
        f"🎯 أهلاً بك يا {update.effective_user.first_name} في نظام إدارة المهام الذكي.\n\n"
        "الرجاء اختيار أحد الخيارات الاحترافية التالية لإدارة يومك بنجاح:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة جميع ضغطات أزرار الـ Inline Keyboard"""
    query = update.callback_query
    await query.answer() # لإخفاء تأثير التحميل من الزر فوراً
    user_id = query.from_user.id

    # --- القائمة الرئيسية ---
    if query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ أولاً: قم بكتابة اسم المهمة أو عنوانها بالأسفل وأرسله:")

    elif query.data == "menu_view":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_text, category, priority FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        conn.close()

        if not tasks:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]]
            await query.edit_message_text("🎉 ممتاز! لا توجد مهام معلقة لديك حالياً.", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = "📋 **قائمة مهامك الحالية تفصيلياً:**\n\n"
            keyboard = []
            for idx, task in enumerate(tasks):
                t_id, t_text, cat, pri = task
                text += f"{idx+1}. {t_text}\n   📁 القسم: {cat} | 🚨 الأولوية: {pri}\n──────────────────\n"
                # زر حذف لكل مهمة على حدة بشكل احترافي
                keyboard.append([InlineKeyboardButton(f"✅ شطب المهمة {idx+1}", callback_data=f"delete_{t_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_ai":
        keyboard = [
            [InlineKeyboardButton("🧠 فكك لي مهمة معقدة", callback_data="ai_split")],
            [InlineKeyboardButton("💡 نصيحة سريعة لمحاربة الكسل", callback_data="ai_tips")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("🤖 **مرحباً بك في مركز الإنتاجية الذكي:**\nاختر الأداة التي ترغب بها:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_clear_all":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        keyboard = [[InlineKeyboardButton("🔙 العودة رئيسية", callback_data="go_main")]]
        await query.edit_message_text("🧹 تم مسح كافة المهام من سجلاتك بنجاح.", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- خطوات إضافة المهمة (خانات الاختيار) ---
    elif query.data.startswith("cat_"):
        category_map = {"work": "💼 العمل", "study": "📚 الدراسة", "personal": "👤 شخصي", "health": "🍏 صحة ولياقة"}
        context.user_data['temp_cat'] = category_map[query.data.split("_")[1]]
        
        # الانتقال لخانة اختيار الأولوية
        keyboard = [
            [InlineKeyboardButton("🔥 عاجل وهام جداً", callback_data="pri_high")],
            [InlineKeyboardButton("⏳ متوسط الأهمية", callback_data="pri_med")],
            [InlineKeyboardButton("💤 عادي / لاحقاً", callback_data="pri_low")]
        ]
        await query.edit_message_text("🚨 ثانياً: اختر **مستوى الأهمية والأولوية** للمهمة:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pri_"):
        priority_map = {"high": "🔥 عاجل", "med": "⏳ متوسط", "low": "💤 منخفض"}
        priority_text = priority_map[query.data.split("_")[1]]
        
        # حفظ كل شيء في قاعدة البيانات
        task_text = context.user_data.get('temp_name')
        category_text = context.user_data.get('temp_cat')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task_text, category, priority) VALUES (?, ?, ?, ?)", 
                       (user_id, task_text, category_text, priority_text))
        conn.commit()
        conn.close()

        # تنظيف الجلسة
        context.user_data.clear()

        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]]
        await query.edit_message_text(f"✅ **تمت إضافة المهمة بنجاح وعرضها في جدولك!**\n\n📌 المضمون: {task_text}\n📁 التصنيف: {category_text}\n🚨 الأولوية: {priority_text}", 
                                      parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- معالجة الحذف الفردي ---
    elif query.data.startswith("delete_"):
        task_id = int(query.data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        keyboard = [[InlineKeyboardButton("🔄 تحديث القائمة", callback_data="menu_view")]]
        await query.edit_message_text("🎉 عمل رائع! تم إنجاز المهمة وشطبها بنجاح.", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- معالجة خيارات الذكاء الاصطناعي ---
    elif query.data == "ai_split":
        context.user_data['action'] = 'waiting_for_ai_split'
        await query.edit_message_text("🤔 اكتب بالأسفل المهمة الكبيرة التي تود من Gemini تفكيكها لخطوات بسيطة:")

    elif query.data == "ai_tips":
        msg = await query.edit_message_text("⚡ جاري استدعاء نصيحة ذهبية من Gemini...")
        prompt = "أعطني نصيحة واحدة قصيرة جداً ومبتكرة وملهمة باللغة العربية لشخص يعاني من التسويف والتأجيل الآن، استخدم إيموجي مشجع."
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        
        keyboard = [[InlineKeyboardButton("🔙 العودة لقسم AI", callback_data="menu_ai")]]
        await msg.edit_text(f"💡 **نصيحة الإنتاجية اليوم:**\n\n{response.text}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- العودة للقائمة الرئيسية ---
    elif query.data == "go_main":
        await query.edit_message_text(f"🎯 مرحباً بك مجدداً يا {query.from_user.first_name}.\nاختر من الخانات بالأسفل:", reply_markup=main_menu_keyboard())

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة النصوص المكتوبة بناءً على خانة الاختيار الفعالة"""
    action = context.user_data.get('action')
    user_text = update.message.text

    if action == 'waiting_for_task_name':
        context.user_data['temp_name'] = user_text
        context.user_data['action'] = None
        
        # نقله فوراً لخانة اختيار القسم بالأزرار
        keyboard = [
            [InlineKeyboardButton("💼 العمل والتطوير", callback_data="cat_work"), InlineKeyboardButton("📚 الدراسة والتعليم", callback_data="cat_study")],
            [InlineKeyboardButton("👤 أمور شخصية", callback_data="cat_personal"), InlineKeyboardButton("🍏 صحة ورياضة", callback_data="cat_health")]
        ]
        await update.message.reply_text("📁 ممتاز، الآن حدد **قسم وتصنيف** هذه المهمة عبر الخانات التالية:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_ai_split':
        waiting_msg = await update.message.reply_text("🧠 جاري تفكيك المهمة بذكاء، انتظر ثوانٍ...")
        context.user_data['action'] = None
        
        prompt = f"قم بتفكيك هذه المهمة: '{user_text}' إلى خطة عمل سريعة جداً من 3 خطوات فقط باللغة العربية وبأسلوب عملي."
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        
        keyboard = [[InlineKeyboardButton("🔙 العودة لقسم AI", callback_data="menu_ai")]]
        await waiting_msg.edit_text(f"🧠 **خطة العمل المقترحة:**\n\n{response.text}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🤖 الرجاء اختيار أحد الأوامر عبر الأزرار التفاعلية المدمجة بالرسائل.")

def main() -> None:
    init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))

    application.run_polling()

if __name__ == '__main__':
    main()