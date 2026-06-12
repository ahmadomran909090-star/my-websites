import os
import logging
import sqlite3
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google import genai

# إعداد السجلات لمراقبة العمليات في Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب المفاتيح البيئية
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_KEY)

DB_FILE = "productivity_platform.db"

# روابط كورسات أسامة الزيرو
ELZERO_PYTHON_PLAYLIST = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAyE_geIT5jC1zXBVf567mZ9"
ELZERO_CPP_PLAYLIST = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAw_t_XWUFbBX-c9MafPk9ji"

# قاموس اللغات المتعددة
LOCALIZATION = {
    "ar": {
        "welcome": "🎯 أهلاً بك يا **{name}** في المنظومة الإنتاجية الخارقة المحدثة!\n\n📊 **ملفك الشخصي المحدث الحين:**\n🏅 المستوى: {level} ({title})\n✨ نقاط الخبرة: {xp} XP\n🪙 رصيد العملات: {coins} مَجَرّة\n💡 التلميحات: {hints}\n\nاختر أحد الأقسام بالأسفل وانطلق بقوة الحين:",
        "main_menu": "🎯 **القائمة الرئيسية المنظمة:**\n🏅 مستواك: {level} ({title}) | {xp} XP\n🪙 رصيدك: {coins} مَجَرّة | 💡 التلميحات: {hints}",
        "btn_tasks": "💼 إدارة وجدولة المهام",
        "btn_quiz": "📝 مركز الكويزات التفاعلي",
        "btn_ai": "🤖 أدوات AI والملخصات الفورية",
        "btn_movies": "🎬 سينما التكنولوجيا والأفلام v2",
        "btn_leaderboard": "🏆 لوحة الصدارة العالمية",
        "btn_shop": "🏪 متجر البوت",
        "btn_courses": "📚 قسم كورسات البرمجة",
        "btn_pomodoro": "⏱️ مؤقت بومودورو",
        "btn_challenge": "🔥 تحدي اليوم البرمجي الخارق",
        "btn_back": "🔙 العودة",
        "btn_main": "🔙 القائمة الرئيسية",
        "lang_select": "🌍 الرجاء اختيار لغة البوت المعتمدة الخاصة بك:"
    },
    "en": {
        "welcome": "🎯 Welcome **{name}** to the ultimate productivity ecosystem!\n\n📊 **Your Profile:**\n🏅 Level: {level} ({title})\n✨ Experience: {xp} XP\n🪙 Coins: {coins} Galaxy\n💡 Hints: {hints}\n\nChoose a section below and unleash your power:",
        "main_menu": "🎯 **Main Dashboard:**\n🏅 Level: {level} ({title}) | {xp} XP\n🪙 Coins: {coins} Galaxy | 💡 Hints: {hints}",
        "btn_tasks": "💼 Task Management & Scheduling",
        "btn_quiz": "📝 Interactive Quiz Center",
        "btn_ai": "🤖 AI Tools & Quick Summaries",
        "btn_movies": "🎬 Tech Cinema & Movies v2",
        "btn_leaderboard": "🏆 Global Leaderboard",
        "btn_shop": "🏪 Bot Shop",
        "btn_courses": "📚 Programming Courses",
        "btn_pomodoro": "⏱️ Pomodoro Timer",
        "btn_challenge": "🔥 Ultimate Daily Coding Challenge",
        "btn_back": "🔙 Back",
        "btn_main": "🔙 Main Menu",
        "lang_select": "🌍 Please choose your preferred bot language:"
    },
    "ru": {
        "welcome": "🎯 Добро пожаловать, **{name}**, в супер-продуктивную экосистему!\n\n📊 **Ваш профиль:**\n🏅 Уровень: {level} ({title})\n✨ Опыт: {xp} XP\n🪙 Монеты: {coins} Галактика\n💡 Подсказки: {hints}\n\nВыбери раздел ниже и начни прямо сейчас:",
        "main_menu": "🎯 **Главное меню:**\n🏅 Уровень: {level} ({title}) | {xp} XP\n🪙 Монеты: {coins} Галактика | 💡 Подсказки: {hints}",
        "btn_tasks": "💼 Управление задачами",
        "btn_quiz": "📝 Интерактивный центр викторин",
        "btn_ai": "🤖 Инструменты ИИ и сводки",
        "btn_movies": "🎬 Техно-кино и фильмы v2",
        "btn_leaderboard": "🏆 Мировая таблица лидеров",
        "btn_shop": "🏪 Магазин бота",
        "btn_courses": "📚 Курсы программирования",
        "btn_pomodoro": "⏱️ Таймер Помодоро",
        "btn_challenge": "🔥 Главный вызов программирования",
        "btn_back": "🔙 Назад",
        "btn_main": "🔙 Главное меню",
        "lang_select": "🌍 Пожалуйста, выберите предпочитаемый язык бота:"
    },
    "tr": {
        "welcome": "🎯 **{name}**, nihai üretkenlik ekosistemine hoş geldiniz!\n\n📊 **Profiliniz:**\n🏅 Seviye: {level} ({title})\n✨ Deneyim: {xp} XP\n🪙 Jetonlar: {coins} Galaksi\n💡 İpuçları: {hints}\n\nAşağıdan bir bölüm seçin ve gücünüzü serbest bırakın:",
        "main_menu": "🎯 **Ana Menü:**\n🏅 Seviye: {level} ({title}) | {xp} XP\n🪙 Jetonlar: {coins} Galaksi | 💡 İpuçları: {hints}",
        "btn_tasks": "💼 Görev Yönetimi ve Planlama",
        "btn_quiz": "📝 İnteraktif Bilgi Yarışması",
        "btn_ai": "🤖 Yapay Zeka Araçları ve Özetler",
        "btn_movies": "🎬 Teknoloji Sineması ve Filmler v2",
        "btn_leaderboard": "🏆 Küresel Liderlik Tablosu",
        "btn_shop": "🏪 Bot Mağazası",
        "btn_courses": "📚 Programlama Kursları",
        "btn_pomodoro": "⏱️ Pomodoro Zamanlayıcı",
        "btn_challenge": "🔥 Günlük Kodlama Yarışması",
        "btn_back": "🔙 Geri",
        "btn_main": "🔙 Ana Menü",
        "lang_select": "🌍 Lütfen tercih ettiğiniz bot dilini seçin:"
    }
}

