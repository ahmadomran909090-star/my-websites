#!/usr/bin/env python, 3
# -*- coding: utf-8 -*-

"""
==========================================================================================
              🌟 THE ULTIMATE MULTI-LANGUAGE PRODUCTIVITY & ACADEMIC BOT 🌟
==========================================================================================
Core Features Built-in:
1. Advanced User Profile & Multi-Language Engine (EN, AR, RU).
2. SQLite3 Robust Local Database Persistence for Users, Tasks, Ideas, and Links.
3. Fully Interactive Task Manager (Add, Categorize, Complete, Delete, and Query Tasks).
4. AI Quiz Generator from Raw Text with Google Gemini Structured Output (JSON Mapping).
5. Interactive PDF Parsing and Automated Document-to-Quiz Framework using PyPDF.
6. Technical Cinema Streaming Hub with Categorized Watchlist Link Matching.
7. Real-Time Async Pomodoro Focus Engine with Integrated Job Queue Notifications.
8. Background Ambient Focus Sound Stream Links.
9. Structured Multi-Tier Book Summarizer with Actionable Implementation Roadmaps.
10. AI Code Bug Fixer, Structural Optimizer, and Multi-Language Explainer.
11. Advanced Link Saver & Dynamic Category Brain Dump Repository.
12. Integrated Language Learning Hub for Learn Russian (🇷🇺) with Direct YouTube Linking.
13. Integrated Language Learning Hub for Learn Turkish (🇹🇷) with Direct YouTube Linking.
14. AI Side-Project Architecture Generator with Technology Stack Blueprints.
15. 24-Hour Gamified Discipline & High-Energy Productivity Challenge Matrix.
16. AI Resume & Professional Corporate Biography Optimizer (LinkedIn-Ready).
17. Intelligent Fallback AI Personal Assistant Continuous Conversational Streaming Mode.
==========================================================================================
"""

import os
import sys
import logging
import sqlite3
import json
import random
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

# استيراد مكتبات تليجرام المتقدمة
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    BotCommand, 
    MenuButtonCommands,
    WebAppInfo
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    JobQueue
)

# استيراد عميل Google GenAI المطور
from google import genai
from google.genai import types

# إعداد السجلات التفصيلية لمراقبة البوت عبر بيئات السحابية مثل Railway
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot_execution_core.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# ==========================================================================================
# 📋 القسم 1: إعداد الثوابت، المتغيرات البيئية والمصادر
# ==========================================================================================

TELEGRAM_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    logger.critical("🛑 CRITICAL ERROR: Environment variables TELEGRAM_BOT_TOKEN or GEMINI_API_KEY are missing!")
    sys.exit("Execution halted due to missing structural environmental keys.")

# إنشاء العميل لـ Google GenAI
ai_client = genai.Client(api_key=GEMINI_KEY)

# ملفات قواعد البيانات والمستندات المؤقتة
DB_FILE: str = "productivity_platform.db"

# روابط قنوات ومصادر تعلم اللغات من اليوتيوب المعتمدة
RUSSIAN_COURSE_1: str = "https://www.youtube.com/playlist?list=PLpZceNenEemqS_X_u8bLwFfS768Sg0mCl" # Be Fluent Beginner
RUSSIAN_COURSE_2: str = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAxVscH9vLz_vbZ6v9_wA99t" # لغة روسية بالعربي
TURKISH_COURSE_1: str = "https://www.youtube.com/playlist?list=PL-Wb0bZ2D80T9gBvS9vK36_C_yL7o8I5L" # تعلم التركية من الصفر
TURKISH_COURSE_2: str = "https://www.youtube.com/playlist?list=PL_Xv_uS8p_hmYOnF5w90qshv9D_S1Lp_j" # كورس تركي مكثف

# قاعدة بيانات أفلام التكنولوجيا الشاملة وروابط البحث التلقائي عنها
MOVIES_DATABASE: Dict[str, List[Dict[str, str]]] = {
    "ai": [
        {"id": "imitation_game", "title": "🧠 The Imitation Game (2014)", "search_url": "https://www.google.com/search?q=The+Imitation+Game+watch+online"},
        {"id": "interstellar", "title": "🚀 Interstellar (2014)", "search_url": "https://www.google.com/search?q=Interstellar+watch+online"},
        {"id": "ex_machina", "title": "🤖 Ex Machina (2014)", "search_url": "https://www.google.com/search?q=Ex+Machina+watch+online"},
        {"id": "her_movie", "title": "🗣️ Her (2013)", "search_url": "https://www.google.com/search?q=Her+movie+watch+online"}
    ],
    "coding": [
        {"id": "social_network", "title": "👨‍💻 The Social Network (2010)", "search_url": "https://www.google.com/search?q=The+Social+Network+watch+online"},
        {"id": "silicon_valley", "title": "🏢 Silicon Valley Series (2014-2019)", "search_url": "https://www.google.com/search?q=Silicon+Valley+series+watch+online"},
        {"id": "pirates_silicon", "title": "🏴‍☠️ Pirates of Silicon Valley (1999)", "search_url": "https://www.google.com/search?q=Pirates+of+Silicon+Valley+watch+online"},
        {"id": "jobs_movie", "title": "🍏 Jobs (2013)", "search_url": "https://www.google.com/search?q=Jobs+movie+watch+online"}
    ],
    "cyber": [
        {"id": "mr_robot", "title": "🔒 Mr. Robot Series (2015-2019)", "search_url": "https://www.google.com/search?q=Mr+Robot+series+watch+online"},
        {"id": "snowden", "title": "👁️ Snowden (2016)", "search_url": "https://www.google.com/search?q=Snowden+movie+watch+online"},
        {"id": "matrix_trilogy", "title": "🕶️ The Matrix (1999)", "search_url": "https://www.google.com/search?q=The+Matrix+1999+watch+online"},
        {"id": "wargames", "title": "📟 WarGames (1983)", "search_url": "https://www.google.com/search?q=WarGames+1983+watch+online"}
    ]
}

# ==========================================================================================
# 🌐 القسم 2: القاموس الضخم المتكامل للغات (English, العربية, Русский)
# ==========================================================================================

