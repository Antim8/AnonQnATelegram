import asyncio
from email import message
from email.mime import application
import logging
from httpx import delete
from telegram import Chat, Update, Poll, KeyboardButtonPollType
import os
from dotenv import load_dotenv
import telegram
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, PollAnswerHandler, PollHandler
import math 
from commands import *


import sqlite3 as sl

#TODO Prevent bots from sending messages by checking update effetive user is_bot
#TODO Evtl. Emojis oder ahnliches hinzufuegen um die IDs besser unterscheiden zu koennen 
#TODO Poll
#TODO teilweise inkosistent da manchmal die telegram_id abgespeichert wird und andernmal die DB-ID 
#TODO help_cmd HelpText schreiben
#TODO Testing 
#TODO Threadsafe db inserting?
#TODO All sql commands need to end with ;
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
    handlers.append(MessageHandler(filters.POLL, create_poll))

    #handlers.append(MessageHandler(filters.REPLY), answer_q_reply)
    handlers.append(CommandHandler('a', answer_q_command))
    handlers.append(CommandHandler('a_group', answer_q_group_command))
    
    application.add_handlers(handlers=handlers)
    
    application.run_polling()

    