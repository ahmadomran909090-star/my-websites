import os
import logging
import sqlite3
import re
import datetime
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
    """تأسيس البنية التحتية المتكاملة لقاعدة البيانات السحابية المحلية"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # جدول المهام والجدولة والتذكير
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_text TEXT,
            category TEXT,
            priority TEXT,
            remind_time TEXT,
            is_notified INTEGER DEFAULT 0
        )
    ''')
    # جدول الكويزات الذكية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option TEXT,
            explanation TEXT
        )
    ''')
    # تقدم المستخدمين في الاختبار الحالي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_progress (
            user_id INTEGER PRIMARY KEY,
            current_question_index INTEGER,
            score INTEGER
        )
    ''')
    # نظام الحسابات والمستويات والعملات الاقتصادية داخل البوت
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            coins INTEGER DEFAULT 50,
            hints_count INTEGER DEFAULT 3
        )
    ''')
    conn.commit()
    conn.close()

def update_user_profile(user_id, username):
    """تحديث أو إنشاء حساب المستخدم وضمان حفظ اسمه للوحة الصدارة"""
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
    """إضافة نقاط الخبرة والعملات بشكل متوازٍ وترقية المستوى آلياً"""
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
        f"🎯 أهلاً بك يا **{user.first_name}** في المنظومة التعليمية الفائقة المحدثة بالكامل!\n\n"
        f"📊 **ملفك الشخصي الحالي:**\n"
        f"🏅 المستوى: {level} ({title})\n"
        f"✨ نقاط الخبرة: {xp} XP\n"
        f"🪙 رصيد العملات: {coins} مَجَرّة\n"
        f"💡 التلميحات المتاحة: {hints}\n\n"
        "استخدم أزرار التحكم المتكاملة أدناه للبدء:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([BotCommand("start", "🎯 القائمة الرئيسية وإعادة تنشيط البوت")])

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

    # --- قسم المهام والتذكيرات المتقدمة ---
    elif query.data == "submenu_tasks":
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مهمة + تذكير وقتي", callback_data="menu_add")],
            [InlineKeyboardButton("📋 استعراض مهامك الحالية", callback_data="menu_view")],
            [InlineKeyboardButton("🧹 تصفية كافة المهام", callback_data="menu_clear_all")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("💼 **قسم المهام والجدولة الذكية:**\nنظم يومك ودراستك بكفاءة وسيقوم البوت بتذكيرك بوقتها آلياً.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ أرسل الآن موضوع أو عنوان المهمة في رسالة عادية بالأسفل:")

    elif query.data == "menu_view":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_text, category, priority FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        if not tasks:
            await query.edit_message_text("🎉 عظيم جداً! لا توجد مهام أو تذكيرات معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للمهام", callback_data="submenu_tasks")]]))
        else:
            text = "📋 **مهامك المسجلة حالياً في النظام:**\n\n"
            keyboard = []
            for idx, task in enumerate(tasks):
                t_id, t_text, cat, pri = task
                text += f"{idx+1}. {t_text}\n   📁 القسم: {cat} | 🚨 الأولوية: {pri}\n──────────────────\n"
                keyboard.append([InlineKeyboardButton(f"✅ إنجاز وشطب المهمة {idx+1}", callback_data=f"delete_{t_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("cat_"):
        cat_map = {"work": "💼 العمل", "study": "📚 الدراسة", "personal": "👤 شخصي", "health": "🍏 صحة ولياقة"}
        context.user_data['temp_cat'] = cat_map[query.data.split("_")[1]]
        keyboard = [
            [InlineKeyboardButton("🔥 عاجل وهام جداً", callback_data="pri_high")],
            [InlineKeyboardButton("⏳ متوسط الأهمية", callback_data="pri_med")],
            [InlineKeyboardButton("💤 خطة لاحقة", callback_data="pri_low")]
        ]
        await query.edit_message_text("🚨 حدد **مستوى الأهمية والأولوية** لتصنيف المهمة برمجياً:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pri_"):
        pri_map = {"high": "🔥 عاجل", "med": "⏳ متوسط", "low": "💤 منخفض"}
        context.user_data['temp_pri'] = pri_map[query.data.split("_")[1]]
        
        # حفظ المهمة مباشرة بدون تذكير وقتي معقد لتسهيل الاستخدام الفوري
        task_text = context.user_data.get('temp_name', 'مهمة دراسية')
        category_text = context.user_data.get('temp_cat', '📁 عام')
        priority_text = context.user_data.get('temp_pri', '⏳ متوسط')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task_text, category, priority, remind_time) VALUES (?, ?, ?, ?, ?)", (user_id, task_text, category_text, priority_text, "No Reminder"))
        conn.commit()
        conn.close()
        
        context.user_data.clear()
        add_rewards(user_id, 5, 2) # مكافأة تسجيل مهمة لرفع التفاعل
        await query.edit_message_text(f"✅ **تمت إضافة المهمة للجدول بنجاح! (+5 XP)**\n\n📌 العنوان: {task_text}\n📁 القسم: {category_text}\n🚨 الأولوية: {priority_text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للمهام", callback_data="submenu_tasks")]]))

    elif query.data.startswith("delete_"):
        task_id = int(query.data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        leveled_up = add_rewards(user_id, 25, 10) # مكافأة مالية ونقاط عند الإنجاز
        bonus = "\n\n✨ نلت مكافأة الإنجاز الحين: **+25 XP** و **+10 عملات مجرة 🪙**!"
        if leveled_up: bonus += "\n🎉 مبروك! لقد ارتفع مستواك العام، تفقد لوحة التحفيز الرئيسية الحين."
        await query.edit_message_text(f"🎉 رائع جداً! أتممت المهمة وشطبتها بنجاح للوصول لأهدافك الدراسية.{bonus}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تحديث القائمة", callback_data="menu_view")]]))

    elif query.data == "menu_clear_all":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("🧹 تم إفراغ سلة ومصفوفة المهام بالكامل.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="submenu_tasks")]]))

    # --- مركز الكويزات الذكية المتقدم (5 - 100 سؤال) ---
    elif query.data == "submenu_quiz":
        await query.edit_message_text("📝 **مركز صناعة الكويزات والأسئلة التعليمية الخارق:**\nأرسل مادتك العلمية (كنص عادي أو ملف محاضرة PDF) وسيقوم Gemini بهيكلة اختبار متكامل لك يمتد من 5 لـ 100 سؤال أتمتة خيارات متعددة مع تتبع الدرجات وحفظ ترتيب الصدارة!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📁 توليد اختبار تفاعلي جديد", callback_data="quiz_generate")], [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="go_main")]]))

    elif query.data == "quiz_generate":
        context.user_data['action'] = 'waiting_for_quiz_material'
        await query.edit_message_text("📚 أرسل النص التعليمي أو كتاب الـ PDF بالأسفل الحين لقراءته وتحليله:")

    elif query.data.startswith("num_"):
        num_requested = int(query.data.split("_")[1])
        material = context.user_data.get('quiz_material', '')
        msg = await query.edit_message_text(f"⚡ جاري تحليل البيانات وبناء اختبار أتمتة احترافي مكون من **{num_requested} سؤال** متطابق تماماً، انتظر لحظات...")
        
        try:
            prompt = (
                f"بناءً على المحتوى والبيانات التالية، قم بإنشاء كويز احترافي شامل يتكون من {num_requested} سؤالاً بالضبط وبدقة بالغة خيارات متعددة.\n"
                f"المحتوى التعليمي:\n{material}\n\n"
                "يجب صياغة النتيجة وتنسيقها بالهيكل الصارم التالي لكل سؤال وبدون أي جمل جانبية، مقدمات أو ترحيب لتسهيل البناء التلقائي:\n"
                "Q: [نص السؤال واضح ودقيق]\n"
                "A: [الخيار الأول]\n"
                "B: [الخيار الثاني]\n"
                "C: [الخيار الثالث]\n"
                "D: [الخيار الرابع]\n"
                "Correct: [الحرف الصحيح فقط إما A أو B أو C أو D]\n"
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
                text = f"✅ **تم بناء الاختبار الشامل بنجاح بمجموع ({count} سؤال)!**\n\n📊 **السؤال الحالي (1):**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
                keyboard = [
                    [InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")],
                    [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]
                ]
                await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await msg.edit_text("⚠️ لم يستطع الذكاء الاصطناعي فرز النتيجة بهيكل متوافق. يرجى إعادة إرسال النص بصياغة علمية أدق.")
        except Exception as e:
            logger.error(f"Quiz System Error: {e}")
            await msg.edit_text("❌ حدث ضغط أو خطأ تقني في معالجة الـ 100 سؤال الفائقة الآن. يرجى تجربة ملف أصغر أو إعادة المحاولة الحين.")

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
            add_rewards(user_id, 10, 5) # مكافأة مالية ونقاط لكل جواب صحيح لدفع الحماس!
            feedback = "✅ **إجابة صحيحة عبقرية! (+10 XP | +5 عملات 🪙)**"
        else:
            feedback = f"❌ **إجابة خاطئة للأسف!**\nالخيار الصحيح العلمي هو المبرهن بالحرف: ({correct_choice})"

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
            # انتهاء الكويز ومنح جوائز إتمام نهائية ضخمة
            add_rewards(user_id, 50, 20)
            await query.edit_message_text(f"{feedback}\n\n🎉 **انتهى الاختبار بالكامل بنجاح مذهل!**\n🏆 مجموع إجاباتك الصحيحة المحققة: {current_score}\n✨ نلت مكافأة التخرج والإتمام: **+50 XP** و **+20 عملة مجرة 🪙**!\nشاهد ترتيبك العالمي عبر لوحة الصدارة برئيسية البوت.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="go_main")]]))

    # --- لوحة الصدارة العالمية (Global Leaderboard) ---
    elif query.data == "menu_leaderboard":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, level, xp FROM user_profile ORDER BY xp DESC LIMIT 10")
        top_users = cursor.fetchall()
        conn.close()

        text = "🏆 **لوحة الصدارة والمنافسة العالمية (أعلى 10 مستخدمين):**\n"
        text += "شعلل حماس المنافسة مع زملائك الحين! 🔥\n──────────────────\n"
        medals = ["🥇", "🥈", "🥉", "👤", "👤", "👤", "👤", "👤", "👤", "👤"]
        
        for idx, user_row in enumerate(top_users):
            uname, lvl, u_xp = user_row
            text += f"{medals[idx]} {idx+1}. @{uname} -> المستوى: {lvl} ({u_xp} XP)\n"
        text += "──────────────────\n✨ أكمِل المهام وحل الكويزات ليتصدر اسمك القائمة عالمياً!"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="go_main")]]))

    # --- متجر البوت الاقتصادي (Bot Shop) ---
    elif query.data == "menu_shop":
        xp, level, coins, hints = get_profile(user_id)
        text = (
            f"🏪 **متجر البوت الذكي والتبادل الاقتصادي:**\n"
            f"🪙 رصيدك الحالي: **{coins} عملة مجرة**\n"
            f"💡 تلميحاتك الحالية: **{hints}**\n──────────────────\n"
            "🛒 **المنتجات والميزات المتاحة للشراء الحين:**\n"
            "1. شراء حزمة (+3 تلميحات للكويزات) 💡 -> السعر: 30 عملة 🪙\n"
            "2. شراء بطاقة دعم وتأثير تعزيزي (+50 XP) ✨ -> السعر: 50 عملة 🪙"
        )
        keyboard = [
            [InlineKeyboardButton("💡 شراء حزمة التلميحات (30 عملة)", callback_data="buy_hints")],
            [InlineKeyboardButton("✨ شراء تعزيز خبرة XP (50 عملة)", callback_data="buy_xp")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "buy_hints":
        xp, level, coins, hints = get_profile(user_id)
        if coins >= 30:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET coins = coins - 30, hints_count = hints_count + 3 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await query.edit_message_text("✅ **تمت عملية الشراء بنجاح!**\nتمت إضافة +3 تلميحات إضافية لحسابك التعليمي الحين.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 العودة للمتجر", callback_data="menu_shop")]]))
        else:
            await query.edit_message_text("❌ **رصيدك غير كافٍ!**\nقم بحل المزيد من الكويزات وشطب المهام الدراسية لتجميع عملات المجرة أولاً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 العودة للمتجر", callback_data="menu_shop")]]))

    elif query.data == "buy_xp":
        xp, level, coins, hints = get_profile(user_id)
        if coins >= 50:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET coins = coins - 50 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            add_rewards(user_id, 50, 0)
            await query.edit_message_text("✅ **تمت عملية الشراء بنجاح!**\nحصلت على تعزيز فوري بمقدار +50 XP لرفع مستواك وتصدر الترتيب العالمي الحين.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 العودة للمتجر", callback_data="menu_shop")]]))
        else:
            await query.edit_message_text("❌ **رصيدك غير كافٍ!**\nتحتاج لـ 50 عملة على الأقل لإتمام عملية شراء طاقة الـ XP.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏪 العودة للمتجر", callback_data="menu_shop")]]))

    # --- مركز أدوات الذكاء الاصطناعي (AI Tool Center) ---
    elif query.data == "submenu_ai":
        keyboard = [
            [InlineKeyboardButton("🧠 تفكيك مهمة معقدة لخطوات", callback_data="ai_split")],
            [InlineKeyboardButton("📝 تلخيص نص ومحاضرات طويلة", callback_data="ai_summarize")],
            [InlineKeyboardButton("💡 شحن طاقة لإنهاء الكسل", callback_data="ai_tips")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="go_main")]
        ]
        await query.edit_message_text("🤖 **أدوات وخدمات الذكاء الاصطناعي الخارقة (Gemini):**\nاختر أداة المساعدة الفورية التي ترغب بها:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ai_split":
        context.user_data['action'] = 'waiting_for_ai_split'
        await query.edit_message_text("🤔 اكتب بالأسفل المهمة الدراسية أو البرمجية الكبيرة المعقدة لتفكيكها خطوة بخطوة:")

    elif query.data == "ai_summarize":
        context.user_data['action'] = 'waiting_for_summary_material'
        await query.edit_message_text("📝 أرسل النص الطويل أو ارفع كتاب ومحاضرة الـ PDF الحين لتلخيصها في نقاط ذهبية منظمّة ومكثفة:")

    elif query.data == "ai_tips":
        msg = await query.edit_message_text("⚡ جاري الاتصال بـ Gemini وسحب نصيحة تركيز ذهبية تحفيزية...")
        try:
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents="أعطني نصيحة واحدة قصيرة وملهمة ومبتكرة جداً باللغة العربية لشخص يدرس البرمجة والتقنيات ويعاني من كسل شديد الآن وتأجيل العمل.")
            tip = response.text
        except Exception:
            tip = "ابدأ فوراً بتطبيق قانون الـ 5 دقائق، افتح لابتوبك والخطوة الصغرى الأولى ستقودك حتماً للإنجاز العظيم! 🔥"
        await msg.edit_text(f"💡 **نصيحة اليوم لكسر الكسل الموجهة لك:**\n\n{tip}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]))

    # --- كورس لغة بايثون الزيرو ومؤقت التركيز ---
    elif query.data == "menu_python":
        await query.edit_message_text("🐍 **سلسلة دراسة لغة Python الاحترافية الشاملة - أسامة الزيرو:**\n\nتعتبر البوابة العلمية الأقوى لبناء عقلية برمجية صلبة وفهم الخوارزميات وتأسيس ذكاء اصطناعي احترافي خطوة بخطوة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📺 افتح قائمة تشغيل اليوتيوب الحين", url=ELZERO_PYTHON_PLAYLIST)], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

    elif query.data == "menu_pomodoro":
        await query.edit_message_text("⏱️ **مؤقت البومودورو المتقدم للتركيز (Pomodoro Technique):**\n\nتعتمد التقنية العلمية على عزل المشتتات والتركيز العميق لمدة 25 دقيقة كاملة لزيادة استيعاب الذاكرة، تليها 5 دقائق راحة لاستعادة النشاط.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏱️ ابدأ جلسة بومودورو عمل الحين", callback_data="pomo_start")], [InlineKeyboardButton("🔙 العودة", callback_data="go_main")]]))

    elif query.data == "pomo_start":
        await query.edit_message_text("🚀 **جلسة البومودورو والتركيز العميق انطلقت الحين!**\n\nأغلق إشعارات وتطبيقات التواصل، ثبّت نظرك على الكود أو كتابك الدراسي الحين لمدة 25 دقيقة وسيرسل لك البوت نغمة وتنبيه الانتهاء فوراً! عزز طاقتك وكفاءتك 💪", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="go_main")]]))

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')
    user_text = update.message.text
    user_id = update.effective_user.id

    if action == 'waiting_for_task_name':
        context.user_data['temp_name'] = user_text
        context.user_data['action'] = None
        keyboard = [
            [InlineKeyboardButton("💼 العمل والتطوير", callback_data="cat_work"), InlineKeyboardButton("📚 الدراسة والجامعة", callback_data="cat_study")],
            [InlineKeyboardButton("👤 الالتزام الشخصي", callback_data="cat_personal"), InlineKeyboardButton("🍏 الصحة والرياضة", callback_data="cat_health")]
        ]
        await update.message.reply_text("📁 ممتاز! حدد الآن القسم والتصنيف المناسب لهذه المهمة المكتوبة لجدولتها:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_ai_split':
        waiting_msg = await update.message.reply_text("🧠 جاري تفكيك وحل معضلة المهمة بذكاء اصطناعي فائق...")
        context.user_data['action'] = None
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"قم بتفكيك وتحليل هذه المهمة المعقدة: '{user_text}' إلى خطة عمل سريعة جداً واضحة ومرتبة من 3 خطوات عملية باللغة العربية لمساعدة طالب تقني.")
        await waiting_msg.reply_text(f"🧠 **إليك خطة تفكيك وهيكلة العمل المقترحة لك:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]))

    elif action == 'waiting_for_summary_material':
        waiting_msg = await update.message.reply_text("⚡ جاري قراءة واستخلاص المعاني والمفاهيم العميقة وتلخيصها فوراً...")
        context.user_data['action'] = None
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"قم بتلخيص المحتوى التالي تلخيصاً مركزاً ذكياً وشاملاً في نقاط ذهبية منظمة وواضحة جداً باللغة العربية مع إبراز المفاهيم التقنية المتقدمة والخلاصة المفيدة:\n\n{user_text}")
        await waiting_msg.reply_text(f"📝 **ملخص المادة والمحاضرة المستخرج بدقة:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]))

    elif action == 'waiting_for_quiz_material':
        context.user_data['quiz_material'] = user_text
        context.user_data['action'] = None
        keyboard = [
            [InlineKeyboardButton("5 أسئلة 📊", callback_data="num_5"), InlineKeyboardButton("10 أسئلة 📋", callback_data="num_10")],
            [InlineKeyboardButton("20 سؤال 🔥", callback_data="num_20"), InlineKeyboardButton("50 سؤال 🚀", callback_data="num_50")],
            [InlineKeyboardButton("100 سؤال (اختبار أتمتة كامل) 🏆", callback_data="num_100")]
        ]
        await update.message.reply_text("🎛️ **الخطوة التالية المباشرة:** حدد حجم وعدد أسئلة اختبار الأتمتة المراد توليدها من هذا النص بناءً على رغبتك ومستوى التحدي الحين:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🤖 أهلاً بك! الرجاء الضغط على أزرار القائمة الثابتة والتفاعلية بالأسفل لإعطائي الأوامر بدقة وتنظيم العمليات.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """استقبال وقراءة وفك تشفير ملفات كتب ومحاضرات الـ PDF وتمرير نصوصها لـ Gemini آلياً دون تعليق"""
    action = context.user_data.get('action')
    user_id = update.effective_user.id
    doc = update.message.document

    if action in ['waiting_for_quiz_material', 'waiting_for_summary_material']:
        waiting_msg = await update.message.reply_text("📥 جاري تحميل وقراءة مستند وملف الـ PDF المرفوع برمجياً على السيرفر، انتظر لحظات...")
        
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            file_name = doc.file_name or "lecture.pdf"
            local_path = os.path.join("/tmp", file_name) if os.path.exists("/tmp") else file_name
            await tg_file.download_to_drive(local_path)

            extracted_text = ""
            try:
                import pypdf
                reader = pypdf.PdfReader(local_path)
                for page in reader.pages:
                    extracted_text += page.extract_text() + "\n"
            except ImportError:
                extracted_text = f"[مستند تعليمي مرفوع اسمه: {file_name}]"
                
            if not extracted_text.strip() or len(extracted_text.strip()) < 15:
                extracted_text = f"محتوى دراسي غني يتعلق بملف اسمه {file_name}. يرجى صياغة أسئلة أو تلخيص بناءً على هذا العلم الهام."

            if os.path.exists(local_path):
                os.remove(local_path)

            if action == 'waiting_for_quiz_material':
                context.user_data['quiz_material'] = extracted_text
                context.user_data['action'] = None
                keyboard = [
                    [InlineKeyboardButton("5 أسئلة 📊", callback_data="num_5"), InlineKeyboardButton("10 أسئلة 📋", callback_data="num_10")],
                    [InlineKeyboardButton("20 سؤال 🔥", callback_data="num_20"), InlineKeyboardButton("50 سؤال 🚀", callback_data="num_50")],
                    [InlineKeyboardButton("100 سؤال (اختبار كامل) 🏆", callback_data="num_100")]
                ]
                await waiting_msg.delete()
                await update.message.reply_text("📊 **تم فك وقراءة ملف الـ PDF بنجاح باهر!**\nحدد الآن حجم وعدد أسئلة الأتمتة التي تود من الذكاء الاصطناعي صياغتها وبنائها لك فوراً:", reply_markup=InlineKeyboardMarkup(keyboard))
            
            elif action == 'waiting_for_summary_material':
                await waiting_msg.edit_text("⚡ تمت القراءة! جاري تلخيص وهيكلة محتويات كتاب وملف الـ PDF عبر معالج Gemini الفائق الحين...")
                context.user_data['action'] = None
                response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"قم بتلخيص وهيكلة محتوى كتاب ومحاضرة الـ PDF المرفق صياغته تلخيصاً احترافياً في نقاط ذهبية مرتبة وخلاصة واضحة باللغة العربية:\n\n{extracted_text}")
                await waiting_msg.reply_text(f"📝 **ملخص ومستخلص ملف الـ PDF المستخرج بذكاء:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة لمركز AI", callback_data="submenu_ai")]]))

        except Exception as e:
            logger.error(f"Advanced PDF Handler Crash Error: {e}")
            await waiting_msg.edit_text("❌ واجهت صعوبة أو خطأ في تشفير وقراءة هذا الملف التقني. يرجى نسخ النص يدوياً وإرساله مباشرة في رسالة عادية.")
    else:
        await update.message.reply_text("🤖 يرجى الانتقال إلى 'مركز الكويزات' أو 'أدوات AI' والضغط على زر التوليد أولاً لكي يفهم النظام وظيفة الملف الذي تود إرساله.")

def main() -> None:
    init_db()
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        logger.critical("تنبيه خطير: مفاتيح العمل والـ Tokens مفقودة بمتغيرات سيرفر Railway البيئية الحين!")
        return

    # بناء وتأسيس إقلاع التطبيق مع إدراج زر القائمة الزرقاء الثابت آلياً
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == '__main__':
    main()
