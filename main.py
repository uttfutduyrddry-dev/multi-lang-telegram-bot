import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# تهيئة إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# المتغيرات البيئية (قراءة القيم من البيئة)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
PORT = int(os.environ.get('PORT', '80'))

# التحقق من وجود التوكنز
if not TELEGRAM_BOT_TOKEN or not HUGGING_FACE_TOKEN:
    logger.error("خطأ: يرجى تعيين TELEGRAM_BOT_TOKEN و HUGGING_FACE_TOKEN في المتغيرات البيئية.")
    exit()

# Headers للاتصال بـ Hugging Face API
headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}

# دالة الاستعلام من Hugging Face API
def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"خطأ في الاتصال بـ Hugging Face API: {e}")
        return None

# دالة أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f'أهلاً بك يا {user_name}! أنا بوت دردشة، يمكنك التحدث معي الآن.')

# دالة معالجة الرسائل النصية
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"رسالة جديدة من المستخدم: {user_message}")

    payload = {
        "inputs": user_message
    }
    response = query(payload)

    if response and isinstance(response, list) and response[0].get('generated_text'):
        bot_response = response[0]['generated_text']
        if user_message in bot_response:
            bot_response = bot_response.replace(user_message, "").strip()
        
        if bot_response:
            await update.message.reply_text(bot_response)
        else:
            await update.message.reply_text("عذرًا، لم أتمكن من توليد رد مناسب.")
    else:
        await update.message.reply_text("عذرًا، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقًا.")

# دالة رئيسية لتشغيل البوت
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # Check if running on Render for webhook setup
    if "RENDER_EXTERNAL_HOSTNAME" in os.environ:
        logger.info("Running on Render. Setting up webhook.")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_BOT_TOKEN}"
        )
    else:
        logger.info("Running locally. Using polling.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
