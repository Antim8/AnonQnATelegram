from email.mime import application
import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from commands import *

"""This is the main script handling the bot
""" 
#TODO Testing  

# Load the important information needed to start the bot
load_dotenv()
TOKEN = os.environ.get('TELEGRAM_API_KEY')

# Basic logging config 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    
    handlers = []
    
    # Handlers listening to specific predefined commands
    handlers.append(CommandHandler('start', start))
    handlers.append(CommandHandler('help', help_cmd))
    handlers.append(CommandHandler('password', pw_auth))
    handlers.append(CommandHandler('q', ask_q))
    handlers.append(CommandHandler('report_q', report_question))
    handlers.append(CommandHandler('report_a', report_answer))
    handlers.append(CommandHandler('a', answer_q_command))
    handlers.append(CommandHandler('a_group', answer_q_to_group_command))
    
    # Handlers listening to normal messages addressed towards the bot with filters
    handlers.append(MessageHandler(filters.POLL, create_poll))
    # This means it should fall into the filter for replys and not into the filter for commands
    handlers.append(MessageHandler(filters.REPLY & (~filters.COMMAND), answer_q_in_group))
    
    application.add_handlers(handlers=handlers)
    
    # Looping the bot so it stays up until error or ctrl+c
    application.run_polling()

    