LANG_DICT: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "🎯 <b>Welcome {name} to the Ultimate Productivity & Growth Framework!</b>\n\nYour centralized automated dashboard is initialized successfully. Harness the combined power of Google Gemini, SQLite persistence, academic testing protocols, and professional career builders to transform your workflow.",
        "main_menu": "🎯 <b>Main Automation Control Panel:</b>\nSelect any system sector below to begin:",
        "btn_tasks": "📁 Task Management Terminal",
        "btn_quiz": "🧠 Interactive AI Quiz Architect",
        "btn_tools": "🤖 Software Engineering & Study Tools",
        "btn_growth": "🚀 AI Growth & Professional Hub",
        "btn_cinema": "🎬 Tech Cinema & Streaming Index",
        "btn_pomo": "⏱️ Async Pomodoro Focus Matrix",
        "btn_links": "🔖 Dynamic Link Saver & Brain Dump",
        "btn_russian": "🇷🇺 Language Hub: Learn Russian",
        "btn_turkish": "🇹🇷 Language Hub: Learn Turkish",
        "btn_lang": "⚙️ Change Global Language Settings",
        "chat_ai_status": "🤖 <b>Conversational LLM Mode Active:</b>\nYou can chat with me directly in natural text at any time for assistant support, code reviews, or educational inquiries.",
        "pomo_started": "🚀 <b>Asynchronous Pomodoro Engine Activated!</b>\nFocus session set for 25 minutes. Do not break concentration. Visual and acoustic barriers should be maintained. I will notify you upon expiration. 💪",
        "pomo_done": "🔔 <b>Focus Cycle Completed!</b>\nYour 25-minute Pomodoro focus matrix has concluded successfully. Step away from your workbench, breathe, and take a 5-minute cognitive break! ☕",
        "task_title_prompt": "✍️ <b>Enter Task Parameters:</b>\nPlease type the title/description of your new production task below:",
        "task_added": "✅ Task successfully recorded and indexed into your local persistent database schema!",
        "no_tasks": "🎉 Excellence achieved! You have no pending or unfulfilled tasks inside your database terminal right now.",
        "back": "🔙 Return to Previous Screen",
        "lang_hub_title": "📚 <b>Integrated Language Learning Portals:</b>\nSelect one of the validated syllabus-mapped training courses on YouTube to launch:",
        "course_rus_1": "🇷🇺 Russian Foundational Course (Be Fluent)",
        "course_rus_2": "🇷🇺 Russian Explanations (Arabic Medium)",
        "course_tur_1": "🇹🇷 Turkish Comprehensive Level 1 (From Zero)",
        "course_tur_2": "🇹🇷 Turkish Core Grammar & Conversational Structures",
        "brain_dump_prompt": "💡 <b>Ephemeral Brain Dump Station:</b>\nSend any raw thought, intellectual spark, or note to cache it inside your persistent storage system:",
        "link_saver_prompt": "🔖 <b>Archival Link Hub:</b>\nSend any website URL, documentation file, or reference repository link to preserve it securely:",
        "book_prompt": "📚 <b>Advanced Book Blueprint Engine:</b>\nSend the precise title of any non-fiction literature to extract structural summaries and implementation guides:",
        "growth_title": "🚀 <b>AI Growth & Professional Calibration Hub:</b>\nUtilize specialized neural prompts to enhance your portfolio, resume, and discipline index:",
        "btn_side_project": "💡 Side-Project Architecture Generator",
        "btn_challenge": "🎯 24-Hour Gamified Discipline Matrix",
        "btn_cv_optimizer": "📝 Executive CV & Bio Phrasing Builder",
        "quiz_prompt": "🧠 <b>AI Quiz Generator (PDF/Text Engine):</b>\nSend a block of instructional text or upload a structural PDF file to extract highly analytical multi-choice questions with dynamic validation schemas.",
        "generic_error": "⚠️ An internal execution error occurred inside the handler pipeline. Please re-trigger the action state."
    },
    "ar": {
        "welcome": "🎯 <b>أهلاً بك يا {name} في المنظومة الإنتاجية والأكاديمية الخارقة المحدثة!</b>\n\nتم تهيئة لوحة التحكم المركزية الآلية بنجاح. استفد الآن من القوة المشتركة للذكاء الاصطناعي التوليدي ونظام قواعد البيانات المستقل لحفظ المهام والأفكار وبناء مستقبلك المهني والأكاديمي الحين.",
        "main_menu": "🎯 <b>لوحة التحكم والأتمتة الرئيسية:</b>\nاختر أحد الأقسام التكنولوجية بالأسفل للبدء والمتابعة:",
        "btn_tasks": "📁 محطة إدارة وجدولة المهام والتنبيهات",
        "btn_quiz": "🧠 مركز الكويزات الذكي واختبارات الـ PDF",
        "btn_tools": "🤖 أدوات المطور، فحص الأكواد والدراسة بالـ AI",
        "btn_growth": "🚀 مركز التطوير المهني والتحفيز الذكي",
        "btn_cinema": "🎬 سينما التكنولوجيا وروابط الفحص والمشاهدة",
        "btn_pomo": "⏱️ مؤقت بومودورو الآلي وأصوات التركيز",
        "btn_links": "🔖 مستودع الروابط المؤرشفة ومفكرة الأفكار",
        "btn_russian": "🇷🇺 بوابة تعلم اللغة الروسية من الصفر",
        "btn_turkish": "🇹🇷 بوابة تعلم اللغة التركية من الصفر",
        "btn_lang": "⚙️ تغيير لغة النظام / Change Global Language",
        "chat_ai_status": "🤖 <b>وضع المساعد الشخصي والمحاكاة المباشرة نشط:</b>\nيمكنك إرسال أي نص أو كود أو سؤال عام للبوت مباشرة في أي وقت دون قيود ليقوم بمساعدتك فوراً.",
        "pomo_started": "🚀 <b>تم تفعيل محرك البومودورو والتركيز بنجاح!</b>\nبدأت الجلسة الحين لمدة 25 دقيقة. يرجى عزل نفسك تماماً عن المشتتات والبيئات المحيطة وسأقوم بإرسال إشعار لك فور انتهاء الوقت. 💪",
        "pomo_done": "🔔 <b>انتهت دورة التركيز بنجاح واكتمال!</b>\nانتهت جلسة البومودورو (25 دقيقة) الحين. اترك شاشة العمل ومفاتيح التطوير، خذ نفساً عميقاً واستمتع باستراحة كوجنيتيف قصيرة لمدة 5 دقائق! ☕",
        "task_title_prompt": "✍️ <b>إدخال معالم المهمة الجديدة:</b>\nيرجى كتابة عنوان أو تفاصيل المهمة المراد إضافتها في قاعدة البيانات بالأسفل:",
        "task_added": "✅ تم تسجيل المهمة بنجاح وفهرستها داخل جدول البيانات المستقل الخاص بك الحين!",
        "no_tasks": "🎉 تهانينا! جدولك نظيف تماماً ولا توجد مهام معلقة أو غير منجزة في قاعدة بياناتك الحالية.",
        "back": "🔙 العودة للقائمة السابقة",
        "lang_hub_title": "📚 <b>مراكز تعلم اللغات العالمية (يوتيوب):</b>\nاختر أحد السلاسل والكورسات المعتمدة والمبنية على مناهج أكاديمية لبدء الدراسة الحين:",
        "course_rus_1": "🇷🇺 كورس اللغة الروسية التأسيسي للمبتدئين (Be Fluent)",
        "course_rus_2": "🇷🇺 كورس روسي متكامل (باللغة العربية من الصفر)",
        "course_tur_1": "🇹🇷 كورس اللغة التركية الشامل للمستوى الأول (من الصفر)",
        "course_tur_2": "🇹🇷 كورس قواعد ومحادثات اللغة التركية المكثف",
        "brain_dump_prompt": "💡 <b>محطة تفريغ الأفكار والخواطر السريعة:</b>\nأرسل أي فكرة خاطرة، مسودة مشروع، أو خاطرة علمية لحفظها على الفور في ذاكرة البوت الدائمة الحين:",
        "link_saver_prompt": "🔖 <b>مستودع أرشفة الروابط الهامة:</b>\nأرسل أي رابط لموقع، توثيق برمجى، أو مستودع أكواد ليتم حفظه بشكل منظم الحين:",
        "book_prompt": "📚 <b>محرك توليد مخططات الكتب العالمية:</b>\nأرسل الاسم الدقيق لأي كتاب علمي أو تطويري لاستخراج ملخصه الهيكلي وآليات تطبيقه فوراً:",
        "growth_title": "🚀 <b>بوابة التطوير والتحفيز وتوليد المسارات الاحترافية:</b>\nاستخدم الميزات العصبية المتقدمة لبناء ملفك المهني، تحسين سيرتك الذاتية وتحدي انضباطك اليومي:",
        "btn_side_project": "💡 مولد بنية المشاريع الجانبية والمحافظ الشخصية",
        "btn_challenge": "🎯 تحدي الـ 24 ساعة لرفع مستويات الانضباط",
        "btn_cv_optimizer": "📝 مصحح ومطور عبارات السير الذاتية والـ Bio الاحترافي",
        "quiz_prompt": "🧠 <b>مركز توليد الاختبارات الذكي (نص / PDF):</b>\nأرسل نصاً تعليمياً أو قم برفع ملف PDF الحين ليقوم الذكاء الاصطناعي ببناء اختبار متعدد الخيارات مهيكل بالكامل مع نموذج إجابة دقيق وصارم.",
        "generic_error": "⚠️ حدث خطأ داخلي في معالجة البيانات، يرجى إعادة تفعيل الزر أو الطلب مرة أخرى."
    },
    "ru": {
        "welcome": "🎯 <b>Добро пожаловать, {name}, в Единую Платформу Продуктивности и Развития!</b>\n\nВаша централизованная автоматизированная панель управления успешно инициализирована. Используйте мощь Google Gemini, базы данных SQLite и профессиональных инструментов для трансформации ваших ежедневных задач.",
        "main_menu": "🎯 <b>Главная Панель Управления Автоматизацией:</b>\nВыберите системный сектор ниже, чтобы начать работу:",
        "btn_tasks": "📁 Диспетчер задач и напоминаний",
        "btn_quiz": "🧠 Интеллектуальный AI-генератор тестов",
        "btn_tools": "🤖 Инструменты разработчика и обучения",
        "btn_growth": "🚀 Центр профессионального развития и мотивации",
        "btn_cinema": "🎬 Технокино и индекс трансляций",
        "btn_pomo": "⏱️ Асинхронный таймер Помодоро",
        "btn_links": "🔖 Сохранение ссылок и банк идей",
        "btn_russian": "🇷🇺 Изучение русского языка",
        "btn_turkish": "🇹🇷 Изучение турецкого языка",
        "btn_lang": "⚙️ Изменить глобальные языковые настройки",
        "chat_ai_status": "🤖 <b>Режим AI-ассистента активен:</b>\nВы можете общаться со мной напрямую в любое время для получения помощи, обзора кода или ответов на вопросы.",
        "pomo_started": "🚀 <b>Таймер Помодоро активирован!</b>\nФокусируйтесь на задаче в течение 25 минут. Я пришлю вам уведомление по окончании сессии. 💪",
        "pomo_done": "🔔 <b>Сессия фокуса завершена!</b>\nВаш 25-минутный цикл Помодоро успешно завершен. Сделайте перерыв на 5 минут! ☕",
        "task_title_prompt": "✍️ <b>Введите параметры задачи:</b>\nОтправьте название или описание вашей новой задачи ниже:",
        "task_added": "✅ Задача успешно сохранена в локальной базе данных!",
        "no_tasks": "🎉 Отлично! У вас нет невыполненных задач в базе данных на данный момент.",
        "back": "🔙 Назад",
        "lang_hub_title": "📚 <b>Изучение языков:</b>\nВыберите курс на YouTube для начала обучения:",
        "course_rus_1": "🇷🇺 Русский для начинающих (Be Fluent)",
        "course_rus_2": "🇷🇺 Курс русского языка (на арабском)",
        "course_tur_1": "🇹🇷 Турецкий с нуля (Полный курс)",
        "course_tur_2": "🇹🇷 Турецкая грамматика и разговорная речь",
        "brain_dump_prompt": "💡 <b>Быстрые заметки и идеи:</b>\nОтправьте любую мысль для сохранения в базе данных:",
        "link_saver_prompt": "🔖 <b>Сохранение ссылок:</b>\nОтправьте ссылку для ее безопасного архивирования:",
        "book_prompt": "📚 <b>Анализ книг:</b>\nОтправьте название книги для получения краткого содержания и уроков:",
        "growth_title": "🚀 <b>Центр развития и карьерной калибровки:</b>\nИспользуйте инструменты ИИ для улучшения резюме, портфолио и самодисциплины:",
        "btn_side_project": "💡 Генератор идей для сайд-проектов",
        "btn_challenge": "🎯 24-часовой вызов дисциплины",
        "btn_cv_optimizer": "📝 Оптимизатор резюме и профилей LinkedIn",
        "quiz_prompt": "🧠 <b>Генератор тестов (Текст / PDF):</b>\nОтправьте текст или загрузите PDF для генерации интерактивного теста.",
        "generic_error": "⚠️ Произошла внутренняя ошибка. Пожалуйста, попробуйте еще раз."
    }
}

