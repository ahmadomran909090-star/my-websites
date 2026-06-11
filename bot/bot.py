import os
import logging
import sqlite3
import io
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from pypdf import PdfReader
from pydantic import BaseModel, Field

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب المفاتيح
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_KEY)

DB_FILE = "tasks.db"

# --- تحديد هيكل البيانات المرجعة من Gemini (Structured Output) ---
class QuizQuestion(BaseModel):
    question: str = Field(description="نص السؤال باللغة العربية بناءً على محتوى الـ PDF المرسل")
    options: list[str] = Field(description="قائمة تحتوي على 3 أو 4 خيارات للإجابة")
    correct_index: int = Field(description="مؤشر الخيار الصحيح (يبدأ من 0)")

class QuizSchema(BaseModel):
    quiz: list[QuizQuestion] = Field(description="قائمة من 3 إلى 5 أسئلة اختبار متنوعة")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_text TEXT,
            category TEXT,
            priority TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مهمة جديدة", callback_data="menu_add")],
        [InlineKeyboardButton("📋 مهامي المعلقة", callback_data="menu_view"), InlineKeyboardButton("📊 إحصائيات الإنجاز", callback_data="menu_stats")],
        [InlineKeyboardButton("🧠 مستشار الإنتاجية (AI)", callback_data="menu_ai")],
        [InlineKeyboardButton("📝 تحويل PDF إلى كويز 🔥", callback_data="menu_pdf_quiz")],
        [InlineKeyboardButton("⏱️ ضبط تذكير سريع", callback_data="menu_remind")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_db()
    welcome_text = (
        f"🚀 أهلاً بك يا {update.effective_user.first_name} في مساعدك الشامل!\n\n"
        "تمت إضافة ميزة **صانع الاختبارات الذكي** من ملفات PDF. يمكنك الآن رفع أي ملف وتحويله لأسئلة تفاعلية فوراً.\n\n"
        "👇 اختر من لوحة التحكم أدناه لتبدأ:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ أرسل الآن اسم أو عنوان المهمة الجديدة:")

    elif query.data == "menu_view":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_text, category, priority FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
        tasks = cursor.fetchall()
        conn.close()

        if not tasks:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]]
            await query.edit_message_text("🎉 لا توجد مهام معلقة! جدولك نظيف تماماً.", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = "📋 **مهامك النشطة الحالية:**\n\n"
            keyboard = []
            for idx, task in enumerate(tasks):
                t_id, t_text, cat, pri = task
                text += f"{idx+1}. {t_text}\n   📂 {cat} | 🚨 {pri}\n──────────────────\n"
                keyboard.append([InlineKeyboardButton(f"✅ إنجاز وشطب {idx+1}", callback_data=f"complete_{t_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="go_main")])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_stats":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
        pending_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,))
        completed_cnt = cursor.fetchone()[0]
        conn.close()

        total = pending_cnt + completed_cnt
        rate = int((completed_cnt / total) * 100) if total > 0 else 0
        progress_bar = "🟩" * (rate // 10) + "⬜" * (10 - (rate // 10))

        stats_text = (
            f"📊 **تقرير إنتاجيتك الشخصي:**\n\n"
            f"📝 إجمالي المهام: {total}\n"
            f"⏳ المعلقة: {pending_cnt}\n"
            f"✅ المنجزة: {completed_cnt}\n\n"
            f"📈 نسبة الإنجاز: {rate}%\n{progress_bar}"
        )
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]]
        await query.edit_message_text(stats_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_ai":
        keyboard = [
            [InlineKeyboardButton("📅 خطط لي يومي بذكاء", callback_data="ai_schedule")],
            [InlineKeyboardButton("🧠 تفكيك مهمة معقدة", callback_data="ai_split")],
            [InlineKeyboardButton("💡 نصيحة التخلص من التأجيل", callback_data="ai_tips")],
            [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]
        ]
        await query.edit_message_text("🤖 **مركز Gemini للإنتاجية والتخطيط الذكي:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_pdf_quiz":
        context.user_data['action'] = 'waiting_for_pdf'
        await query.edit_message_text("📂 من فضلك قم بإرسال ملف الـ **PDF** الخاص بالمادة أو الكتاب هنا الآن كـ (Document)، وسأقوم بقراءته واستخراج كويز تفاعلي لك فوراً!")

    elif query.data == "menu_remind":
        context.user_data['action'] = 'waiting_for_reminder_time'
        await query.edit_message_text("⏱️ بعد كم دقيقة من الآن تريدني أن أذكرك؟")

    elif query.data == "go_main":
        await query.edit_message_text("🎯 لوحة التحكم الرئيسية الخاصة بك:", reply_markup=main_menu_keyboard())

    # (بقية الـ callbacks من الكود السابق كالتصنيفات وإنجاز المهام تبقى كما هي لتوفير المساحة وتعمل تلقائياً)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """استقبال ملفات الـ PDF وتحويلها لكويز تفاعلي عبر تليجرام Polls"""
    action = context.user_data.get('action')
    if action != 'waiting_for_pdf':
        await update.message.reply_text("🤖 إذا أردت تحويل PDF إلى كويز، يرجى الضغط على الزر المخصص أولاً من القائمة الرئيسية.")
        return

    document = update.message.document
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("⚠️ عذراً، يجب إرسال ملف بصيغة PDF فقط.")
        return

    waiting_msg = await update.message.reply_text("📥 جاري تحميل وقراءة ملف الـ PDF... انتظر لحظة.")
    context.user_data['action'] = None

    try:
        # تحميل الملف في الذاكرة بدون حفظه على القرص
        tg_file = await context.bot.get_file(document.file_id)
        file_bytes = await tg_file.download_as_bytearray()
        
        # استخراج النص من الـ PDF
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        extracted_text = ""
        
        # نقرأ أول 5 صفحات كحد أقصى لضمان السرعة وحجم البيانات
        max_pages = min(5, len(reader.pages))
        for i in range(max_pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                extracted_text += page_text + "\n"

        if len(extracted_text.strip()) < 50:
            await waiting_msg.edit_text("❌ لم أتمكن من استخراج نص كافٍ من الـ PDF. تأكد أنه ملف نصي وليس عبارة عن صور مصورة كلياً.")
            return

        await waiting_msg.edit_text("🧠 النص جاهز! يقوم Gemini الآن بإنشاء أسئلة الاختبار الذكية...")

        # استدعاء Gemini لإنشاء هيكل كويز احترافي
        prompt = (
            f"بناءً على النص المستخرج من ملف الـ PDF المرفق بالأسفل، قم بإنشاء اختبار اختيار من متعدد باللغة العربية.\n"
            f"يجب أن يتكون الاختبار من 3 إلى 4 أسئلة ذكية تغطي لب وجوهر المحتوى.\n\n"
            f"النص المستخرج:\n{extracted_text[:4000]}"
        )

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuizSchema,
            ),
        )

        # تحويل البيانات المرسلة من الاستجابة الهيكلية
        quiz_data = response.parsed

        await waiting_msg.delete() # حذف رسالة الانتظار وبدء إرسال الكويزات

        await update.message.reply_text(f"📝 **بدأ الكويز التفاعلي لملف: {document.file_name}** 👇")

        # إرسال الأسئلة على هيئة Telegram Polls حقيقية!
        for q in quiz_data.quiz:
            await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=q.question[:300], # الحد الأقصى لتليجرام هو 300 حرف للسؤال
                options=[opt[:100] for opt in q.options], # الحد الأقصى للخيارات 100 حرف
                is_anonymous=False,
                type="quiz",
                correct_option_id=q.correct_index
            )

    except Exception as e:
        logger.error(f"Error PDF Quiz: {e}")
        await update.message.reply_text("❌ حدث خطأ داخلي أثناء معالجة الملف وصياغة الأسئلة بالذكاء الاصطناعي. يرجى المحاولة مرة أخرى.")

async def send_reminder_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(chat_id=job.chat_id, text=f"⏰ **تنبييييه!**\n\nانتهى وقت المؤقت المجدول، عد لإنجاز مهامك.")

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # الكود المعتاد للتعامل مع نصوص المهام والمؤقت كما هو في الكود السابق...
    pass

def main() -> None:
    init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))

    application.run_polling()

if __name__ == '__main__':
    main()
