#!/usr/bin/env python3
"""
بوت تيليجرام لتحويل PDF إلى أسئلة اختيار متعدد
"""

import os
import json
import logging
import tempfile
import pdfplumber
from pypdf import PdfReader
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ===================== الإعدادات =====================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "AQ.Ab8RN6ISrHMpQt79YJ2Mf-QmAJqbjRryzoTdwctsUkhc7dT-ZA")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8627204229:AAGhpaMUxTjc1XXYyUhhGTu4RunHVd3tm-Y")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== استخراج النص =====================
def extract_text(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception:
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            logger.error(f"فشل استخراج النص: {e}")
    return text.strip()

# ===================== توليد الأسئلة =====================
def generate_questions(text: str, num: int) -> list[dict]:
    if len(text) > 12000:
        text = text[:12000]

    prompt = f"""أنت مساعد متخصص في إنشاء اختبارات تعليمية.

بناءً على النص التالي، أنشئ بالضبط {num} سؤال اختيار متعدد باللغة العربية.

النص:
\"\"\"
{text}
\"\"\"

أعد ردك كـ JSON فقط بدون أي نص إضافي:
[
  {{
    "question": "نص السؤال",
    "options": {{
      "A": "الخيار الأول",
      "B": "الخيار الثاني",
      "C": "الخيار الثالث",
      "D": "الخيار الرابع"
    }},
    "answer": "A",
    "explanation": "شرح مختصر للإجابة الصحيحة"
  }}
]

قواعد: كل سؤال له 4 خيارات، الإجابة حرف واحد فقط، JSON فقط بدون backticks."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

# ===================== إرسال السؤال =====================
async def send_question(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    data = context.user_data
    questions = data["questions"]
    index = data["current"]

    if index >= len(questions):
        await show_final_results(context, chat_id)
        return

    q = questions[index]
    text = f"❓ *السؤال {index + 1} من {len(questions)}*\n\n{q['question']}"

    keyboard = [
        [InlineKeyboardButton(f"🅰️ {q['options']['A']}", callback_data="A")],
        [InlineKeyboardButton(f"🅱️ {q['options']['B']}", callback_data="B")],
        [InlineKeyboardButton(f"🇨 {q['options']['C']}", callback_data="C")],
        [InlineKeyboardButton(f"🇩 {q['options']['D']}", callback_data="D")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="Markdown")

# ===================== عرض النتيجة النهائية =====================
async def show_final_results(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    data = context.user_data
    score = data["score"]
    total = len(data["questions"])
    percent = score / total * 100

    if percent >= 90:
        grade = "ممتاز 🏆"
    elif percent >= 75:
        grade = "جيد جداً 🥈"
    elif percent >= 60:
        grade = "جيد 🥉"
    elif percent >= 50:
        grade = "مقبول 📘"
    else:
        grade = "يحتاج مراجعة 📖"

    msg = (
        f"📊 *نتيجة الاختبار*\n\n"
        f"✅ الإجابات الصحيحة: {score} / {total}\n"
        f"📈 النسبة: {percent:.1f}%\n"
        f"🎯 التقدير: {grade}\n\n"
        f"أرسل ملف PDF جديد لبدء اختبار آخر 📄"
    )
    await context.bot.send_message(chat_id, msg, parse_mode="Markdown")
    context.user_data.clear()

# ===================== أوامر البوت =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً! أنا بوت الاختبارات الذكي 🤖\n\n"
        "📄 أرسل لي ملف PDF وسأحوّله إلى أسئلة اختيار متعدد!\n\n"
        "يمكنك تحديد عدد الأسئلة بكتابة:\n"
        "/setnum 5  ← لضبط عدد الأسئلة (افتراضي: 5)"
    )

async def set_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(context.args[0])
        if 1 <= num <= 20:
            context.user_data["num_questions"] = num
            await update.message.reply_text(f"✅ تم ضبط عدد الأسئلة على: {num}")
        else:
            await update.message.reply_text("⚠️ اختر رقماً بين 1 و 20")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ استخدم: /setnum 5")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📥 جاري تحميل الملف...")

    try:
        file = await update.message.document.get_file()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            pdf_path = tmp.name

        await msg.edit_text("📖 جاري قراءة الملف...")
        text = extract_text(pdf_path)
        os.unlink(pdf_path)

        if not text:
            await msg.edit_text("❌ لم أتمكن من قراءة الملف. تأكد أنه PDF يحتوي على نص.")
            return

        num = context.user_data.get("num_questions", 5)
        await msg.edit_text(f"🤖 جاري توليد {num} أسئلة بالذكاء الاصطناعي...")

        questions = generate_questions(text, num)

        context.user_data.update({
            "questions": questions,
            "current": 0,
            "score": 0,
            "results": []
        })

        await msg.edit_text(f"✅ تم توليد {len(questions)} أسئلة! سنبدأ الاختبار الآن 🎯")
        await send_question(context, update.effective_chat.id)

    except Exception as e:
        logger.error(f"خطأ: {e}")
        await msg.edit_text(f"❌ حدث خطأ: {str(e)}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "questions" not in context.user_data:
        await query.edit_message_text("⚠️ أرسل ملف PDF أولاً!")
        return

    data = context.user_data
    index = data["current"]
    q = data["questions"][index]
    user_answer = query.data
    correct = q["answer"].upper()
    is_correct = user_answer == correct

    if is_correct:
        data["score"] += 1
        result_text = f"✅ *إجابة صحيحة!*\n\n💡 {q['explanation']}"
    else:
        result_text = (
            f"❌ *إجابة خاطئة!*\n\n"
            f"الصواب: *{correct})* {q['options'][correct]}\n\n"
            f"💡 {q['explanation']}"
        )

    data["results"].append({
        "question": q["question"],
        "your_answer": user_answer,
        "correct_answer": correct,
        "is_correct": is_correct
    })

    await query.edit_message_text(
        f"❓ *السؤال {index + 1}*\n{q['question']}\n\n{result_text}",
        parse_mode="Markdown"
    )

    data["current"] += 1
    await send_question(context, query.message.chat_id)

# ===================== تشغيل البوت =====================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setnum", set_num))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(CallbackQueryHandler(handle_answer))

    print("🤖 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
