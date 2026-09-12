import os
import io
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from PIL import Image

TELEGRAM_BOT_TOKEN = "8307934615:AAFJin0H3nn7KbdKeUM5K5Itb06xDFZY2Rk"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_TELEGRAM_ID = 7300441812

MAX_DAILY_LIMIT = 5

ai_client = genai.Client(api_key=GEMINI_API_KEY)
user_usage = {}

def check_and_update_limit(user_id: int) -> tuple[bool, str]:
    if user_id == ADMIN_TELEGRAM_ID:
        return True, "غير محدود (حساب الأدمن) 👑"

    today = datetime.date.today()
    if user_id not in user_usage or user_usage[user_id]["date"] != today:
        user_usage[user_id] = {"count": 1, "date": today}
        remaining = MAX_DAILY_LIMIT - 1
        return True, f"{remaining} محاولات متبقية"
    
    if user_usage[user_id]["count"] < MAX_DAILY_LIMIT:
        user_usage[user_id]["count"] += 1
        remaining = MAX_DAILY_LIMIT - user_usage[user_id]["count"]
        return True, f"{remaining} محاولات متبقية"
    else:
        return False, "0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت تحليل الشارت! 📈\n\nأرسل صورة الرسم البياني (الشارت) وسأقوم بتحليل الحركة المتوقعة وتحديد اتجاه الصفقة ونسبة النجاح."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    allowed, status_msg = check_and_update_limit(user_id)
    
    if not allowed:
        await update.message.reply_text("❌ لقد استنفدت محاولاتك الـ 5 المجانية لهذا اليوم. يتجدد رصيدك غداً!")
        return

    await update.message.reply_text("⏳ جاري قراءة الشارت وتحليل المؤشرات...")

    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))

        prompt = """
        أنت خبير تحليل فني في أسواق المال والخيارات الثنائية. قم بتحليل صورة الشارت المرفقة بدقة وأعطني النتيجة بالشكل التالي:
        
        🎯 الاتجاه المتوقع: [صعود CALL / هبوط PUT]
        📊 نسبة النجاح المتوقعة: [نسبة مئوية تقريبية]
        ⏱️ الصفقة الموصى بها: [مثلاً: شمعة دقيقة واحدة]
        🔍 السبب الفني: [سطرين توضيحين لسبب الاتجاه بناءً على الدعوم/المقاومات والشمعات]
        """

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, prompt]
        )

        result = f"{response.text}\n\n📌 رصيدك اليومي: {status_msg}"
        await update.message.reply_text(result)

    except Exception as e:
        await update.message.reply_text("حدث خطأ أثناء تحليل الصورة، يرجى إعادة المحاولة.")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
