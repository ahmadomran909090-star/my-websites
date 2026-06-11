import os
import logging
import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google import genai

# إعداد السجلات لمراقبة العمليات في Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب المفاتيح البيئية من Railway
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_KEY)

DB_FILE = "tasks.db"

# رابط قائمة تشغيل دورة بايثون لأسامة الزيرو
ELZERO_PYTHON_PLAYLIST = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAyE_geIT5jC1zXBVf567mZ9"

def init_db():
    """تهيئة جداول قاعدة البيانات المستقرة (المهام + الكويزات)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # جدول المهام
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_text TEXT,
            category TEXT,
            priority TEXT
        )
    ''')
    # جدول الكويزات لحفظ الأسئلة المستخرجة من الملفات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option TEXT
        )
    ''')
    # جدول لمتابعة تقدم المستخدم الحالي في الكويز
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_progress (
            user_id INTEGER PRIMARY KEY,
            current_question_index INTEGER,
            score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def main_menu_keyboard():
    """أزرار القائمة الرئيسية الاحترافية المدمجة مع إضافة خانة تعلم بايثون"""
    keyboard = [
        [InlineKeyboardButton("💼 إدارة وتنظيم المهام", callback_data="submenu_tasks")],
        [InlineKeyboardButton("📝 مركز الكويزات والأسئلة (حتى 100 سؤال)", callback_data="submenu_quiz")],
        [InlineKeyboardButton("🧠 قسم الذكاء الاصطناعي (Gemini)", callback_data="menu_ai")],
        [InlineKeyboardButton("🐍 تعلم لغة Python (كورس الزيرو)", callback_data="menu_python")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر البداية"""
    init_db()
    welcome_text = (
        f"🎯 أهلاً بك يا {update.effective_user.first_name} في بوت الإنتاجية والتعليم الذكي المطور!\n\n"
        "تمت إضافة خانة خاصة لتعلم البرمجة بلغة بايثون الآن.\n"
        "الرجاء الاختيار من الخانات الاحترافية بالأسفل للبدء:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأزرار وفك التعليق فوراً"""
    query = update.callback_query
    await query.answer() # فك تعليق الزر فوراً
    user_id = query.from_user.id

    # --- القوائم الرئيسية ---
    if query.data == "go_main":
        await query.edit_message_text("🎯 الخانات الرئيسية للنظام، اختر ما يناسبك:", reply_markup=main_menu_keyboard())

    elif query.data == "submenu_tasks":
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مهمة جديدة", callback_data="menu_add")],
            [InlineKeyboardButton("📋 عرض وتعديل المهام", callback_data="menu_view")],
            [InlineKeyboardButton("🗑️ مسح كافة المهام", callback_data="menu_clear_all")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("💼 **قسم إدارة المهام:**\nاختر الإجراء المناسب:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "submenu_quiz":
        keyboard = [
            [InlineKeyboardButton("📁 توليد كويز جديد من نص/ملف", callback_data="quiz_generate")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("📝 **مركز الكويزات المتطور:**\nيمكنك إرسال نصوص طويلة وتوليد حتى 100 سؤال ليقوم البوت باختبارك بها تتابيعاً.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- خانة تعلم بايثون الجديدة ---
    elif query.data == "menu_python":
        keyboard = [
            [InlineKeyboardButton("📺 فتح الـ Playlist على يوتيوب", url=ELZERO_PYTHON_PLAYLIST)],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        python_text = (
            "🐍 **دورة تعلم لغة Python - Elzero Web School**\n\n"
            "تعتبر دورة المهندس أسامة الزيرو واحدة من أفضل الدورات العربية لتعلم بايثون من الصفر وحتى الاحتراف بأسلوب مبسط وتطبيقات عملية.\n\n"
            "اضغط على الزر بالأسفل للانتقال مباشرة إلى قائمة التشغيل:"
        )
        await query.edit_message_text(python_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- معالجة قسم المهام ---
    elif query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ أرسل الآن عنوان المهمة في رسالة عادية:")

    elif query.data == "menu_view":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_text, category, priority FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        conn.close()

        if not tasks:
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")]]
            await query.edit_message_text("🎉 ممتاز! لا توجد مهام معلقة لديك حالياً.", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = "📋 **قائمة مهامك الحالية تفصيلياً:**\n\n"
            keyboard = []
            for idx, task in enumerate(tasks):
                t_id, t_text, cat, pri = task
                text += f"{idx+1}. {t_text}\n   📁 القسم: {cat} | 🚨 الأولوية: {pri}\n──────────────────\n"
                keyboard.append([InlineKeyboardButton(f"✅ شطب المهمة {idx+1}", callback_data=f"delete_{t_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("cat_"):
        category_map = {"work": "💼 العمل", "study": "📚 الدراسة", "personal": "👤 شخصي", "health": "🍏 صحة ولياقة"}
        context.user_data['temp_cat'] = category_map[query.data.split("_")[1]]
        keyboard = [
            [InlineKeyboardButton("🔥 عاجل وهام جداً", callback_data="pri_high")],
            [InlineKeyboardButton("⏳ متوسط الأهمية", callback_data="pri_med")],
            [InlineKeyboardButton("💤 عادي / لاحقاً", callback_data="pri_low")]
        ]
        await query.edit_message_text("🚨 اختر **مستوى الأهمية والأولوية** للمهمة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pri_"):
        priority_map = {"high": "🔥 عاجل", "med": "⏳ متوسط", "low": "💤 منخفض"}
        priority_text = priority_map[query.data.split("_")[1]]
        task_text = context.user_data.get('temp_name', 'مهمة بدون عنوان')
        category_text = context.user_data.get('temp_cat', '📁 عام')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task_text, category, priority) VALUES (?, ?, ?, ?)", (user_id, task_text, category_text, priority_text))
        conn.commit()
        conn.close()

        context.user_data.clear()
        keyboard = [[InlineKeyboardButton("🔙 العودة للمهام", callback_data="submenu_tasks")]]
        await query.edit_message_text(f"✅ **تمت إضافة المهمة بنجاح!**\n\n📌 المضمون: {task_text}\n📁 التصنيف: {category_text}\n🚨 الأولوية: {priority_text}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("delete_"):
        task_id = int(query.data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        keyboard = [[InlineKeyboardButton("🔄 تحديث القائمة", callback_data="menu_view")]]
        await query.edit_message_text("🎉 عمل رائع! تم إنجاز المهمة وشطبها بنجاح.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_clear_all":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")]]
        await query.edit_message_text("🧹 تم مسح كافة المهام بنجاح.", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- معالجة قسم الذكاء الاصطناعي السريع ---
    elif query.data == "menu_ai":
        keyboard = [
            [InlineKeyboardButton("🧠 فكك لي مهمة معقدة", callback_data="ai_split")],
            [InlineKeyboardButton("💡 نصيحة سريعة لمحاربة الكسل", callback_data="ai_tips")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("🤖 **مركز الإنتاجية الذكي:**\nاختر الأداة التي ترغب بها:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ai_split":
        context.user_data['action'] = 'waiting_for_ai_split'
        await query.edit_message_text("🤔 اكتب بالأسفل المهمة المعقدة لتفكيكها:")

    elif query.data == "ai_tips":
        msg = await query.edit_message_text("⚡ جاري استدعاء نصيحة من Gemini...")
        try:
            prompt = "أعطني نصيحة واحدة قصيرة جداً وملهمة باللغة العربية لشخص يعاني من التسويف والتأجيل الآن."
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            tip = response.text
        except Exception:
            tip = "ابدأ العمل الآن لمدة 5 دقائق فقط، أصعب خطوة هي البدء! 🚀"
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="menu_ai")]]
        await msg.edit_text(f"💡 **نصيحة اليوم:**\n\n{tip}", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- معالجة تشغيل وإجابات الكويز المتتابع التفاعلي ---
    elif query.data == "quiz_generate":
        context.user_data['action'] = 'waiting_for_quiz_material'
        await query.edit_message_text("📚 أرسل الآن النص أو المادة العلمية بالأسفل ليقوم البوت بقراءتها وتحويلها لكويز:")

    elif query.data.startswith("quizans_"):
        parts = query.data.split("_")
        user_choice = parts[1]
        correct_choice = parts[2]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT current_question_index, score FROM user_quiz_progress WHERE user_id = ?", (user_id,))
        progress = cursor.fetchone()
        
        current_idx, current_score = progress if progress else (0, 0)

        if user_choice == correct_choice:
            current_score += 1
            feedback = "✅ **إجابة صحيحة ممتازة!**"
        else:
            feedback = f"❌ **إجابة خاطئة!**\nالإجابة الصحيحة كانت: ({correct_choice})"

        next_idx = current_idx + 1
        cursor.execute("INSERT OR REPLACE INTO user_quiz_progress (user_id, current_question_index, score) VALUES (?, ?, ?)", (user_id, next_idx, current_score))
        conn.commit()

        cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE user_id = ? LIMIT 1 OFFSET ?", (user_id, next_idx))
        next_q = cursor.fetchone()
        conn.close()

        if next_q:
            q_text, oa, ob, oc, od, correct = next_q
            text = f"{feedback}\n\n📊السؤال الحالي ({next_idx + 1}):\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
            keyboard = [
                [InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")],
                [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]]
            await query.edit_message_text(f"{feedback}\n\n🎉 **تهانينا! لقد أتممت الكويز بالكامل.**\n\n🏆 النتيجة النهائية: {current_score} من الأسئلة المطروحة بنجاح.", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إدارة واستلام النصوص الطويلة والرسائل المكتوبة دون تعليق"""
    action = context.user_data.get('action')
    user_text = update.message.text
    user_id = update.effective_user.id

    if action == 'waiting_for_task_name':
        context.user_data['temp_name'] = user_text
        context.user_data['action'] = None
        keyboard = [
            [InlineKeyboardButton("💼 العمل", callback_data="cat_work"), InlineKeyboardButton("📚 الدراسة", callback_data="cat_study")],
            [InlineKeyboardButton("👤 شخصي", callback_data="cat_personal"), InlineKeyboardButton("🍏 صحة", callback_data="cat_health")]
        ]
        await update.message.reply_text("📁 حدد تصنيف وقسم المهمة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_ai_split':
        waiting_msg = await update.message.reply_text("🧠 جاري تفكيك المهمة بذكاء...")
        context.user_data['action'] = None
        prompt = f"قم بتفكيك هذه المهمة: '{user_text}' إلى خطة عمل سريعة جداً من 3 خطوات عملية باللغة العربية وبأسلوب بسيط."
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="menu_ai")]]
        await waiting_msg.reply_text(f"🧠 **خطة العمل المقترحة:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_quiz_material':
        waiting_msg = await update.message.reply_text("⚡ جاري تحليل المادة العلمية وتوليد الأسئلة بالذكاء الاصطناعي...")
        context.user_data['action'] = None

        try:
            prompt = (
                f"بناءً على المحتوى التالي، قم بإنشاء كويز شامل وخيارات متعددة (حتى لو بلغ 20 أو 50 سؤالاً بحسب طول المحتوى).\n"
                f"المحتوى:\n{user_text}\n\n"
                "مطلوب صياغة النتيجة بدقة وبنفس الصيغة الهيكلية التالية تماماً لكل سؤال لتسهيل قراءتها برمجياً وبدون مقدمات:\n"
                "Q: [نص السؤال]\n"
                "A: [الخيار الأول]\n"
                "B: [الخيار الثاني]\n"
                "C: [الخيار الثالث]\n"
                "D: [الخيار الرابع]\n"
                "Correct: [الحرف الصحيح فقط A أو B أو C أو D]\n"
                "---"
            )
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            raw_quiz = response.text

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM quizzes WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT OR REPLACE INTO user_quiz_progress (user_id, current_question_index, score) VALUES (?, 0, 0)", (user_id,))
            
            questions_blocks = raw_quiz.split("---")
            for block in questions_blocks:
                q_match = re.search(r"Q:\s*(.*)", block)
                a_match = re.search(r"A:\s*(.*)", block)
                b_match = re.search(r"B:\s*(.*)", block)
                c_match = re.search(r"C:\s*(.*)", block)
                d_match = re.search(r"D:\s*(.*)", block)
                correct_match = re.search(r"Correct:\s*([A-D])", block)

                if q_match and a_match and b_match and c_match and d_match and correct_match:
                    cursor.execute(
                        "INSERT INTO quizzes (user_id, question, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, q_match.group(1).strip(), a_match.group(1).strip(), b_match.group(1).strip(), c_match.group(1).strip(), d_match.group(1).strip(), correct_match.group(1).strip())
                    )
            conn.commit()

            cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE user_id = ? LIMIT 1 OFFSET 0", (user_id,))
            first_q = cursor.fetchone()
            conn.close()

            if first_q:
                q_text, oa, ob, oc, od, correct = first_q
                text = f"✅ **تم توليد الكويز بنجاح وجاهز للاختبار!**\n\n📊 **السؤال الأول (1):**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
                keyboard = [
                    [InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")],
                    [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]
                ]
                await waiting_msg.delete()
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await waiting_msg.edit_text("⚠️ لم يتمكن الذكاء الاصطناعي من صياغة الأسئلة بشكل متوافق، يرجى المحاولة بنص آخر.")
        except Exception as e:
            logger.error(f"Quiz Error: {e}")
            await waiting_msg.edit_text("❌ حدث خطأ أثناء توليد الأسئلة. جرب مرة أخرى.")
    else:
        await update.message.reply_text("🤖 الرجاء توجيهي باستخدام الأزرار التفاعلية المدمجة بالرسائل.")

def main() -> None:
    init_db()
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        logger.critical("المفاتيح ناقصة في إعدادات Railway!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))

    application.run_polling()

if __name__ == '__main__':
    main()
