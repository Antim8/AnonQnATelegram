import asyncio
from email.mime import application
import logging
from telegram import Chat, Update
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import re

#TODO Prevent bots from sending messages by checking update effetive user is_bot

load_dotenv()
TOKEN = os.environ.get('TELEGRAM_API_KEY')
GROUP_ID = os.environ.get('GROUP_ID')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update:Update, context: ContextTypes.DEFAULT_TYPE):
    #TODO too repetitive 
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    
    await context.bot.send_message(chat_id=chat_id, text="Hey there, pls wait while I try to authenticate you")
    a = await user_auth(chat_id=chat_id, user_id=update.effective_user.id, context=context)
    print(a)
    
async def help_cmd(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    #TODO Change into usefull helptext
    await context.bot.send_message(chat_id=chat_id, text="HELPTEXT")

async def pw_auth(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
        
    #TODO Change into usefull helptext
    await user_auth_pw(chat_id=chat_id, context=context, password=' '.join(context.args))
    
async def ask_q(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    
    #TODO Create Q in DB with ID and User ID and Chat ID
    await context.bot.send_message(chat_id=GROUP_ID, text=(' '.join(context.args) + "\n\nID:1337"))

async def answer_q(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    #TODO Create A in DB with id and if private or open
    #TODO Connect A to Q in DB
    #TODO Fetch user ID of asked Q
    #TODO Send Answer to user who asked Q 
    #TODO Set if answer is open or private
    await context.bot.send_message(chat_id=chat_id, text="HELPTEXT")
    
#HELPERS
async def user_auth(chat_id, user_id, context):
    if context.bot.get_chat_member(chat_id, user_id):
        #TODO Set auth in DB
        await context.bot.send_message(chat_id=chat_id, text="Congrats you can now use the bot! Enter the /help command to see how everything works")
        return True
    else:
        await context.bot.send_message(chat_id=chat_id, text="Seems like you are not in the group or there was a mistake while trying to authenticate you, pls try /start again or enter the command /password followed by the password for our special website")
        return False
    
async def user_auth_pw(chat_id, context, password):
    if password == os.environ.get("AUTH"):
        #TODO Set auth in DB
        
        await context.bot.send_message(chat_id=chat_id, text="Congrats you can now use the bot! Enter the /help command to see how everything works")
        asyncio.run(help_cmd)
        return True
    else:
        await context.bot.send_message(chat_id=chat_id, text="Wrong password, pls try again")
        #TODO pw try count up
        return False
        
    
#TODO Message Handler with filters to REPLY -> Grab ID and forward answers to initial chat
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    
    handlers = []
    handlers.append(CommandHandler('start', start))
    handlers.append(CommandHandler('help', help_cmd))
    handlers.append(CommandHandler('password', pw_auth))
    handlers.append(CommandHandler('q', ask_q))
    
    application.add_handlers(handlers=handlers)
    
    application.run_polling()
    
    