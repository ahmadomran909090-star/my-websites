import os
import logging
import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google import genai

# إعداد السجلات الاحترافية لمراقبة العمليات في Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب المفاتيح البيئية
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_KEY)

DB_FILE = "productivity_platform.db"
ELZERO_PYTHON_PLAYLIST = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAyE_geIT5jC1zXBVf567mZ9"

def init_db():
    """تأسيس البنية التحتية لقاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task_text TEXT, category TEXT, priority TEXT, remind_time TEXT, is_notified INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, question TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT, correct_option TEXT, explanation TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_progress (user_id INTEGER PRIMARY KEY, current_question_index INTEGER, score INTEGER)
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY, username TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 50, hints_count INTEGER DEFAULT 3
        )
    ''')
    conn.commit()
    conn.close()

def update_user_profile(user_id, username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user_profile (user_id, username, xp, level, coins, hints_count) VALUES (?, ?, 0, 1, 50, 3)", (user_id, username))
    else:
        cursor.execute("UPDATE user_profile SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, coins, hints_count FROM user_profile WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 1, 50, 3)

def add_rewards(user_id, xp_amount, coins_amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, coins FROM user_profile WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    xp, level, coins = res if res else (0, 1, 50)
    new_xp = xp + xp_amount
    new_coins = coins + coins_amount
    new_level = (new_xp // 100) + 1
    cursor.execute("UPDATE user_profile SET xp = ?, level = ?, coins = ? WHERE user_id = ?", (new_xp, new_level, new_coins, user_id))
    conn.commit()
    conn.close()
    return new_level > level

def get_level_title(level):
    if level == 1: return "💤 مبتدئ كسلان"
    elif level == 2: return "🌱 طموح ناشئ"
    elif level == 3: return "🔨 محارب الإنتاجية"
    elif level == 4: return "🧠 وحش البايثون"
    return "👑 الأستاذ العبقري الخارق"

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💼 إدارة وجدولة المهام", callback_data="submenu_tasks")],
        [InlineKeyboardButton("📝 مركز الكويزات التفاعلي (5 - 100)", callback_data="submenu_quiz")],
        [InlineKeyboardButton("🤖 أدوات AI والملخصات الفورية", callback_data="submenu_ai")],
        [InlineKeyboardButton("🎬 سينما التكنولوجيا والأفلام", callback_data="submenu_movies")],
        [InlineKeyboardButton("🏆 لوحة الصدارة العالمية", callback_data="menu_leaderboard"), InlineKeyboardButton("🏪 متجر البوت", callback_data="menu_shop")],
        [InlineKeyboardButton("🐍 كورس Python", callback_data="menu_python"), InlineKeyboardButton("⏱️ مؤقت بومودورو", callback_data="menu_pomodoro")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_db()
    user = update.effective_user
    username = user.username or user.first_name
    update_user_profile(user.id, username)
    xp, level, coins, hints = get_profile(user.id)
    title = get_level_title(level)
    welcome_text = (
        f"🎯 أهلاً بك يا **{user.first_name}** في المنظومة التعليمية والإنتاجية الفائقة المحدثة!\n\n"
        f"📊 **ملفك الشخصي الحالي:**\n🏅 المستوى: {level} ({title})\n✨ نقاط الخبرة: {xp} XP\n🪙 رصيد العملات: {coins} مَجَرّة\n💡 التلميحات: {hints}\n\n"
        "استخدم أزرار التحكم بالأسفل للبدء والإنتاج الحين:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([BotCommand("start", "🎯 القائمة الرئيسية")])

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    update_user_profile(user_id, username)

    if query.data == "go_main":
        xp, level, coins, hints = get_profile(user_id)
        title = get_level_title(level)
        text = f"🎯 **القائمة الرئيسية المنظمة:**\n🏅 مستواك: {level} ({title}) | {xp} XP\n🪙 رصيدك: {coins} مَجَرّة | 💡 التلميحات: {hints}"
        await query.edit_message_text(text, reply_markup=main_menu_keyboard())

    elif query.data == "submenu_tasks":
        keyboard = [[InlineKeyboardButton("➕ إضافة مهمة جديدة", callback_data="menu_add")], [InlineKeyboardButton("📋 استعراض مهامك", callback_data="menu_view")], [InlineKeyboardButton("🧹 تصفية كافة المهام", callback_data="menu_clear_all")], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]
        await query.edit_message_text("💼 **| قسم المهام والجدولة الذكية:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ أرسل الآن عنوان المهمة بالأسفل:")

    elif query.data == "menu_view":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_text, category, priority FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        if not tasks:
            await query.edit_message_text("🎉 لا توجد مهام معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")]]))
        else:
            text = "📋 **مهامك المسجلة حالياً:**\n\n"
            keyboard = []
            for idx, task in enumerate(tasks):
                t_id, t_text, cat, pri = task
                text += f"{idx+1}. {t_text}\n   📁 القسم: {cat} | 🚨 الأولوية: {pri}\n──────────────────\n"
                keyboard.append([InlineKeyboardButton(f"✅ إنجاز المهمة {idx+1}", callback_data=f"delete_{t_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("cat_"):
        cat_map = {"work": "💼 العمل", "study": "📚 الدراسة", "personal": "👤 شخصي", "health": "🍏 صحة ولياقة"}
        context.user_data['temp_cat'] = cat_map[query.data.split("_")[1]]
        keyboard = [[InlineKeyboardButton("🔥 عاجل وهام", callback_data="pri_high")], [InlineKeyboardButton("⏳ متوسط الأهمية", callback_data="pri_med")], [InlineKeyboardButton("💤 خطة لاحقة", callback_data="pri_low")]]
        await query.edit_message_text("🚨 حدد مستوى الأولوية للمهمة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pri_"):
        pri_map = {"high": "🔥 عاجل", "med": "⏳ متوسط", "low": "💤 منخفض"}
        task_text = context.user_data.get('temp_name', 'مهمة دراسية')
        category_text = context.user_data.get('temp_cat', '📁 عام')
        priority_text = pri_map[query.data.split("_")[1]]
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task_text, category, priority, remind_time) VALUES (?, ?, ?, ?, ?)", (user_id, task_text, category_text, priority_text, "No Reminder"))
        conn.commit()
        conn.close()
        context.user_data.clear()
        add_rewards(user_id, 5, 2)
        await query.edit_message_text(f"✅ **تمت إضافة المهمة للجدول! (+5 XP)**\n\n📌 العنوان: {task_text}\n📁 القسم: {category_text}\n🚨 الأولوية: {priority_text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للمهام", callback_data="submenu_tasks")]]))

    elif query.data.startswith("delete_"):
        task_id = int(query.data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        leveled_up = add_rewards(user_id, 25, 10)
        bonus = "\n\n✨ نلت: **+25 XP** و **+10 عملات 🪙**!"
        if leveled_up: bonus += "\n🎉 مبروك! ارتفع مستواك العام."
        await query.edit_message_text(f"🎉 أتممت المهمة وشطبتها بنجاح.{bonus}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تحديث القائمة", callback_data="menu_view")]]))

    elif query.data == "menu_clear_all":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("🧹 تم إفراغ المهام بالكامل.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")]]))

    elif query.data == "submenu_quiz":
        await query.edit_message_text("📝 **مركز الكويزات التفاعلي:**\nأرسل نصاً أو ملف PDF لتوليد اختبار يصل لـ 100 سؤال الحين!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📁 توليد اختبار جديد", callback_data="quiz_generate")], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

    elif query.data == "quiz_generate":
        context.user_data['action'] = 'waiting_for_quiz_material'
        await query.edit_message_text("📚 أرسل النص أو ملف الـ PDF بالأسفل لقراءته وصناعة كويز منه:")

    elif query.data.startswith("num_"):
        num_requested = int(query.data.split("_")[1])
        material = context.user_data.get('quiz_material', '')
        msg = await query.edit_message_text(f"⚡ جاري توليد **{num_requested} سؤال** عبر Gemini، انتظر لحظات...")
        
        try:
            prompt = (
                f"بناءً على المحتوى التالي، قم بإنشاء كويز يتكون من {num_requested} سؤالاً بالضبط خيارات متعددة.\n"
                f"المحتوى:\n{material}\n\n"
                "يجب صياغة النتيجة بالتنسيق التالي تماماً لكل سؤال وبدون أي مقدمات أو نصوص جانبية:\n"
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
                    cursor.execute("INSERT INTO quizzes (user_id, question, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, q_match.group(1).strip(), a_match.group(1).strip(), b_match.group(1).strip(), c_match.group(1).strip(), d_match.group(1).strip(), correct_match.group(1).strip()))
                    count += 1
            conn.commit()

            cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE user_id = ? LIMIT 1 OFFSET 0", (user_id,))
            first_q = cursor.fetchone()
            conn.close()

            if first_q:
                q_text, oa, ob, oc, od, correct = first_q
                text = f"✅ **تم بناء الاختبار بنجاح (المجموع {count} سؤال)!**\n\n📊 **السؤال الأول (1):**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
                keyboard = [[InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")], [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]]
                await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await msg.edit_text("⚠️ لم يتم الفرز بشكل متوافق، أعد إرسال النص بوضوح أكبر.")
        except Exception as e:
            logger.error(f"Quiz Error: {e}")
            await msg.edit_text("❌ حدث خطأ مؤقت في النظام. يرجى تجربة ملف أصغر.")

    elif query.data.startswith("quizans_"):
        parts = query.data.split("_")
        user_choice, correct_choice = parts[1], parts[2]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT current_question_index, score FROM user_quiz_progress WHERE user_id = ?", (user_id,))
        progress = cursor.fetchone()
        current_idx, current_score = progress if progress else (0, 0)

        if user_choice == correct_choice:
            current_score += 1
            add_rewards(user_id, 10, 5)
            feedback = "✅ **إجابة صحيحة! (+10 XP | +5 عملات 🪙)**"
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
            keyboard = [[InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")], [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            add_rewards(user_id, 50, 20)
            await query.edit_message_text(f"{feedback}\n\n🎉 **انتهى الاختبار بالكامل!**\n🏆 نتيجتك: {current_score} إجابة صحيحة.\n✨ نلت مكافأة التخرج: **+50 XP** و **+20 عملة 🪙**!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="go_main")]]))

    # --- خانة الأفلام والمسلسلات الجديدة المضافة ---
    elif query.data == "submenu_movies":
        text = (
            "🎬 **| سينما التكنولوجيا والأفلام الملهمة:**\n\n"
            "مرحباً بك في صالة العرض التقنية! الأفلام هنا ليست للتسلية فقط، بل لتوسيع مداركك البرمجية وإشعال شغفك التقني من جديد. 🔥\n\n"
            "اختر أحد الأفلام الشهيرة أدناه لقراءة النبذة والبدء:"
        )
        keyboard = [
            [InlineKeyboardButton("👨‍💻 The Social Network", callback_data="movie_social")],
            [InlineKeyboardButton("🧠 The Imitation Game", callback_data="movie_imitation")],
            [InlineKeyboardButton("🤖 Mr. Robot (مسلسل)", callback_data="movie_robot")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("movie_"):
        m_type = query.data.split("_")[1]
        if m_type == "social":
            m_text = "🎬 **فيلم: The Social Network (2010)**\n\n📌 **القصة:** يروي قصة عبقري حاسوب من جامعة هارفارد (مارك زوكربيرغ) يقوم ببناء منصة شبكة اجتماعية كبرى تصبح لاحقاً 'فيسبوك'.\n\n💡 **العبرة:** يعلمك الفيلم كيفية تحويل فكرة برمجية بسيطة إلى نظام برمجي ضخم يخدم ملايين البشر حول العالم."
        elif m_type == "imitation":
            m_text = "🎬 **فيلم: The Imitation Game (2014)**\n\n📌 **القصة:** يجسد قصة العالم الشهير (آلان تورينج) وفريقه التقني الذين بنوا أول آلة حاسوبية برمجية لفك شيفرات آلة 'إنيجما' الألمانية المعقدة خلال الحرب العالمية.\n\n💡 **العبرة:** يوضح العبقرية الرياضية والتأسيس الحقيقي لعلم الخوارزميات وصناعة الكمبيوتر."
        elif m_type == "robot":
            m_text = "🎬 **مسلسل: Mr. Robot (2015-2019)**\n\n📌 **القصة:** يتحدث عن (إليوت)، مهندس الأمن السيبراني العبقري الذي يعاني من اضطرابات، ويتم تجنيده من قبل مجموعة هاكرز غامضة لإسقاط واحدة من أكبر الشركات في العالم.\n\n💡 **العبرة:** يعتبر من أدق المسلسلات علمياً وفنياً في إظهار تقنيات البرمجة، واللينكس، والشبكات، والأمن السيبراني الحقيقي."
        
        keyboard = [
            [InlineKeyboardButton("✅ تم المشاهدة واستخلاص الفائدة (+20 XP)", callback_data="movie_watched_reward")],
            [InlineKeyboardButton("🔙 العودة لقائمة الأفلام", callback_data="submenu_movies")]
        ]
        await query.edit_message_text(m_text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "movie_watched_reward":
        add_rewards(user_id, 20, 5)
        await query.edit_message_text("🎉 **رائع جداً يا بطل!**\nتم إضافة **+20 XP** و **+5 عملات 🪙** لحسابك لمواصلة شغفك بالتعلم والتطور المستمر الحين.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للأفلام", callback_data="submenu_movies")]]))

    elif query.data == "menu_leaderboard":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, level, xp FROM user_profile ORDER BY xp DESC LIMIT 10")
        top_users = cursor.fetchall()
        conn.close()
        text = "🏆 **لوحة الصدارة والمنافسة العالمية (أعلى 10 مستخدمين):**\n──────────────────\n"
        medals = ["🥇", "🥈", "🥉", "👤", "👤", "👤", "👤", "👤", "👤", "👤"]
        for idx, user_row in enumerate(top_users):
            uname, lvl, u_xp = user_row
            text += f"{medals[idx]} {idx+1}. @{uname} -> المستوي: {lvl} ({u_xp} XP)\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

    elif query.data == "menu_shop":
        xp, level, coins, hints = get_profile(user_id)
        text = f"🏪 **متجر البوت الذكي:**\n🪙 رصيدك الحالي: **{coins} عملة**\n💡 تلميحاتك: **{hints}**\n──────────────────\n1. شراء (+3 تلميحات) 💡 -> السعر: 30 عملة 🪙\n2. شراء تعزيز خبرة (+50 XP) ✨ -> السعر: 50 عملة 🪙"
        keyboard = [[InlineKeyboardButton("💡 شراء تلميحات (30 عملة)", callback_data="buy_hints")], [InlineKeyboardButton("✨ شراء طاقة XP (50 عملة)", callback_data="buy_xp")], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "buy_hints":
        xp, level, coins, hints = get_profile(user_id)
        if coins >= 30:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET coins = coins - 30, hints_count = hints_count + 3 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await query.edit_message_text("✅ تم الشراء بنجاح! نلت +3 تلميحات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 المتجر", callback_data="menu_shop")]]))
        else:
            await query.edit_message_text("❌ رصيدك غير كافٍ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 المتجر", callback_data="menu_shop")]]))

    elif query.data == "buy_xp":
        xp, level, coins, hints = get_profile(user_id)
        if coins >= 50:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET coins = coins - 50 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            add_rewards(user_id, 50, 0)
            await query.edit_message_text("✅ تم إضافة +50 XP بنجاح!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 المتجر", callback_data="menu_shop")]]))
        else:
            await query.edit_message_text("❌ رصيدك غير كافٍ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 المتجر", callback_data="menu_shop")]]))

    elif query.data == "submenu_ai":
        keyboard = [[InlineKeyboardButton("🧠 تفكيك مهمة معقدة", callback_data="ai_split")], [InlineKeyboardButton("📝 تلخيص نص ومحاضرات", callback_data="ai_summarize")], [InlineKeyboardButton("💡 نصيحة للتركيز", callback_data="ai_tips")], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]
        await query.edit_message_text("🤖 **أدوات الذكاء الاصطناعي (Gemini):**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ai_split":
        context.user_data['action'] = 'waiting_for_ai_split'
        await query.edit_message_text("🤔 اكتب المهمة الكبيرة الحين لتفكيكها:")

    elif query.data == "ai_summarize":
        context.user_data['action'] = 'waiting_for_summary_material'
        await query.edit_message_text("📝 أرسل النص أو ارفع ملف الـ PDF بالأسفل لتلخيصه:")

    elif query.data == "ai_tips":
        msg = await query.edit_message_text("⚡ جاري جلب نصيحة مخصصة كسر الكسل...")
        try:
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents="أعطني نصيحة قصيرة ملهمة باللغة العربية لشخص يدرس البرمجة ويعاني من الكسل الحين.")
            tip = response.text
        except Exception:
            tip = "ابدأ بتطبيق قانون الـ 5 دقائق، افتح لابتوبك والخطوة الصغرى الأولى ستقودك حتماً للإنجاز! 🔥"
        await msg.edit_text(f"💡 **نصيحة اليوم:**\n\n{tip}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="submenu_ai")]]))

    elif query.data == "menu_python":
        await query.edit_message_text("🐍 **كورس تعلم لغة Python - أسامة الزيرو**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📺 افتح اليوتيوب", url=ELZERO_PYTHON_PLAYLIST)], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

    elif query.data == "menu_pomodoro":
        await query.edit_message_text("⏱️ **تقنية البومودورو للتركيز الكامل:**\nتركيز 25 دقيقة يليه 5 دقائق راحة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏱️ ابدأ جلسة بومودورو عمل", callback_data="pomo_start")], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

    elif query.data == "pomo_start":
        await query.edit_message_text("🚀 **بدأت جلسة البومودورو بنجاح!**\nعزل تام عن المشتتات الحين لمدة 25 دقيقة وسيتم إخطارك عند الانتهاء. 💪", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')
    user_text = update.message.text

    if action == 'waiting_for_task_name':
        context.user_data['temp_name'] = user_text
        context.user_data['action'] = None
        keyboard = [[InlineKeyboardButton("💼 العمل", callback_data="cat_work"), InlineKeyboardButton("📚 الدراسة", callback_data="cat_study")], [InlineKeyboardButton("👤 شخصي", callback_data="cat_personal"), InlineKeyboardButton("🍏 صحة", callback_data="cat_health")]]
        await update.message.reply_text("📁 حدد تصنيف وقسم هذه المهمة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_ai_split':
        waiting_msg = await update.message.reply_text("🧠 جاري التفكيك بذكاء الـ AI...")
        context.user_data['action'] = None
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"قم بتفكيك المهمة: '{user_text}' إلى 3 خطوات مرتبة باللغة العربية.")
        await waiting_msg.reply_text(f"🧠 **خطة تفكيك العمل:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="submenu_ai")]]))

    elif action == 'waiting_for_summary_material':
        waiting_msg = await update.message.reply_text("⚡ جاري استخراج الخلاصة والتلخيص...")
        context.user_data['action'] = None
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"لخص النص التالي في نقاط ذهبية واضحة باللغة العربية:\n\n{user_text}")
        await waiting_msg.reply_text(f"📝 **الملخص المستخرج:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]))

    elif action == 'waiting_for_quiz_material':
        context.user_data['quiz_material'] = user_text
        context.user_data['action'] = None
        keyboard = [[InlineKeyboardButton("5 أسئلة 📊", callback_data="num_5"), InlineKeyboardButton("10 أسئلة 📋", callback_data="num_10")], [InlineKeyboardButton("20 سؤال 🔥", callback_data="num_20"), InlineKeyboardButton("50 سؤال 🚀", callback_data="num_50")], [InlineKeyboardButton("100 سؤال 🏆", callback_data="num_100")]]
        await update.message.reply_text("🎛️ حدد عدد الأسئلة المراد توليدها من هذا النص:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🤖 يرجى استخدام أزرار التحكم المدمجة بالرسائل لتوجيهي.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')
    doc = update.message.document

    if action in ['waiting_for_quiz_material', 'waiting_for_summary_material']:
        waiting_msg = await update.message.reply_text("📥 جاري تحميل وقراءة ملف الـ PDF الحين، انتظر ثوانٍ...")
        
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            file_name = doc.file_name or "document.pdf"
            local_path = os.path.join("/tmp", file_name) if os.path.exists("/tmp") else file_name
            await tg_file.download_to_drive(local_path)

            extracted_text = ""
            try:
                import pypdf
                reader = pypdf.PdfReader(local_path)
                for page in reader.pages:
                    extracted_text += page.extract_text() + "\n"
            except ImportError:
                extracted_text = f"[ملف مرفوع: {file_name}]"
                
            if not extracted_text.strip() or len(extracted_text.strip()) < 10:
                extracted_text = f"محتوى دراسي باسم {file_name}. يرجى معالجته بشكل ذكي وشامل."

            if os.path.exists(local_path):
                os.remove(local_path)

            if action == 'waiting_for_quiz_material':
                context.user_data['quiz_material'] = extracted_text
                context.user_data['action'] = None
                keyboard = [[InlineKeyboardButton("5 أسئلة 📊", callback_data="num_5"), InlineKeyboardButton("10 أسئلة 📋", callback_data="num_10")], [InlineKeyboardButton("20 سؤال 🔥", callback_data="num_20"), InlineKeyboardButton("50 سؤال 🚀", callback_data="num_50")], [InlineKeyboardButton("100 سؤال 🏆", callback_data="num_100")]]
                await waiting_msg.delete()
                await update.message.reply_text("📊 **تمت قراءة الـ PDF بنجاح!**\nحدد كم عدد أسئلة اختبار الأتمتة التي تود توليدها منها:", reply_markup=InlineKeyboardMarkup(keyboard))
            
            elif action == 'waiting_for_summary_material':
                await waiting_msg.edit_text("⚡ جاري التلخيص بذكاء الـ AI...")
                context.user_data['action'] = None
                response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"قم بتلخيص ملف الـ PDF التالي تلخيصاً مركزاً في نقاط مرتبة باللغة العربية:\n\n{extracted_text}")
                await waiting_msg.reply_text(f"📝 **ملخص ملف الـ PDF المستخرج:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]))

        except Exception as e:
            logger.error(f"PDF Error: {e}")
            await waiting_msg.edit_text("❌ واجهت مشكلة في قراءة الملف برمجياً. يرجى نسخ النص وإرساله مباشرة.")
    else:
        await update.message.reply_text("🤖 الرجاء تفعيل أزرار التوليد من القائمة أولاً قبل رفع المستندات والملفات.")

def main() -> None:
    init_db()
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        return
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.run_polling()

if __name__ == '__main__':
    main()