# ==========================================================================================
# 🗄️ القسم 3: إدارة وإعداد هياكل وجداول قاعدة البيانات (SQLite3 Engine)
# ==========================================================================================

def database_bootstrap() -> None:
    """
    تقوم بإنشاء وتهيئة جداول قاعدة البيانات المستقلة والفهارس لضمان سرعة الاستعلام
    والحفاظ على بيانات مستخدمي المنصة بشكل دائم عبر عمليات الإيقاف والتشغيل.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 1. جدول الحسابات والملفات الشخصية للمستخدمين واللغات المفضلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lang TEXT DEFAULT 'en',
                registration_date TEXT
            )
        ''')
        
        # 2. جدول نظام إدارة وجدولة المهام والتنبيهات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_text TEXT NOT NULL,
                priority TEXT DEFAULT 'Medium',
                created_at TEXT
            )
        ''')
        
        # 3. جدول مفكرة الأفكار السريعة وتفريغ العقول
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brain_dump (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                note_text TEXT NOT NULL,
                timestamp TEXT
            )
        ''')
        
        # 4. جدول الأرشفة السليمة والمستودعات والروابط المهمة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                link_url TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                archived_at TEXT
            )
        ''')
        
        # إنشاء الفهارس لرفع أداء وسرعة الاستعلامات عبر الـ User ID
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_user ON user_profile(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dump_user ON brain_dump(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_user ON saved_links(user_id)')
        
        conn.commit()
        logger.info("💾 Local SQLite persistent database schema bootstrapped and checked successfully.")
    except sqlite3.Error as db_error:
        logger.critical(f"🛑 Critical structural database fail during bootstrap operation: {db_error}")
    finally:
        conn.close()

def get_user_lang(user_id: int) -> str:
    """تستعلم وتجلب الاختصار الخاص باللغة المفضلة للمستخدم الحالية من قاعدة البيانات."""
    lang_code = 'en'
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT lang FROM user_profile WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0] in LANG_DICT:
            lang_code = result[0]
    except sqlite3.Error as e:
        logger.error(f"Error reading user lang cache parameters for user {user_id}: {e}")
    finally:
        conn.close()
    return lang_code

def set_user_lang(user_id: int, username: Optional[str], lang: str) -> None:
    """تقوم بإنشاء ملف تعريف جديد أو تحديث اللغة العالمية المفضلة للمستخدم مباشرة."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO user_profile (user_id, username, lang, registration_date)
            VALUES (?, ?, ?, COALESCE((SELECT registration_date FROM user_profile WHERE user_id = ?), ?))
        ''', (user_id, username, lang, user_id, now_str))
        conn.commit()
        logger.info(f"🌐 User {user_id} profile calibrated language tracking token to: '{lang}'")
    except sqlite3.Error as e:
        logger.error(f"Failed to commit user language updates for user {user_id}: {e}")
    finally:
        conn.close()

# ==========================================================================================
# ⌨️ القسم 4: توليد لوحات المفاتيح التفاعلية والأزرار البرمجية الشاملة
# ==========================================================================================

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """تقوم بتشييد وهندسة لوحة التحكم والمفاتيح الأساسية للبوت تليجرام بناء على لغة العرض."""
    keyboard = [
        [InlineKeyboardButton(LANG_DICT[lang]["btn_tasks"], callback_data="submenu_tasks")],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_quiz"], callback_data="submenu_quiz")],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_tools"], callback_data="submenu_tools")],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_growth"], callback_data="submenu_growth")],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_cinema"], callback_data="submenu_movies")],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_pomo"], callback_data="submenu_pomo")],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_links"], callback_data="submenu_links")],
        [
            InlineKeyboardButton(LANG_DICT[lang]["btn_russian"], callback_data="submenu_russian"),
            InlineKeyboardButton(LANG_DICT[lang]["btn_turkish"], callback_data="submenu_turkish")
        ],
        [InlineKeyboardButton(LANG_DICT[lang]["btn_lang"], callback_data="menu_lang")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main_button(lang: str) -> InlineKeyboardMarkup:
    """مولد زر العودة الفردي الموحد لتوفير مساحة الكود والرجوع السلس."""
    return InlineKeyboardMarkup([[InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]])

# ==========================================================================================
# 🚀 القسم 5: الأوامر البرمجية الأساسية ومعالجات التهيئة الأولى للبوت
# ==========================================================================================

async def command_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """المعالج الأساسي لأمر الاستهلال البدء وتوليد واجهة الترحيب الفخمة وتحديد اللغات."""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # التحقق التلقائي وبناء ملف المستخدم داخل قاعدة البيانات
    lang = get_user_lang(user_id)
    set_user_lang(user_id, username, lang)
    
    welcome_message = (
        LANG_DICT[lang]["welcome"].format(name=update.effective_user.first_name) + 
        "\n\n" + LANG_DICT[lang]["chat_ai_status"]
    )
    
    await update.message.reply_text(
        text=welcome_message,
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML"
    )

async def application_post_init(application: Application) -> None:
    """تقوم بتهيئة وتحديث أوامر البوت والأوصاف العامة والشاشات الترحيبية بلغات متعددة تلقائياً."""
    try:
        # تهيئة الأوصاف التلقائية لقوائم تليجرام العامة
        await application.bot.set_my_description(
            description="Welcome! Your Ultimate Multi-Language Productivity Hub. Manage tasks, use AI chat, learn Russian/Turkish, generate quizzes from PDFs, and track Pomodoro. Click /start to run!",
            language_code="en"
        )
        await application.bot.set_my_description(
            description="مرحباً بك في منصة الإنتاجية المتكاملة المطعمة بالذكاء الاصطناعي! يمكنك تنظيم مهامك، محاكاة الـ AI بحرية، تعلم الروسية والتركية، تحويل ملفات الـ PDF لاختبارات، وتنشيط التطوير الاحترافي. اضغط /start للانطلاق!",
            language_code="ar"
        )
        # تحديد الأوامر المتاحة داخل زر الـ Menu الجانبي
        await application.bot.set_my_commands([
            BotCommand("start", "🎯 Main Menu / لوحة التحكم الرئيسية")
        ])
        logger.info("🤖 Global bot descriptions and command manifests synchronized successfully with Telegram server.")
    except Exception as env_err:
        logger.error(f"Failed to set high-level server parameters or bot layout descriptions: {env_err}")

# ==========================================================================================
# 🎛️ القسم 6: المحرك المركزي المتقدم لمعالجة الضغطات والـ Callbacks التفاعلية
# ==========================================================================================

async def main_callback_query_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الموزع والراوتر المركزي لجميع أحداث نقرات الأزرار المضمنة Inline الكبيرة والفرعية."""
    query = update.callback_query
    if not query or not query.from_user:
        return

    user_id = query.from_user.id
    lang = get_user_lang(user_id)
    
    # تجنب مشاكل انتهاء وقت النقر في واجهات تليجرام الرسمية
    try:
        await query.answer()
    except Exception:
        pass

    data_payload = query.data
    logger.info(f"📥 Query Callback Event Registered: Code Token '{data_payload}' issued by user id: {user_id}")

    # 1. الرجوع المباشر للقائمة الرئيسية
    if data_payload == "go_main":
        context.user_data.clear() # تصفية الحالات المؤقتة للمستخدم لتفادي تداخل العمليات
        await query.edit_message_text(
            text=LANG_DICT[lang]["main_menu"],
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )

    # 2. لوحة مفاتيح اختيار وتعديل اللغة للنظام بأكمله
    elif data_payload == "menu_lang":
        keyboard = [
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
                InlineKeyboardButton("🇦🇪 العربية", callback_data="setlang_ar"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru")
            ],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text="🌐 <b>Global Language Configuration / إعدادات اللغة العالمية / Выберите глобальный язык:</b>\n\nSelect your primary instruction token below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    # 3. معالجة وحفظ تغير اللغة
    elif data_payload.startswith("setlang_"):
        extracted_lang = data_payload.split("_")[1]
        username_str = query.from_user.username or query.from_user.first_name
        set_user_lang(user_id, username_str, extracted_lang)
        # تحديث متغير اللغة اللحظي لاستخدامه في تحديث الرسالة الحالية فوراً
        lang = extracted_lang
        await query.edit_message_text(
            text=LANG_DICT[lang]["main_menu"],
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )

    # 4. قسم تعلم اللغة الروسية والمصادر المدمجة
    elif data_payload == "submenu_russian":
        keyboard = [
            [InlineKeyboardButton(LANG_DICT[lang]["course_rus_1"], url=RUSSIAN_COURSE_1)],
            [InlineKeyboardButton(LANG_DICT[lang]["course_rus_2"], url=RUSSIAN_COURSE_2)],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text=LANG_DICT[lang]["lang_hub_title"],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    # 5. قسم تعلم اللغة التركية والمصادر المدمجة
    elif data_payload == "submenu_turkish":
        keyboard = [
            [InlineKeyboardButton(LANG_DICT[lang]["course_tur_1"], url=TURKISH_COURSE_1)],
            [InlineKeyboardButton(LANG_DICT[lang]["course_tur_2"], url=TURKISH_COURSE_2)],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text=LANG_DICT[lang]["lang_hub_title"],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    # 6. قسم إدارة وجدولة المهام والتنبيهات الفرعي
    elif data_payload == "submenu_tasks":
        btn_add = "➕ Add Task" if lang=='en' else "➕ إضافة مهمة جديدة" if lang=='ar' else "➕ Добавить задачу"
        btn_view = "📋 View Active Tasks" if lang=='en' else "📋 استعراض وعرض المهام الحالية" if lang=='ar' else "📋 Посмотреть задачи"
        keyboard = [
            [InlineKeyboardButton(btn_add, callback_data="task_action_prompt_add")],
            [InlineKeyboardButton(btn_view, callback_data="task_action_view_all")],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text="📁 <b>Task Control Terminal:</b>\n\nManage your persistent database schedule entries easily:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data_payload == "task_action_prompt_add":
        context.user_data['action'] = 'state_waiting_for_task_title'
        await query.edit_message_text(text=LANG_DICT[lang]["task_title_prompt"], parse_mode="HTML")

    elif data_payload == "task_action_view_all":
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, task_text FROM tasks WHERE user_id = ?", (user_id,))
            user_tasks = cursor.fetchall()
            conn.close()
            
            if not user_tasks:
                await query.edit_message_text(
                    text=LANG_DICT[lang]["no_tasks"],
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="submenu_tasks")]]),
                    parse_mode="HTML"
                )
            else:
                layout_text = "📋 <b>Your Active Indexed Tasks:</b>\n\n" if lang=='en' else "📋 <b>قائمة مهامك النشطة الحالية:</b>\n\n" if lang=='ar' else "📋 <b>Ваши активные задачи:</b>\n\n"
                keyboard = []
                for idx, item in enumerate(user_tasks):
                    task_id, task_msg = item
                    layout_text += f"<b>{idx+1}.</b> {task_msg}\n"
                    # زر إنهاء فريد لكل مهمة بناء على معرفها التلقائي بالـ Database
                    keyboard.append([InlineKeyboardButton(f"✅ Mark Done {idx+1}", callback_data=f"taskdone_id_{task_id}")])
                
                keyboard.append([InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="submenu_tasks")])
                await query.edit_message_text(
                    text=layout_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML"
                )
        except sqlite3.Error as dbe:
            logger.error(f"Task selection database execution error: {dbe}")
            await query.edit_message_text(text=LANG_DICT[lang]["generic_error"], reply_markup=back_to_main_button(lang))

    elif data_payload.startswith("taskdone_id_"):
        target_task_id = int(data_payload.split("_")[2])
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (target_task_id, user_id))
            conn.commit()
            conn.close()
            
            success_msg = "✅ Task marked as completed and removed from storage schema!" if lang=='en' else "✅ تم شطب المهمة وإكمالها بنجاح وحذفها من جدول البيانات الحين!" if lang=='ar' else "✅ Задача выполнена!"
            await query.edit_message_text(
                text=success_msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Reload List" if lang=='en' else "📋 تحديث القائمة الحين" if lang=='ar' else "📋 Обновить", callback_data="task_action_view_all")]]),
                parse_mode="HTML"
            )
        except sqlite3.Error as dbe:
            logger.error(f"Failed to delete task row {target_task_id}: {dbe}")
            await query.edit_message_text(text=LANG_DICT[lang]["generic_error"], reply_markup=back_to_main_button(lang))

    # 7. مركز كبسولة التطوير الذكي والمهني الجديد والتحفيز (AI Growth Hub)
    elif data_payload == "submenu_growth":
        keyboard = [
            [InlineKeyboardButton(LANG_DICT[lang]["btn_side_project"], callback_data="growth_action_project")],
            [InlineKeyboardButton(LANG_DICT[lang]["btn_challenge"], callback_data="growth_action_challenge")],
            [InlineKeyboardButton(LANG_DICT[lang]["btn_cv_optimizer"], callback_data="growth_action_cv")],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text=LANG_DICT[lang]["growth_title"],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data_payload == "growth_action_project":
        context.user_data['action'] = 'state_waiting_for_project_parameters'
        prompt_info = (
            "💡 <b>AI Side-Project Architect:</b>\n\nSend me your current technology keywords (e.g., Python, Docker, React, SQL) along with your expertise level (Beginner/Intermediate/Advanced) and I will craft an optimized software architecture plan for your GitHub profile portfolio."
            if lang == 'en' else
            "💡 <b>مولد أفكار ومخططات المشاريع الجانبية:</b>\n\nأرسل لي الكلمات المفتاحية للتقنيات التي تتقنها أو تدرسها (مثال: Python, React, JavaScript, Django) مع مستوى خبرتك الحالية الحين، وسيقوم الذكاء الاصطناعي بابتكار بنية مشروع كاملة، فريدة ومجهزة لرفعها في معرض أعمالك."
        )
        await query.edit_message_text(text=prompt_info, parse_mode="HTML")

    elif data_payload == "growth_action_challenge":
        await query.edit_message_text(
            text="⚡ <code>Calibrating high-energy discipline nodes... Generating challenge...</code>" if lang=='en' else "⚡ <code>جاري فحص مصفوفة الانضباط وتوليد التحدي اليومي المكثف الحين...</code>",
            parse_mode="HTML"
        )
        challenge_prompt = (
            "Act as a professional elite productivity, military discipline, and career execution coach. Generate EXACTLY ONE random, unique, highly structural, and actionable 24-hour accountability challenge for a technology student or high-performance software programmer. The challenge must be strictly practical, time-bound, and immediately measurable today. Do not give generic advice. Keep it hard, intense, concise, and heavily motivating. Respond entirely in " + lang + " language."
        )
        try:
            ai_response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=challenge_prompt)
            keyboard = [
                [InlineKeyboardButton("🔄 Generate Another Challenge" if lang=='en' else "🔄 رول وتوليد تحدي آخر الحين", callback_data="growth_action_challenge")],
                [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="submenu_growth")]
            ]
            await query.message.reply_text(
                text=f"🎯 <b>Your 24-Hour Gamified Discipline Challenge Matrix:</b>\n\n{ai_response.text}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        except Exception as ai_ex:
            logger.error(f"Gemini API failure during challenge generation: {ai_ex}")
            await query.message.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=back_to_main_button(lang))

    elif data_payload == "growth_action_cv":
        context.user_data['action'] = 'state_waiting_for_cv_input'
        prompt_info = (
            "📝 <b>Executive CV & Bio Optimization Engine:</b>\n\nSend me any raw draft statement, messy job description bullet points, or your current personal profile text. I will structurally engineer and re-write it with hyper-impactful verbs and action-driven technical terminology tailored to clear ATS tracking filters and impress HR scouts."
            if lang == 'en' else
            "📝 <b>مصحح ومطور العبارات والسير الذاتية والـ Bio الاحترافي:</b>\n\nأرسل لي العبارة العادية أو مسودة الخبرة أو الوصف الذي ترغب بوضعه في سيرتك الذاتية أو حساب LinkedIn الحين، وسيقوم النظام بإعادة صياغتها بالكامل بأسلوب إداري مبهر ومقنع للشركات الكبرى وأصحاب العمل."
        )
        await query.edit_message_text(text=prompt_info, parse_mode="HTML")

    # 8. محطة الكويزات الذكية وبناء أسئلة الـ JSON والـ PDF
    elif data_payload == "submenu_quiz":
        context.user_data['action'] = 'state_waiting_for_quiz_payload'
        await query.edit_message_text(text=LANG_DICT[lang]["quiz_prompt"], parse_mode="HTML")

    # 9. قسم أدوات المطور والدراسة بالذكاء الاصطناعي
    elif data_payload == "submenu_tools":
        keyboard = [
            [InlineKeyboardButton("🛠️ AI Advanced Code Debugger & Optimizer", callback_data="tool_action_code")],
            [InlineKeyboardButton("📚 AI Comprehensive Non-Fiction Book Summarizer", callback_data="tool_action_book")],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text="🤖 <b>AI Developer & Advanced Study Framework:</b>\n\nSelect your automated intellectual accelerator tool:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data_payload == "tool_action_code":
        context.user_data['action'] = 'state_waiting_for_code_block'
        await query.edit_message_text(
            text="💻 <b>Advanced Code Analyzer:</b>\n\nPaste your raw source code block (Python, C++, JS, etc.) below. The AI will instantly audit the logical syntax, detect subtle leak bugs, optimize time-complexity profiles, and supply optimized structural variations.",
            parse_mode="HTML"
        )

    elif data_payload == "tool_action_book":
        context.user_data['action'] = 'state_waiting_for_book_title'
        await query.edit_message_text(text=LANG_DICT[lang]["book_prompt"], parse_mode="HTML")

    # 10. مؤقت بومودورو الآلي المتقدم وتكامل طابور المهام Async Job Queue
    elif data_payload == "submenu_pomo":
        keyboard = [
            [InlineKeyboardButton("⏱️ Activate 25-Min Production Session", callback_data="pomo_action_start")],
            [InlineKeyboardButton("🎵 Focus Environment: Lo-Fi Study Stream", url="https://www.youtube.com/watch?v=jfKfPfyJRdk")],
            [InlineKeyboardButton("🎵 Focus Environment: Rain & Thunderstorm ASMR", url="https://www.youtube.com/watch?v=mPZkdNFkNps")],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text="⏱️ <b>Asynchronous Pomodoro Engine & Cognitive Focus Hub:</b>\n\nCalibrate your physical study cycles and block external noise nodes:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data_payload == "pomo_action_start":
        # تشغيل المؤقت الحقيقي بإضافة عمل لطابور المهام ينتهي بعد 1500 ثانية (25 دقيقة)
        # للتجارب والاختبارات السريعة يمكن تعديل القيمة لـ 10 ثوانٍ مثلاً
        context.job_queue.run_once(
            pomodoro_expiration_callback, 
            when=1500, 
            user_id=user_id, 
            data={"pomo_lang": lang}
        )
        await query.edit_message_text(
            text=LANG_DICT[lang]["pomo_started"],
            reply_markup=back_to_main_button(lang),
            parse_mode="HTML"
        )

    # 11. قسم سينما ومسلسلات وأفلام التكنولوجيا والـ Streaming
    elif data_payload == "submenu_movies":
        keyboard = [
            [InlineKeyboardButton("🎬 Artificial Intelligence & Androids Category", callback_data="cinema_cat_ai")],
            [InlineKeyboardButton("👨‍💻 Programming, Systems & Tech Startup History", callback_data="cinema_cat_coding")],
            [InlineKeyboardButton("🔒 Cyber Security, Hacking & Surveillance Era", callback_data="cinema_cat_cyber")],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text="🎬 <b>Welcome to the Technical Cinema Database:</b>\n\nSelect a sub-genre to pull streaming blueprints and instantaneous look-up URLs for top titles:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data_payload.startswith("cinema_cat_"):
        target_category = data_payload.split("_")[2]
        movie_list = MOVIES_DATABASE.get(target_category, [])
        keyboard = []
        for film in movie_list:
            keyboard.append([InlineKeyboardButton(film["title"], url=film["search_url"])])
        keyboard.append([InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="submenu_movies")])
        await query.edit_message_text(
            text="🍿 <b>Indexed Tech Masterpieces Found:</b>\n\nClick any button title to search availability, trailers, and streaming options instantly online:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    # 12. مستودع حفظ وتصنيف الروابط السريع والمفكرة المفتوحة
    elif data_payload == "submenu_links":
        keyboard = [
            [InlineKeyboardButton("💡 Deposit a Brain Dump Idea Row", callback_data="link_action_dump")],
            [InlineKeyboardButton("🔖 Secure a Resource Hyperlink URL", callback_data="link_action_save")],
            [InlineKeyboardButton(LANG_DICT[lang]["back"], callback_data="go_main")]
        ]
        await query.edit_message_text(
            text="🔖 <b>Persistent Bookmarks & Cognitive Waste Dump Terminals:</b>\n\nPrevent context switching by offloading mental metadata safely:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data_payload == "link_action_dump":
        context.user_data['action'] = 'state_waiting_for_brain_dump_text'
        await query.edit_message_text(text=LANG_DICT[lang]["brain_dump_prompt"], parse_mode="HTML")

    elif data_payload == "link_action_save":
        context.user_data['action'] = 'state_waiting_for_link_saver_url'
        await query.edit_message_text(text=LANG_DICT[lang]["link_saver_prompt"], parse_mode="HTML")

async def pomodoro_expiration_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """يتم استدعاؤها برمجياً فور اكتمال وقت مؤقت البومودورو المجدول لإخطار العميل بنجاح."""
    target_job = context.job
    if not target_job or not target_job.user_id:
        return
        
    session_data = target_job.data
    lang_token = session_data.get("pomo_lang", "en")
    alert_message = LANG_DICT[lang_token]["pomo_done"]
    
    try:
        await context.bot.send_message(
            chat_id=target_job.user_id,
            text=alert_message,
            parse_mode="HTML"
        )
        logger.info(f"🔔 Pomodoro alarm dispatched successfully to target client ID: {target_job.user_id}")
    except Exception as dispatch_err:
        logger.error(f"Could not dispatch async pomodoro notification message row: {dispatch_err}")

# ==========================================================================================
# 📝 القسم 7: معالجة نصوص ومحادثات ومخرجات المستخدم والتحكم في حالات الـ AI (LLM Execution)
# ==========================================================================================

async def global_user_text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """المعالج البشري والنصي المعقد. يقوم بفحص حالات العميل النشطة وتوجيه النصوص للـ LLM."""
    if not update.message or not update.message.text:
        return

    current_state = context.user_data.get('action')
    input_text = update.message.text
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    logger.info(f"📥 Incoming User Text Text Session: State='{current_state}', Length={len(input_text)} chars.")

    # 💠 الحالة أ: معالجة حفظ عنوان وإدخال مهمة جديدة بقاعدة البيانات
    if current_state == 'state_waiting_for_task_title':
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (user_id, task_text, priority, created_at) VALUES (?, ?, ?, ?)",
                (user_id, input_text, "High", datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            context.user_data.clear() # إغلاق الحالة ونظافة المتغيرات
            await update.message.reply_text(
                text=LANG_DICT[lang]["task_added"],
                reply_markup=main_menu_keyboard(lang),
                parse_mode="HTML"
            )
        except sqlite3.Error as dbe:
            logger.error(f"Task database write operations crashed: {dbe}")
            await update.message.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة ب: معالجة حفظ مسودات تفريغ الدماغ والأفكار السريعة
    elif current_state == 'state_waiting_for_brain_dump_text':
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO brain_dump (user_id, note_text, timestamp) VALUES (?, ?, ?)",
                (user_id, input_text, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            context.user_data.clear()
            success_note = (
                "💡 <b>Idea Logged:</b> Your computational or study concept is now safely written onto your server disk storage partition row!" 
                if lang=='en' else 
                "💡 <b>تم توثيق الفكرة الحين:</b> تم حفظ فكرتك ومسودتك الخاطرة بأمان داخل ذاكرة البوت المستقلة وقاعدة البيانات بنجاح!"
            )
            await update.message.reply_text(text=success_note, reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        except sqlite3.Error as dbe:
            logger.error(f"Brain dump insert query fail: {dbe}")
            await update.message.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة ج: معالجة أرشفة وحفظ روابط الانترنت والمقالات الهامة
    elif current_state == 'state_waiting_for_link_saver_url':
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO saved_links (user_id, link_url, category, archived_at) VALUES (?, ?, ?, ?)",
                (user_id, input_text, "Aesthetic-Study", datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            context.user_data.clear()
            success_link = (
                "🔖 <b>Hyperlink Archived:</b> Resource mapped and indexed into persistent category slots successfully."
                if lang=='en' else
                "🔖 <b>تم أرشفة وحفظ الرابط بنجاح:</b> تم فهرسة مورد الإنترنت وجدولته في تصنيفاتك بنجاح الحين."
            )
            await update.message.reply_text(text=success_link, reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        except sqlite3.Error as dbe:
            logger.error(f"Link saver dynamic module exception: {dbe}")
            await update.message.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة د: معالجة هندسة بنية ومخططات المشاريع الجانبية (AI Side-Project Architect)
    elif current_state == 'state_waiting_for_project_parameters':
        waiting_ui = await update.message.reply_text(
            text="⚡ <code>Analyzing technical ecosystem constraints... Constructing production repository architecture...</code>" if lang=='en' else "⚡ <code>جاري فحص المتطلبات البرمجية الحين وبناء معمارية المشروع المستهدف عبر جمناي...</code>",
            parse_mode="HTML"
        )
        context.user_data.clear()
        structural_prompt = (
            f"You are a visionary principal software architect and veteran venture tech builder. Based on the user's input skills and technology target: '{input_text}', construct a highly innovative, unique, and realistic side-project architecture concept that can be built by an independent developer to boost their CV. Your structure MUST follow this breakdown:\n"
            f"1. 🚀 PROJECT UNIQUE NAME: Create a punchy, ultra-modern tech name.\n"
            f"2. 🎯 CORE PROBLEM SOLVED: Define the painful reality or consumer need this project satisfies.\n"
            f"3. 🛠️ GRANULAR TECHNICAL ARCHITECTURE: Explain database choice, server stack, backend strategy, API paradigms, and external dependencies.\n"
            f"4. 📦 STEP-BY-STEP DEVELOPMENT ROADMAP: Map out exactly 4 development phases from initial setup to deployment.\n"
            f"Keep your tone inspiring, clear, deeply technical, and professional. Write the entire output inside the requested communication language: '{lang}'."
        )
        try:
            generation = ai_client.models.generate_content(model='gemini-2.5-flash', contents=structural_prompt)
            await waiting_ui.reply_text(
                text=f"💡 <b>Your Tailored Custom Side-Project Architecture Blueprint:</b>\n\n{generation.text}",
                reply_markup=main_menu_keyboard(lang),
                parse_mode="HTML"
            )
        except Exception as api_err:
            logger.error(f"Side project AI generation pipeline fault: {api_err}")
            await waiting_ui.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة هـ: معالجة صياغة وتحسين عبارات السيرة الذاتية الاحترافية للـ HR
    elif current_state == 'state_waiting_for_cv_input':
        waiting_ui = await update.message.reply_text(
            text="⚡ <code>Transforming text syntax... Applying corporate executive parameters...</code>" if lang=='en' else "⚡ <code>جاري مراجعة وتحسين العبارات وتطبيق قواعد الـ ATS العالمية الحين...</code>",
            parse_mode="HTML"
        )
        context.user_data.clear()
        cv_prompt = (
            f"You are an elite corporate talent acquisition head and top-tier global technical resume writer. Take this messy, unpolished draft text or bullet points from a job seeker: '{input_text}'. Re-write it entirely into an optimized, executive-level, result-driven statement suitable for a high-end corporate resume or LinkedIn profile description. Utilize powerful action verbs (e.g., Architected, Optimized, Spearheaded, Engineered), highlight metric accomplishments implicitly, and clean syntax flaws. Write the optimized results clearly and directly in this language target: '{lang}'."
        )
        try:
            generation = ai_client.models.generate_content(model='gemini-2.5-flash', contents=cv_prompt)
            await waiting_ui.reply_text(
                text=f"📝 <b>ATS-Optimized Corporate Phrasing Output:</b>\n\n{generation.text}",
                reply_markup=main_menu_keyboard(lang),
                parse_mode="HTML"
            )
        except Exception as api_err:
            logger.error(f"CV Optimizer neural task failure: {api_err}")
            await waiting_ui.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة و: فحص وإصلاح وتطوير الأكواد البرمجية للمطورين
    elif current_state == 'state_waiting_for_code_block':
        waiting_ui = await update.message.reply_text(text="⚡ <code>Initiating neural compiler audit... Checking algorithms and abstract syntax trees...</code>", parse_mode="HTML")
        context.user_data.clear()
        code_prompt = (
            f"Act as an expert world-class principal software engineering consultant and senior compiler diagnostics expert. Inspect this provided raw code script block carefully:\n\n{input_text}\n\n"
            f"Perform the following internal evaluation tracks:\n"
            f"1. Identity and list any structural bugs, syntax problems, memory vulnerabilities, or logical faults.\n"
            f"2. Supply an optimized, heavily cleaned, secure rewrite variation of the script.\n"
            f"3. Explain the improvements made clearly (such as execution speed optimization or safety guardrails).\n"
            f"Format the entire feedback breakdown using markdown and code syntax highlighting blocks beautifully. Deliver the whole report in this language medium: '{lang}'."
        )
        try:
            generation = ai_client.models.generate_content(model='gemini-2.5-flash', contents=code_prompt)
            await waiting_ui.reply_text(text=f"🛠️ <b>AI Code Diagnostics & Optimization Protocol:</b>\n\n{generation.text}", reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        except Exception as api_err:
            logger.error(f"Compiler tool analyzer crash: {api_err}")
            await waiting_ui.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة ز: تلخيص وشرح الكتب العالمية التنموية والأكاديمية
    elif current_state == 'state_waiting_for_book_title':
        waiting_ui = await update.message.reply_text(text="⚡ <code>Fetching deep literal bibliography index... Mapping macro book arguments...</code>", parse_mode="HTML")
        context.user_data.clear()
        book_prompt = (
            f"Act as an elite speed-reading academic professor and executive literary summarizer. The target literature to dismantle is: '{input_text}'. Provide a deep, structured, non-fiction architectural summary blueprint of this book. Your feedback summary MUST strictly follow this layout:\n"
            f"1. 📚 CORE THESIS: Describe the overarching primary driving philosophical message of the book in 3 lines.\n"
            f"2. 🔑 THE 3 REVOLUTIONARY PILLARS: Break down the top 3 most profound concepts or strategies explained within, utilizing clear, heavy bullet points.\n"
            f"3. 🛠️ ACTIONABLE LESSON MATRIX: Provide exactly 3 explicit daily habits or workflows the reader can immediately perform tomorrow morning to execute the book's teachings in reality.\n"
            f"Avoid fluff, stay incredibly practical, and supply your response completely translated inside this language medium: '{lang}'."
        )
        try:
            generation = ai_client.models.generate_content(model='gemini-2.5-flash', contents=book_prompt)
            await waiting_ui.reply_text(text=f"📚 <b>AI High-Impact Book Blueprint & Summary:</b>\n\n{generation.text}", reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        except Exception as api_err:
            logger.error(f"Book summarizer subsegment fail: {api_err}")
            await waiting_ui.reply_text(text=LANG_DICT[lang]["generic_error"], reply_markup=main_menu_keyboard(lang))

    # 💠 الحالة ح: توليد بنية الكويزات الذكية عبر الاستجابة المهيكلة (Gemini JSON Schema Framework)
    elif current_state == 'state_waiting_for_quiz_payload':
        waiting_ui = await update.message.reply_text(text="⚡ <code>Parsing text metadata blocks... Structuring evaluation matrices into schema nodes...</code>", parse_mode="HTML")
        context.user_data.clear()
        
        quiz_system_prompt = (
            f"Construct exactly 3 academic multiple-choice checking questions based purely on this instructional text material: '{input_text}'."
        )
        try:
            # تشييد الهيكل البرمجي المتوقع باستخدام BaseModel لفرضه على مخرجات الذكاء الاصطناعي
            class QuizSchemaTemplate(types.BaseModel):
                question_text: str
                option_a: str
                option_b: str
                option_c: str
                option_d: str
                correct_option_token: str # must be a, b, c, or d

            # استدعاء النموذج وفرض صيغة الـ JSON ومطابقة مصفوفة الفئات المحددة
            ai_structured_response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=quiz_system_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[QuizSchemaTemplate],
                    temperature=0.2, # درجة حرارة منخفضة لضمان الالتزام الصارم بالحقائق والنص
                ),
            )
            
            # تحليل واستخراج البيانات من كائن الـ JSON المستلم
            parsed_questions = json.loads(ai_structured_response.text)
            
            rendered_quiz_output = "🧠 <b>AI Structurally Engineered Academic Quiz Result:</b>\n\n"
            for index, question in enumerate(parsed_questions):
                rendered_quiz_output += (
                    f"<b>Q{index+1}: {question['question_text']}</b>\n"
                    f"🔹 A) {question['option_a']}\n"
                    f"🔹 B) {question['option_b']}\n"
                    f"🔹 C) {question['option_c']}\n"
                    f"🔹 D) {question['option_d']}\n"
                    f"👉 <b>Validated Key: Option [{question['correct_option_token'].upper()}]</b>\n\n"
                )
            
            await waiting_ui.reply_text(text=rendered_quiz_output, reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        except Exception as json_schema_fail:
            logger.error(f"Structured output parsing or execution threw exception row: {json_schema_fail}")
            await waiting_ui.reply_text(
                text="⚠️ <b>Parsing System Congestion:</b>\nCould not construct clean structural JSON quiz schemas. Ensure your input chunk contains sufficient factual context data.",
                reply_markup=main_menu_keyboard(lang),
                parse_mode="HTML"
            )

    # 🎯 الوضع الافتراضي المستمر: المساعد الشخصي الذكي الحر (Conversational Streaming Mode)
    else:
        waiting_ui = await update.message.reply_text(text="💭 <code>Gemini thinking...</code>", parse_mode="HTML")
        generic_assistant_prompt = (
            f"You are the centralized, highly intellectual, friendly, and ultra-productive core multi-language personal AI assistant embedded in this automation platform. "
            f"Respond concisely, with outstanding value, structured paragraphs, and clever productivity insights. Keep your language presentation exactly matching this requested user language setting: '{lang}'. User input message reads: '{input_text}'"
        )
        try:
            generation = ai_client.models.generate_content(model='gemini-2.5-flash', contents=generic_assistant_prompt)
            # تحديث رسالة التفكير لتوفير جودة عرض فائقة للمستخدمين دون رسائل مكررة
            await waiting_ui.edit_text(text=generation.text, reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        except Exception as api_err:
            logger.error(f"Fallback assistant interactive neural pathway failed: {api_err}")
            await waiting_ui.edit_text(text="❌ Service communication interruption. Check upstream configuration.", reply_markup=main_menu_keyboard(lang))

# ==========================================================================================
# 📂 القسم 8: المعالجة المتقدمة للمستندات والملفات وقراءة الـ PDFs واشتقاق الاختبارات
# ==========================================================================================

async def document_upload_quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تستقبل ملفات الـ PDF المرفوعة، تقوم بتحميلها وفحصها برمجياً، واشتقاق كويز JSON منها."""
    target_message = update.message
    if not target_message or not target_message.document:
        return

    current_state = context.user_data.get('action')
    telegram_document = target_message.document
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    # التحقق مما إذا كان المستخدم قد اختار تفعيل ميزة الكويزات أولاً أم رفع عشوائياً
    if current_state != 'state_waiting_for_quiz_payload':
        warning_upload = (
            "🤖 Please navigate and select the <b>AI Quiz Generator Terminal</b> button first before sending technical document files to the pipeline."
            if lang=='en' else
            "🤖 يرجى الانتقال والضغط على زر <b>مركز الكويزات الذكي واختبارات الـ PDF</b> أولاً من القائمة قبل رفع أي مستندات برمجية لتهيئة المحرك."
        )
        await target_message.reply_text(text=warning_upload, reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        return

    waiting_ui = await target_message.reply_text(text="📥 <code>Downloading document binary from Telegram servers... Initializing structural extraction...</code>", parse_mode="HTML")
    context.user_data.clear() # تصفية الفهرس لمنع التكرار

    # التأكد من صحة لاحقة الملف وأنها مستند PDF حقيقي لحماية الخادم
    document_extension = telegram_document.file_name.lower() if telegram_document.file_name else ""
    if not document_extension.endswith('.pdf'):
        await waiting_ui.edit_text(text="⚠️ <b>Format Refusal:</b> The academic pipeline only processes structural <code>.pdf</code> extensions. Try raw text copy-pasting instead.", reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
        return

    local_temporary_pdf_path = f"temp_runtime_file_{user_id}_{random.randint(1000, 9999)}.pdf"
    
    try:
        # تحميل الملف الثنائي برمجياً إلى القرص المحلي للبوت
        telegram_file_object = await context.bot.get_file(telegram_document.file_id)
        await telegram_file_object.download_to_drive(custom_path=local_temporary_pdf_path)
        
        await waiting_ui.edit_text(text="⚙️ <code>Binary secured locally. Unpacking pages and extracting Unicode text layers...</code>", parse_mode="HTML")
        
        # استيراد ومعالجة ملف الـ PDF عبر مكتبة PyPDF بكفاءة أسطر عالية ومفصلة
        import pypdf
        pdf_reader_instance = pypdf.PdfReader(local_temporary_pdf_path)
        extracted_text_pool = ""
        
        # قراءة نصوص الصفحات لـ 15 صفحة كحد أقصى لتفادي حظر الذاكرة العشوائية وسقوط الـ Core
        max_page_limits = min(len(pdf_reader_instance.pages), 15)
        for page_index in range(max_page_limits):
            current_page_object = pdf_reader_instance.pages[page_index]
            page_text_buffer = current_page_object.extract_text()
            if page_text_buffer:
                extracted_text_pool += page_text_buffer + "\n"

        # تنظيف وحذف الملف المؤقت من القرص فوراً لضمان عدم امتلاء سعة سيرفر Railway
        if os.path.exists(local_temporary_pdf_path):
            os.remove(local_temporary_pdf_path)

        # التحقق مما إذا كان الـ PDF فارغاً أو عبارة عن صور ممسوحة تحتاج OCR
        if len(extracted_text_pool.strip()) < 40:
            await waiting_ui.reply_text(text="⚠️ <b>Extraction Void:</b> Could not pull sufficient clear text layout characters from this PDF. It might be scanned images or locked by encryption permissions.", reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
            return

        await waiting_ui.edit_text(text="⚡ <code>Text layers compiled successfully. Forcing Gemini structural JSON schema compliance...</code>", parse_mode="HTML")

        # تشييد وبناء قالب الفروق مجدداً للتحليل الهيكلي الآمن
        class DocumentQuizTemplate(types.BaseModel):
            question_text: str
            option_a: str
            option_b: str
            option_c: str
            option_d: str
            correct_option_token: str

        pdf_ai_prompt = (
            f"Generate an advanced, comprehensive 3-question evaluation multiple-choice test based directly on this harvested document text layout database block:\n\n{extracted_text_pool[:6000]}" # قطع النص عند 6000 حرف لتفادي تجاوز حدود حجم الـ Token الخاص بالنماذج السريعة
        )

        ai_structured_response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=pdf_ai_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[DocumentQuizTemplate],
                temperature=0.3
            ),
        )

        parsed_pdf_questions = json.loads(ai_structured_response.text)
        
        rendered_quiz_output = "🧠 <b>PDF Mapped Structural Exam Framework Generated:</b>\n\n"
        for index, question in enumerate(parsed_pdf_questions):
            rendered_quiz_output += (
                f"<b>Q{index+1}: {question['question_text']}</b>\n"
                f"🔸 A) {question['option_a']}\n"
                f"🔸 B) {question['option_b']}\n"
                f"🔸 C) {question['option_c']}\n"
                f"🔸 D) {question['option_d']}\n"
                f"👉 <b>Validated Key: Option [{question['correct_option_token'].upper()}]</b>\n\n"
            )

        await waiting_ui.reply_text(text=rendered_quiz_output, reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
    except Exception as pdf_pipeline_fault:
        logger.error(f"Deep document pipeline automation failure scenario: {pdf_pipeline_fault}")
        if os.path.exists(local_temporary_pdf_path):
            os.remove(local_temporary_pdf_path)
        await waiting_ui.reply_text(text="❌ <b>Critical PDF Processing Fail:</b> Internal pipeline crashed during parsing. Re-ensure document encoding metrics.", reply_markup=main_menu_keyboard(lang), parse_mode="HTML")

# ==========================================================================================
# ⚙️ القسم 9: النواة التشغيلية الأساسية وبدء محرك الـ Polling لـ Telegram Framework
# ==========================================================================================

def execute_platform_runtime_init() -> None:
    """
    نقطة الانطلاق التنفيذية الكبرى. تهيئ قاعدة البيانات، تتحقق من سلامة الأكواد،
    تبني تطبيق تليجرام، تربط المعالجات التفصيلية، وتبدأ استقبال الطلبات.
    """
    # 1. تفعيل وتشغيل الـ Database Schema
    database_bootstrap()
    
    logger.info("⚙️ Core engine pre-flight checks clearing. Registering structural pipeline filters...")
    
    # 2. بناء التطبيق وتمرير التوكن وتكامل معالج الـ Job Queue للمؤقتات الزمنية
    platform_application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(application_post_init)
        .build()
    )
    
    # 3. تسجيل وربط معالجات الأوامر الرئيسية (Command Handlers)
    platform_application.add_handler(CommandHandler("start", command_start_handler))
    
    # 4. تسجيل وربط معالج نقرات الواجهة (Callback Query Handler Matrix)
    platform_application.add_handler(CallbackQueryHandler(main_callback_query_router))
    
    # 5. تسجيل وربط معالج معالجة واستقبال ملفات الـ PDF والمستندات (Document Framework)
    platform_application.add_handler(MessageHandler(filters.Document.ALL, document_upload_quiz_handler))
    
    # 6. تسجيل وربط معالج النصوص المتقدم الشامل والدردشة المستمرة ومفاتيح الحالات (Text Handler)
    platform_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_user_text_message_handler))
    
    # 7. تشغيل البوت وإطلاق الـ Polling على الخادم واستمرارية العمل الدائم
    logger.info("🚀 System Boot Successful! Ultimate Multi-Language Platform is now polling active streams...")
    platform_application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    # حماية الدخول وبدء التنفيذ الصارم لنواة النظام
    execute_platform_runtime_init()
