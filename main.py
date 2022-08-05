from email.mime import application
import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from commands import *

#TODO Prevent bots from sending messages by checking update effetive user is_bot
#TODO teilweise inkosistent da manchmal die telegram_id abgespeichert wird und andernmal die DB-ID 
#TODO Testing 
#TODO Threadsafe db inserting?
#TODO take /2 or /4 of sqrt for banning
# No encouragement to "Try again!". redundant and not fitting -> No exclamation marks 

load_dotenv()
TOKEN = os.environ.get('TELEGRAM_API_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#TODO Message Handler with filters to REPLY -> Grab ID and forward answers to initial chat
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    
    handlers = []
    handlers.append(CommandHandler('start', start))
    handlers.append(CommandHandler('help', help_cmd))
    handlers.append(CommandHandler('password', pw_auth))
    handlers.append(CommandHandler('q', ask_q))
    handlers.append(CommandHandler('report_q', report_question))
    handlers.append(CommandHandler('report_a', report_answer))
    handlers.append(CommandHandler('a', answer_q_command))
    handlers.append(CommandHandler('a_group', answer_q_to_group_command))
    
    handlers.append(MessageHandler(filters.POLL, create_poll))
    handlers.append(MessageHandler(filters.REPLY & (~filters.COMMAND), answer_q_in_group))
    
    application.add_handlers(handlers=handlers)
    
    application.run_polling()

    