# قاعدة بيانات الأفلام والمسلسلات
MOVIES_DATABASE = {
    "ai": [
        {"id": "imitation", "title": "🧠 The Imitation Game", "story": "قصة العالم (آلان تورينج) الذي نجح في بناء أول آلة كمبيوتر بدائية لفك شفرة الإيجما الألمانية معقّداً قواعد الحرب.", "lesson": "يعلمك التأسيس الحقيقي للمنطق البرمجي والخوارزميات وتوليد الآلات الذكية.", "q": "ما هي الشفرة الألمانية التي نجح آلان تورينج في فكها؟", "a": "الإيجما (Enigma)", "b": "النازية", "c": "اللينكس", "correct": "A"},
        {"id": "interstellar", "title": "🚀 Interstellar", "story": "فريق من رواد الفضاء يسافر عبر ثقب دودي في محاولة لإنقاذ البشرية، مع وجود الروبوت الذكي TARS الذاتي التفكير.", "lesson": "يبرز قوة البيانات، الفيزياء الحاسوبية، والذكاء الاصطناعي المتقدم في إدارة الأزمات الكونية.", "q": "ما اسم الروبوت الذكي الذي ساعد رواد الفضاء في الفيلم?", "a": "JARVIS", "b": "TARS", "c": "R2D2", "correct": "B"}
    ],
    "coding": [
        {"id": "social", "title": "👨‍💻 The Social Network", "story": "كيف قام مارك زوكربيرج بتحويل كود برميجي بسيط داخل غرفته بجامعة هارفارد إلى المنصة الأكبر عالمياً (فيسبوك).", "lesson": "يعلمك ريادة الأعمال التقنية، وكيف يغير التطوير البرمجي الفعلي حياة ملايين البشر.", "q": "ما هي المنصة العالمية التي ركز الفيلم على قصة تأسيسها؟", "a": "تويتر", "b": "جوجل", "c": "فيسبوك", "correct": "C"},
        {"id": "silicon", "title": "🏢 Silicon Valley (مسلسل)", "story": "مسلسل كوميدي تقني يحكي عن مهندسي برمجيات يحاولون بناء شركة ناشئة لخوارزميات ضغط البيانات في وادي السيليكون.", "lesson": "أدق عمل درامي يشرح بيئة عمل المبرمجين، صراعات الأكواد، وأنظمة التمويل والمستثمرين التقنيين.", "q": "ما هو مجال الخوارزمية الأساسية التي بنتها الشركة الناشئة بالمسلسل؟", "a": "ضغط البيانات", "b": "الأمن السيبراني", "c": "تطوير الألعاب", "correct": "A"}
    ],
    "cyber": [
        {"id": "robot", "title": "🔒 Mr. Robot (مسلسل)", "story": "مهندس أمن سيبراني عبقري مصاب باضطرابات نفسية يتم تجنيده من قبل منظمة هاكرز سرية لتدمير أكبر نظام مالي عالمي.", "lesson": "يعتبر المرجع الدرامي الأدق لعمليات الاختراق الحقيقية، واستخدام أنظمة Linux والشبكات وأمن المعلومات.", "q": "ما هو نظام التشغيل الأكثر استخداماً من قبل شخصيات الهكرز في هذا المسلسل؟", "a": "Windows", "b": "Linux", "c": "macOS", "correct": "B"},
        {"id": "snowden", "title": "👁️ Snowden", "story": "القصة الحقيقية لموظف وكالة الأمن القومي الأمريكية إدوارد سنودن الذي سرب تفاصيل آليات التجسس الرقمي السرية للعالم.", "lesson": "يفيدك جداً في فهم أبعاد الخصوصية الرقمية، التشفير، وحماية البيانات على الإنترنت.", "q": "ما هي الوكالة الحكومية التي كان يعمل بها إدوارد سنودن؟", "a": "وكالة الأمن القومي (NSA)", "b": "الفضاء (NASA)", "c": "الصحة العالمية", "correct": "A"},
        {"id": "hacker2016", "title": "💻 Hacker (2016)", "story": "مهاجر شاب يتجه إلى عالم الجريمة الإلكترونية والهاكينج لكسب المال ومساعدة عائلته ماديًا، ليدخل في صراع مع جهات ضخمة.", "lesson": "يوضح مخاطر الهندسة الاجتماعية، وكيف يمكن للثغرات البرمجية البسيطة أن تطيح بأنظمة بنكية كاملة.", "q": "ما هو الأسلوب النفسي الذي يعتمد على خداع الأشخاص للحصول على بياناتهم؟", "a": "التشفير المتماثل", "b": "الهندسة الاجتماعية", "c": "هجوم الحرمان من الخدمة", "correct": "B"},
        {"id": "wargames", "title": "🕹️ WarGames", "story": "هاكر شاب يخترق بالخطأ كمبيوترًا عملاقًا تابعًا للجيش الأمريكي مخصصًا للتنبؤ بالحروب النووية، ويبدأ اللعب معه دون أن يدري أنه قد يشعل حرباً عالمية.", "lesson": "فيلم كلاسيكي رائع يوضح بدايات مفهوم الأمن السيبراني، وأهمية حماية الأنظمة الحساسة من الاختراقات الخارجية.", "q": "ما الذي كان يحسب الفتى أنه يلعب معه عندما اخترق الكمبيوتر العملاق؟", "a": "لعبة كمبيوتر عادية", "b": "موقع بنكي", "c": "شات بوت ذكي", "correct": "A"}
    ]
}

