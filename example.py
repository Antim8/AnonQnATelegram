import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
API_KEY = os.environ.get('TELEGRAM_API_KEY')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')
    
async def testStart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}',quote=False)


app = ApplicationBuilder().token(API_KEY).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("test", testStart))

app.run_polling()