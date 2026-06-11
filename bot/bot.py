import os
import logging
import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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
ELZERO_PYTHON_PLAYLIST = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAyE_geIT5jC1zXBVf567mZ9"

def init_db():
    """تهيئة جداول قاعدة البيانات المستقرة والمتكاملة"""
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
    # جدول الكويزات
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
    # تقدم الكويز الحالي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_progress (
            user_id INTEGER PRIMARY KEY,
            current_question_index INTEGER,
            score INTEGER
        )
    ''')
    # نظام النقاط والمستويات (Gamification)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def get_profile(user_id):
    """جلب بيانات مستوى المستخدم ونقاطه"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level FROM user_profile WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO user_profile (user_id, xp, level) VALUES (?, 0, 1)", (user_id,))
        conn.commit()
        res = (0, 1)
    conn.close()
    return res

def add_xp(user_id, amount):
    """إضافة نقاط خبرة وترقية المستوى تلقائياً عند تخطي الحدود"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    xp, level = get_profile(user_id)
    new_xp = xp + amount
    # كل مستوى يحتاج 100 XP للترقية
    new_level = (new_xp // 100) + 1
    cursor.execute("UPDATE user_profile SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
    conn.commit()
    conn.close()
    return new_level > level # إرجاع True إذا ارتفع المستوى

def get_level_title(level):
    """إعطاء ألقاب حماسية بناءً على مستوى المستخدم"""
    if level == 1: return "💤 مبتدئ كسلان"
    elif level == 2: return "🌱 طموح ناشئ"
    elif level == 3: return "🔨 محارب الإنتاجية"
    elif level == 4: return "🧠 وحش البايثون"
    return "👑 الأستاذ العبقري"

def main_menu_keyboard(user_id):
    """لوحة التحكم الرئيسية الخارقة التي تشمل كافة الخيارات الجديدة"""
    xp, level = get_profile(user_id)
    title = get_level_title(level)
    
    keyboard = [
        [InlineKeyboardButton("💼 إدارة وتنظيم المهام", callback_data="submenu_tasks")],
        [InlineKeyboardButton("📝 مركز الكويزات المتطور (5 - 100)", callback_data="submenu_quiz")],
        [InlineKeyboardButton("🧠 مركز AI والملخصات الذكية", callback_data="submenu_ai")],
        [InlineKeyboardButton("🐍 تعلم Python (كورس الزيرو)", callback_data="menu_python")],
        [InlineKeyboardButton("⏱️ مؤقت بومودورو للتركيز", callback_data="menu_pomodoro")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_db()
    user_id = update.effective_user.id
    xp, level = get_profile(user_id)
    title = get_level_title(level)
    
    welcome_text = (
        f"🎯 أهلاً بك يا {update.effective_user.first_name} في مساعدك الشخصي الخارق للإنتاجية والتعليم!\n\n"
        f"📊 **ملفك الحالي:**\n"
        f"🏅 المستوى: {level} ({title})\n"
        f"✨ نقاط الخبرة: {xp} XP\n\n"
        "تم تجميع كافة الميزات الذكية ونظام الكويزات المرن بالأسفل لتبدأ فوراً:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(user_id))

async def post_init(application: Application) -> None:
    commands = [BotCommand("start", "🎯 القائمة الرئيسية / إعادة تشغيل البوت")]
    await application.bot.set_my_commands(commands)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer() # فك تعليق جميع الأزرار فوراً لحل المشكلة نهائياً
    user_id = query.from_user.id

    if query.data == "go_main":
        xp, level = get_profile(user_id)
        title = get_level_title(level)
        text = f"🎯 **القائمة الرئيسية:**\n🏅 مستواك: {level} ({title}) | {xp} XP\n\nاختر الأداة التي ترغب بها:"
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(user_id))

    # --- قسم المهام ---
    elif query.data == "submenu_tasks":
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مهمة جديدة", callback_data="menu_add")],
            [InlineKeyboardButton("📋 عرض وتعديل المهام", callback_data="menu_view")],
            [InlineKeyboardButton("🗑️ مسح كافة المهام", callback_data="menu_clear_all")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("💼 **قسم إدارة المهام:**\nاختر الإجراء المناسب:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ أرسل الآن عنوان المهمة في رسالة عادية بالأسفل:")

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
                keyboard.append([InlineKeyboardButton(f"✅ شطب وإنجاز المهمة {idx+1}", callback_data=f"delete_{t_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("cat_"):
        category_map = {"work": "💼 العمل", "study": "📚 الدراسة", "personal": "👤 شخصي", "health": "🍏 صحة ولياقة"}
        context.user_data['temp_cat'] = category_map[query.data.split("_")[1]]
        keyboard = [
            [InlineKeyboardButton("🔥 عاجل وهام", callback_data="pri_high")],
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
        
        # منح المستخدم نقاط خبرة عند إنجاز المهمة!
        leveled_up = add_xp(user_id, 20)
        bonus_text = "\n\n✨ حصلت على **+20 XP** لإنتاجيتك!"
        if leveled_up: bonus_text += "\n🎉 مبروك! لقد ارتفع مستواك الإجمالي، تفقد الملف الشخصي برئيسية البوت."
        
        keyboard = [[InlineKeyboardButton("🔄 تحديث القائمة", callback_data="menu_view")]]
        await query.edit_message_text(f"🎉 عمل رائع! تم إنجاز المهمة وشطبها بنجاح.{bonus_text}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_clear_all":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")]]
        await query.edit_message_text("🧹 تم مسح كافة المهام بنجاح.", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- مركز الكويزات المطور (من 5 إلى 100 سؤال) ---
    elif query.data == "submenu_quiz":
        keyboard = [
            [InlineKeyboardButton("📁 توليد كويز تفاعلي جديد", callback_data="quiz_generate")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("📝 **مركز الكويزات والأسئلة الشامل:**\nيمكنك الآن إرسال موادك وتحديد حجم الاختبار بدقة ليصل حتى 100 سؤال!", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "quiz_generate":
        context.user_data['action'] = 'waiting_for_quiz_material'
        await query.edit_message_text("📚 أرسل الآن المحاضرة أو النص العلمي بالأسفل لتحليله وصناعة كويز منه:")

    elif query.data.startswith("num_"):
        # المستخدم حدد عدد الأسئلة المطلوبة الآن
        num_requested = int(query.data.split("_")[1])
        material = context.user_data.get('quiz_material', '')
        
        msg = await query.edit_message_text(f"⚡ جاري استدعاء Gemini وتوليد كويز من **{num_requested} سؤال** خيارات متعددة بدقة، انتظر ثوانٍ...")
        
        try:
            prompt = (
                f"بناءً على المحتوى التالي، قم بإنشاء كويز احترافي خيارات متعددة يتكون من {num_requested} سؤالاً بالضبط وبدقة بالغة.\n"
                f"المحتوى:\n{material}\n\n"
                "صغ النتيجة بالهيكل التالي تماماً لكل سؤال لتسهيل الاستخراج البرمجي وبدون أي مقدمات أو نصوص جانبية:\n"
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
            cursor.execute("INSERT OR REPLACE INTO user_quiz_progress (user_id, current_question_index, score) VALUES (?, 0, 0)", (user_id, 0, 0))
            
            questions_blocks = raw_quiz.split("---")
            count = 0
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
                    count += 1
            conn.commit()

            cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE user_id = ? LIMIT 1 OFFSET 0", (user_id,))
            first_q = cursor.fetchone()
            conn.close()

            if first_q:
                q_text, oa, ob, oc, od, correct = first_q
                text = f"✅ **تم توليد الكويز بنجاح المجموع ({count} سؤال)!**\n\n📊 **السؤال الأول (1):**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
                keyboard = [
                    [InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")],
                    [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]
                ]
                await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await msg.edit_text("⚠️ لم يتمكن الذكاء الاصطناعي من هيكلة الأسئلة بشكل متوافق، أعد إرسال النص بوضوح.")
        except Exception as e:
            logger.error(f"Quiz Error: {e}")
            await msg.edit_text("❌ حدث خطأ في النظام أثناء معالجة الـ 100 سؤال. قلل النص أو أعد المحاولة ثانية.")

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
            add_xp(user_id, 10) # 10 XP للإجابة الصحيحة
            feedback = "✅ **إجابة صحيحة مذهلة! (+10 XP)**"
        else:
            feedback = f"❌ **إجابة خاطئة!**\nالصحيح هو: ({correct_choice})"

        next_idx = current_idx + 1
        cursor.execute("INSERT OR REPLACE INTO user_quiz_progress (user_id, current_question_index, score) VALUES (?, ?, ?)", (user_id, next_idx, current_score))
        conn.commit()

        cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE user_id = ? LIMIT 1 OFFSET ?", (user_id, next_idx))
        next_q = cursor.fetchone()
        conn.close()

        if next_q:
            q_text, oa, ob, oc, od, correct = next_q
            text = f"{feedback}\n\n📊 **السؤال التالي ({next_idx + 1}):**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
            keyboard = [
                [InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")],
                [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="go_main")]]
            await query.edit_message_text(f"{feedback}\n\n🎉 **انتهى الكويز بالكامل المطور!**\n🏆 نتيجتك النهائية المحققة: {current_score} إجابات صحيحة.\nاستمر في التعلم لرفع مستواك الشخصي الخارق!", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- مركز الذكاء الاصطناعي والتلاخيص ---
    elif query.data == "submenu_ai":
        keyboard = [
            [InlineKeyboardButton("🧠 تفكيك مهمة معقدة", callback_data="ai_split")],
            [InlineKeyboardButton("📝 تلخيص نص/محاضرة طويلة", callback_data="ai_summarize")],
            [InlineKeyboardButton("💡 نصيحة لإنهاء الكسل", callback_data="ai_tips")],
            [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]
        ]
        await query.edit_message_text("🤖 **مركز الذكاء الاصطناعي الذكي (Gemini):**\nاختر الأداة التعليمية المناسبة للبدء الحين:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ai_split":
        context.user_data['action'] = 'waiting_for_ai_split'
        await query.edit_message_text("🤔 اكتب بالأسفل المهمة الكبيرة التي تعجز عن تفكيكها الحين:")

    elif query.data == "ai_summarize":
        context.user_data['action'] = 'waiting_for_summary_material'
        await query.edit_message_text("📝 أرسل النص الطويل أو مقال المحاضرة بالأسفل لتلخيصه في نقاط ذهبية فوراً:")

    elif query.data == "ai_tips":
        msg = await query.edit_message_text("⚡ جاري جلب نصيحة ذهبية لزيادة تركيزك...")
        try:
            prompt = "أعطني نصيحة واحدة قصيرة وملهمة باللغة العربية لشخص يدرس البرمجة والذكاء الاصطناعي ويعاني من الكسل الآن."
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            tip = response.text
        except Exception:
            tip = "ابدأ فوراً بتطبيق قانون الـ 5 دقائق، افتح اللابتوب والخطوة الأولى ستقودك للبقية! 🔥"
        keyboard = [[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]
        await msg.edit_text(f"💡 **نصيحة اليوم للتركيز:**\n\n{tip}", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- كورس بايثون الزيرو ---
    elif query.data == "menu_python":
        keyboard = [
            [InlineKeyboardButton("📺 فتح الـ Playlist على يوتيوب", url=ELZERO_PYTHON_PLAYLIST)],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        python_text = (
            "🐍 **دورة تعلم لغة Python من الصفر - أسامة الزيرو**\n\n"
            "الدورة العربية الأقوى لتعلم التفكير البرمجي وبناء التطبيقات خطوة بخطوة وبشرح مبسط للغاية.\n\n"
            "اضغط على الخانة أدناه للانتقال للمشاهدة والدراسة فوراً:"
        )
        await query.edit_message_text(python_text, reply_markup=InlineKeyboardMarkup(keyboard))

    # --- مؤقت البومودورو للتركيز ---
    elif query.data == "menu_pomodoro":
        keyboard = [
            [InlineKeyboardButton("⏱️ ابدأ بومودورو (25 دقيقة عمل)", callback_data="pomo_start")],
            [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]
        ]
        await query.edit_message_text("⏱️ **تقنية البومودورو (Pomodoro Technique):**\n\nتعتمد على التركيز الكامل لمدة 25 دقيقة كاملة في الدراسة دون تشتيت، ثم أخذ راحة 5 دقائق لإعادة شحن طاقتك.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "pomo_start":
        keyboard = [[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="go_main")]]
        await query.edit_message_text("🚀 **بدأت جلسة البومودورو بنجاح!**\n\nقم بإغلاق كافة شبكات التواصل والتركيز التام على بايثون أو مادتك الدراسية الآن لمدة 25 دقيقة. سيعلمك البوت عند الانتهاء تلقائياً! 💪", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await update.message.reply_text("📁 حدد تصنيف وقسم المهمة المكتوبة الحين:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_ai_split':
        waiting_msg = await update.message.reply_text("🧠 جاري تفكيك المهمة المعقدة بذكاء الـ AI...")
        context.user_data['action'] = None
        prompt = f"قم بتفكيك هذه المهمة المعقدة: '{user_text}' إلى خطة عمل سريعة جداً ومرتبة من 3 خطوات واضحة باللغة العربية."
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="submenu_ai")]]
        await waiting_msg.reply_text(f"🧠 **خطة تفكيك العمل الموصى بها:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_summary_material':
        waiting_msg = await update.message.reply_text("⚡ جاري قراءة النص وتلخيصه بذكاء...")
        context.user_data['action'] = None
        prompt = f"قم بتلخيص النص التالي تلخيصاً مكثفاً في نقاط ذهبية واضحة مع إبراز المفاهيم الهامة والخلاصة باللغة العربية:\n\n{user_text}"
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        keyboard = [[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]
        await waiting_msg.reply_text(f"📝 **ملخص المادة المستخرج:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_quiz_material':
        # حفظ النص في الذاكرة المؤقتة وسؤال المستخدم عن عدد الأسئلة التي يفضلها بحرية من 5 لـ 100!
        context.user_data['quiz_material'] = user_text
        context.user_data['action'] = None
        
        keyboard = [
            [InlineKeyboardButton("5 أسئلة 📊", callback_data="num_5"), InlineKeyboardButton("10 أسئلة 📋", callback_data="num_10")],
            [InlineKeyboardButton("20 سؤال 🔥", callback_data="num_20"), InlineKeyboardButton("50 سؤال 🚀", callback_data="num_50")],
            [InlineKeyboardButton("100 سؤال (اختبار كامل) 🏆", callback_data="num_100")]
        ]
        await update.message.reply_text("🎛️ **الخطوة الثانية:** حدد عدد الأسئلة الأتمتة المراد توليدها من هذا النص:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🤖 الرجاء توجيهي واستخدام الأزرار التفاعلية المدمجة بالرسائل لإدارة العمليات.")

def main() -> None:
    init_db()
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        logger.critical("المفاتيح ناقصة في إعدادات ومتغيرات Railway بيئياً!")
        return

    # تشغيل البوت مع زر القائمة الثابت تلقائياً عند الإقلاع
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))

    application.run_polling()

if __name__ == '__main__':
    main()