def init_db():
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
            user_id INTEGER PRIMARY KEY, username TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 20, hints_count INTEGER DEFAULT 6, lang TEXT DEFAULT 'ar'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watched_movies (
            user_id INTEGER, movie_id TEXT, PRIMARY KEY (user_id, movie_id)
        )
    ''')
    conn.commit()
    conn.close()

def update_user_profile(user_id, username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user_profile (user_id, username, xp, level, coins, hints_count, lang) VALUES (?, ?, 0, 1, 20, 6, 'ar')", (user_id, username))
    else:
        cursor.execute("UPDATE user_profile SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, coins, hints_count, lang FROM user_profile WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 1, 20, 6, 'ar')

def set_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_profile SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def add_rewards(user_id, xp_amount, coins_amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, coins FROM user_profile WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    xp, level, coins = res if res else (0, 1, 20)
    new_xp = xp + xp_amount
    new_coins = coins + coins_amount
    new_level = (new_xp // 100) + 1
    cursor.execute("UPDATE user_profile SET xp = ?, level = ?, coins = ? WHERE user_id = ?", (new_xp, new_level, new_coins, user_id))
    conn.commit()
    conn.close()
    return new_level > level

def get_level_title(level, lang='ar'):
    if lang == 'ar':
        if level == 1: return "💤 مبتدئ كسلان"
        elif level == 2: return "🌱 طموح ناشئ"
        elif level == 3: return "🔨 محارب الإنتاجية"
        elif level == 4: return "🧠 وحش البرمجة"
        return "👑 الأستاذ العبقري الخارق"
    else:
        if level == 1: return "💤 Lazy Beginner"
        elif level == 2: return "🌱 Ambitious Novice"
        elif level == 3: return "🔨 Productivity Warrior"
        elif level == 4: return "🧠 Coding Beast"
        return "👑 Super Genius Master"

def main_menu_keyboard(lang='ar'):
    lang_dict = LOCALIZATION[lang]
    keyboard = [
        [InlineKeyboardButton(lang_dict["btn_tasks"], callback_data="submenu_tasks")],
        [InlineKeyboardButton(lang_dict["btn_quiz"], callback_data="submenu_quiz")],
        [InlineKeyboardButton(lang_dict["btn_ai"], callback_data="submenu_ai")],
        [InlineKeyboardButton(lang_dict["btn_movies"], callback_data="submenu_movies")],
        [InlineKeyboardButton(lang_dict["btn_leaderboard"], callback_data="menu_leaderboard"), InlineKeyboardButton(lang_dict["btn_shop"], callback_data="menu_shop")],
        [InlineKeyboardButton(lang_dict["btn_courses"], callback_data="submenu_courses"), InlineKeyboardButton(lang_dict["btn_pomodoro"], callback_data="menu_pomodoro")],
        [InlineKeyboardButton(lang_dict["btn_challenge"], callback_data="menu_daily_challenge")]
    ]
    return InlineKeyboardMarkup(keyboard)

def lang_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"), InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en")],
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="setlang_ru"), InlineKeyboardButton("Türkçe 🇹🇷", callback_data="setlang_tr")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_db()
    user = update.effective_user
    username = user.username or user.first_name
    update_user_profile(user.id, username)
    
    # واجهة اختيار اللغة أول مرة
    await update.message.reply_text(LOCALIZATION["ar"]["lang_select"], reply_markup=lang_menu_keyboard())

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([BotCommand("start", "🎯 Main Menu / القائمة الرئيسية")])

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    update_user_profile(user_id, username)
    
    xp, level, coins, hints, lang = get_profile(user_id)
    lang_dict = LOCALIZATION[lang]

    # ضبط واختيار اللغة
    if query.data.startswith("setlang_"):
        selected_lang = query.data.split("_")[1]
        set_user_lang(user_id, selected_lang)
        xp, level, coins, hints, lang = get_profile(user_id)
        lang_dict = LOCALIZATION[lang]
        title = get_level_title(level, lang)
        
        welcome_text = lang_dict["welcome"].format(name=query.from_user.first_name, level=level, title=title, xp=xp, coins=coins, hints=hints)
        await query.edit_message_text(welcome_text, reply_markup=main_menu_keyboard(lang), parse_mode="Markdown")
        return

    if query.data == "go_main":
        title = get_level_title(level, lang)
        text = lang_dict["main_menu"].format(level=level, title=title, xp=xp, coins=coins, hints=hints)
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))

    elif query.data == "submenu_tasks":
        keyboard = [[InlineKeyboardButton("➕ Add Task" if lang!='ar' else "➕ إضافة مهمة جديدة", callback_data="menu_add")], [InlineKeyboardButton("📋 View Tasks" if lang!='ar' else "📋 استعراض مهامك", callback_data="menu_view")], [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]
        await query.edit_message_text("💼 **| Tasks:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_add":
        context.user_data['action'] = 'waiting_for_task_name'
        await query.edit_message_text("✍️ Send task title:" if lang!='ar' else "✍️ أرسل الآن عنوان المهمة بالأسفل:")

    elif query.data == "menu_view":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_text, category, priority FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        if not tasks:
            await query.edit_message_text("🎉 No tasks pending." if lang!='ar' else "🎉 لا توجد مهام معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_tasks")]]))
        else:
            text = "📋 **Your Tasks:**\n\n" if lang!='ar' else "📋 **مهامك المسجلة حالياً:**\n\n"
            keyboard = []
            for idx, task in enumerate(tasks):
                t_id, t_text, cat, pri = task
                text += f"{idx+1}. {t_text}\n   📁 {cat} | 🚨 {pri}\n──────────────────\n"
                keyboard.append([InlineKeyboardButton(f"✅ Done {idx+1}", callback_data=f"delete_{t_id}")])
            keyboard.append([InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_tasks")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("cat_"):
        context.user_data['temp_cat'] = query.data.split("_")[1]
        keyboard = [[InlineKeyboardButton("🔥 High", callback_data="pri_high")], [InlineKeyboardButton("⏳ Med", callback_data="pri_med")], [InlineKeyboardButton("💤 Low", callback_data="pri_low")]]
        await query.edit_message_text("🚨 Priority:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pri_"):
        pri_text = query.data.split("_")[1]
        task_text = context.user_data.get('temp_name', 'Task')
        category_text = context.user_data.get('temp_cat', 'General')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task_text, category, priority, remind_time) VALUES (?, ?, ?, ?, ?)", (user_id, task_text, category_text, pri_text, "No Reminder"))
        conn.commit()
        conn.close()
        context.user_data.clear()
        add_rewards(user_id, 5, 2)
        await query.edit_message_text(f"✅ Saved! (+5 XP)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_tasks")]]))

    elif query.data.startswith("delete_"):
        task_id = int(query.data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        add_rewards(user_id, 25, 10)
        await query.edit_message_text("🎉 Completed! (+25 XP / +10 Coins)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="menu_view")]]))

    elif query.data == "submenu_quiz":
        await query.edit_message_text("📝 **Quiz Center:**\nSend text/PDF to generate a custom quiz up to 100 questions!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📁 Generate", callback_data="quiz_generate")], [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]))

    elif query.data == "quiz_generate":
        context.user_data['action'] = 'waiting_for_quiz_material'
        await query.edit_message_text("📚 Send content or upload PDF:")

    elif query.data.startswith("num_"):
        num_requested = int(query.data.split("_")[1])
        material = context.user_data.get('quiz_material', '')
        msg = await query.edit_message_text("⚡ Generating questions via Gemini AI...")
        
        try:
            prompt = (
                f"Based on this content, create exactly {num_requested} multiple choice questions in English or Arabic depending on context language.\n"
                f"Content:\n{material}\n\n"
                "Format EXACTLY like this for each block separated by ---\n"
                "Q: [Question text]\n"
                "A: [Option 1]\n"
                "B: [Option 2]\n"
                "C: [Option 3]\n"
                "D: [Option 4]\n"
                "Correct: [A, B, C or D]\n"
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
                text = f"✅ **Generated {count} questions!**\n\n📊 **Q1:**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
                keyboard = [[InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")], [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]]
                await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await msg.edit_text("⚠️ Content format failed, try again with clearer text.")
        except Exception as e:
            logger.error(f"Quiz Error: {e}")
            await msg.edit_text("❌ System error occurred.")

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
            feedback = "✅ Correct! (+10 XP / +5 Coins)"
        else:
            feedback = f"❌ Incorrect! Correct answer was: ({correct_choice})"

        next_idx = current_idx + 1
        cursor.execute("INSERT OR REPLACE INTO user_quiz_progress (user_id, current_question_index, score) VALUES (?, ?, ?)", (user_id, next_idx, current_score))
        conn.commit()

        cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_option FROM quizzes WHERE user_id = ? LIMIT 1 OFFSET ?", (user_id, next_idx))
        next_q = cursor.fetchone()
        conn.close()

        if next_q:
            q_text, oa, ob, oc, od, correct = next_q
            text = f"{feedback}\n\n📊 **Next Question ({next_idx + 1}):**\n{q_text}\n\n🇦 {oa}\n🇧 {ob}\n🇨 {oc}\n🇩 {od}"
            keyboard = [[InlineKeyboardButton("A", callback_data=f"quizans_A_{correct}"), InlineKeyboardButton("B", callback_data=f"quizans_B_{correct}")], [InlineKeyboardButton("C", callback_data=f"quizans_C_{correct}"), InlineKeyboardButton("D", callback_data=f"quizans_D_{correct}")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            add_rewards(user_id, 50, 20)
            await query.edit_message_text(f"{feedback}\n\n🎉 **Quiz Finished!**\n🏆 Score: {current_score}\nBonus: **+50 XP** & **+20 Coins**!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_main"], callback_data="go_main")]]))

    # --- [قسم الأفلام والسينما المطور] ---
    elif query.data == "submenu_movies":
        text = "🎬 **| Tech Cinema Room V2:**"
        keyboard = [
            [InlineKeyboardButton("🧠 AI", callback_data="movcat_ai")],
            [InlineKeyboardButton("👨‍💻 Coding & Startups", callback_data="movcat_coding")],
            [InlineKeyboardButton("🔒 Cyber Security & Hacking 🔥", callback_data="movcat_cyber")],
            [InlineKeyboardButton("🎲 Random Suggestion", callback_data="mov_random")],
            [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("movcat_"):
        category_name = query.data.split("_")[1]
        text = f"🎬 **List:**"
        keyboard = []
        for movie in MOVIES_DATABASE[category_name]:
            keyboard.append([InlineKeyboardButton(movie["title"], callback_data=f"viewmov_{category_name}_{movie['id']}")])
        keyboard.append([InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_movies")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "mov_random":
        all_cats = list(MOVIES_DATABASE.keys())
        rand_cat = random.choice(all_cats)
        rand_movie = random.choice(MOVIES_DATABASE[rand_cat])
        query.data = f"viewmov_{rand_cat}_{rand_movie['id']}"

    if query.data.startswith("viewmov_"):
        _, cat, m_id = query.data.split("_")
        movie_data = next((m for m in MOVIES_DATABASE[cat] if m["id"] == m_id), None)
        if movie_data:
            m_text = f"🎬 **{movie_data['title']}**\n\n📌 **Story:** {movie_data['story']}\n\n💡 **Lesson:** {movie_data['lesson']}"
            keyboard = [
                [InlineKeyboardButton("🎯 Answer Verification Quiz", callback_data=f"movcheck_{cat}_{m_id}")],
                [InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_movies")]
            ]
            await query.edit_message_text(m_text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("movcheck_"):
        _, cat, m_id = query.data.split("_")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM watched_movies WHERE user_id = ? AND movie_id = ?", (user_id, m_id))
        if cursor.fetchone():
            conn.close()
            await query.edit_message_text("⚠️ Already claimed rewards!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_movies")]]))
            return
        conn.close()
        movie_data = next((m for m in MOVIES_DATABASE[cat] if m["id"] == m_id), None)
        if movie_data:
            q_text = f"🎯 **Quiz for ({movie_data['title']}):**\n\n{movie_data['q']}\n\n🇦 {movie_data['a']}\n🇧 {movie_data['b']}\n🇨 {movie_data['c']}"
            keyboard = [[InlineKeyboardButton("A", callback_data=f"movans_A_{movie_data['correct']}_{m_id}"), InlineKeyboardButton("B", callback_data=f"movans_B_{movie_data['correct']}_{m_id}"), InlineKeyboardButton("C", callback_data=f"movans_C_{movie_data['correct']}_{m_id}")]]
            await query.edit_message_text(q_text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("movans_"):
        _, choice, correct, m_id = query.data.split("_")
        if choice == correct:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO watched_movies (user_id, movie_id) VALUES (?, ?)", (user_id, m_id))
            conn.commit()
            conn.close()
            add_rewards(user_id, 20, 5)
            await query.edit_message_text("🎉 Correct! (+20 XP / +5 Coins)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_movies")]]))
        else:
            await query.edit_message_text("❌ Incorrect answer! Try again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_movies")]]))

    # --- [تحدي اليوم البرمجي الخارق] ---
    elif query.data == "menu_daily_challenge":
        msg = await query.edit_message_text("⚡ Fetching coding challenge...")
        try:
            prompt = f"Give a short, exciting coding challenge question in language code {lang} with two multiple choice options. Do not include answers inside the text block directly."
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            await msg.edit_text(f"🔥 **Challenge:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]))
        except Exception:
            await msg.edit_text("🔥 Python Challenge:\n`print(type(5.0))`\n\n🇦 int\n🇧 float\n\nCorrect is 🇧!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]))

    # --- [قسم كورسات البرمجة المطور] ---
    elif query.data == "submenu_courses":
        text = "📚 **Elzero Programming Playlists:**"
        keyboard = [
            [InlineKeyboardButton("🐍 Elzero Python Playlist", url=ELZERO_PYTHON_PLAYLIST)],
            [InlineKeyboardButton("💻 Elzero C++ Playlist ✨", url=ELZERO_CPP_PLAYLIST)],
            [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # --- بقية الأقسام الثابتة ---
    elif query.data == "menu_leaderboard":
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, level, xp FROM user_profile ORDER BY xp DESC LIMIT 10")
        top_users = cursor.fetchall()
        conn.close()
        text = "🏆 **Leaderboard:**\n──────────────────\n"
        for idx, user_row in enumerate(top_users):
            uname, lvl, u_xp = user_row
            text += f"{idx+1}. @{uname} -> Lvl: {lvl} ({u_xp} XP)\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]))

    elif query.data == "menu_shop":
        text = f"🏪 **Shop:**\n🪙 Coins: {coins}\n💡 Hints: {hints}"
        keyboard = [[InlineKeyboardButton("💡 Buy Hints (30 C)", callback_data="buy_hints")], [InlineKeyboardButton("✨ Buy XP (50 C)", callback_data="buy_xp")], [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "buy_hints":
        if coins >= 30:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET coins = coins - 30, hints_count = hints_count + 3 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await query.edit_message_text("✅ Purchased successfully!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="menu_shop")]]))
        else:
            await query.edit_message_text("❌ Not enough coins!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="menu_shop")]]))

    elif query.data == "buy_xp":
        if coins >= 50:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET coins = coins - 50 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            add_rewards(user_id, 50, 0)
            await query.edit_message_text("✅ +50 XP Added!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="menu_shop")]]))
        else:
            await query.edit_message_text("❌ Not enough coins!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="menu_shop")]]))

    elif query.data == "submenu_ai":
        keyboard = [[InlineKeyboardButton("🧠 Tasks Split", callback_data="ai_split")], [InlineKeyboardButton("📝 Summarize", callback_data="ai_summarize")], [InlineKeyboardButton("💡 Tip", callback_data="ai_tips")], [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]
        await query.edit_message_text("🤖 **AI Tools:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ai_split":
        context.user_data['action'] = 'waiting_for_ai_split'
        await query.edit_message_text("🤔 Write complex task text:")

    elif query.data == "ai_summarize":
        context.user_data['action'] = 'waiting_for_summary_material'
        await query.edit_message_text("📝 Send text or upload PDF:")

    elif query.data == "ai_tips":
        msg = await query.edit_message_text("⚡ Fetching motivation tip...")
        try:
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"Give a short programming motivation tip in language {lang}")
            await msg.edit_text(f"💡 **Tip:**\n\n{response.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_ai")]]))
        except Exception:
            await msg.edit_text("Start with the 5-minute rule! 🚀", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="submenu_ai")]]))

    elif query.data == "menu_pomodoro":
        await query.edit_message_text("⏱️ **Pomodoro Timer:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏱️ Start 25m Jolt", callback_data="pomo_start")], [InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]))

    elif query.data == "pomo_start":
        await query.edit_message_text("🚀 Pomodoro started! Focus for 25 mins. 💪", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang_dict["btn_back"], callback_data="go_main")]]))

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')
    user_text = update.message.text

    if action == 'waiting_for_task_name':
        context.user_data['temp_name'] = user_text
        context.user_data['action'] = None
        keyboard = [[InlineKeyboardButton("Work", callback_data="cat_work"), InlineKeyboardButton("Study", callback_data="cat_study")]]
        await update.message.reply_text("📁 Select Category:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'waiting_for_ai_split':
        waiting_msg = await update.message.reply_text("🧠 Splitting via AI...")
        context.user_data['action'] = None
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"Split this task: '{user_text}' into 3 simple actionable steps.")
        await waiting_msg.reply_text(f"🧠 **Plan:**\n\n{response.text}")

    elif action == 'waiting_for_summary_material':
        waiting_msg = await update.message.reply_text("⚡ Summarizing...")
        context.user_data['action'] = None
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"Summarize the following text neatly:\n\n{user_text}")
        await waiting_msg.reply_text(f"📝 **Summary:**\n\n{response.text}")

    elif action == 'waiting_for_quiz_material':
        context.user_data['quiz_material'] = user_text
        context.user_data['action'] = None
        keyboard = [[InlineKeyboardButton("5 Qs 📊", callback_data="num_5"), InlineKeyboardButton("10 Qs 📋", callback_data="num_10")]]
        await update.message.reply_text("🎛️ Select number of questions to generate:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🤖 Please use keyboard menus to communicate.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')
    doc = update.message.document

    if action in ['waiting_for_quiz_material', 'waiting_for_summary_material']:
        waiting_msg = await update.message.reply_text("📥 Reading PDF document, hold on...")
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
                extracted_text = f"[Uploaded Document: {file_name}]"
                
            if not extracted_text.strip():
                extracted_text = "Educational study material block."

            if os.path.exists(local_path):
                os.remove(local_path)

            if action == 'waiting_for_quiz_material':
                context.user_data['quiz_material'] = extracted_text
                context.user_data['action'] = None
                keyboard = [[InlineKeyboardButton("5 Qs 📊", callback_data="num_5"), InlineKeyboardButton("10 Qs 📋", callback_data="num_10")]]
                await waiting_msg.delete()
                await update.message.reply_text("📊 **PDF Processed!** Choose number of questions:", reply_markup=InlineKeyboardMarkup(keyboard))
            
            elif action == 'waiting_for_summary_material':
                context.user_data['action'] = None
                response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"Summarize this text thoroughly:\n\n{extracted_text}")
                await waiting_msg.reply_text(f"📝 **Summary:**\n\n{response.text}")
        except Exception as e:
            logger.error(f"PDF Error: {e}")
            await waiting_msg.edit_text("❌ Error processing PDF file.")

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
