import asyncio
from email.mime import application
import logging
from telegram import Chat, Update, Poll, KeyboardButtonPollType
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, PollAnswerHandler, PollHandler
import re
import math 

import sqlite3 as sl

#TODO Prevent bots from sending messages by checking update effetive user is_bot

load_dotenv()
TOKEN = os.environ.get('TELEGRAM_API_KEY')
GROUP_ID = os.environ.get('GROUP_ID')

DB_NAME = os.environ.get("DB_NAME")
con = sl.connect(DB_NAME)
cur = con.cursor()

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
    await user_auth_pw(chat_id=chat_id, context=context, user_id=update.effective_user.id,password=' '.join(context.args))
    
async def ask_q(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    
    cur.execute("SELECT id FROM USER WHERE telegram_id=?", (update.effective_user.id,))
    user_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO QUESTIONS (user_id, q_text) VALUES (?,?)", (user_id, ' '.join(context.args))
        )
    id = cur.lastrowid
    await context.bot.send_message(chat_id=GROUP_ID, text=(' '.join(context.args) + "\n\nID: " + str(id)))

async def create_poll(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return

    poll = update.effective_message.poll
    
    await context.bot.send_poll(
        chat_id=GROUP_ID,
        question=poll.question, 
        options=[i.text for i in poll.options],
        is_anonymous=poll.is_anonymous,
        allows_multiple_answers=poll.allows_multiple_answers
        )

async def answer_q_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    
    a_text = ' '.join(context.args)
    user_id = update.effective_user.id
    anon = True
    in_group = False

    q_id = context.args[0]
    
    if not q_id.isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Please enter first the ID-Number and then your reply. Try again!")
        return 
    
    cur.execute("SELECT id FROM QUESTIONS WHERE id=?", (q_id,))
    entry = cur.fetchall()
    if len(entry) == 0:
        await context.bot.send_message(chat_id=chat_id, text="It seems that the ID-Number is incorrect. Try again!")
        return 

    cur.execute(
        "INSERT INTO ANSWERS (q_id, user_id, a_text, anon, in_group) VALUES (?,?,?,?,?)", 
        (q_id, user_id, 'ID: ' + a_text, anon, in_group)
        )   

    cur.execute("SELECT user_id FROM QUESTIONS WHERE id=?", (q_id,))
    user_id = cur.fetchone()

    cur.execute("SELECT telegram_id FROM USER WHERE id=?", user_id)
    chat_id = cur.fetchone()[0]
    
    await context.bot.send_message(chat_id=int(chat_id), text="ID: " + a_text)

async def answer_q_group_command(update:Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    
    a_text = ' '.join(context.args)
    user_id = update.effective_user.id
    anon = True
    in_group = True

    q_id = context.args[0]
    
    if not q_id.isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Please enter first the ID-Number and then your reply. Try again!")
        return 
    
    cur.execute("SELECT id FROM QUESTIONS WHERE id=?", (q_id,))
    entry = cur.fetchall()
    if len(entry) == 0:
        await context.bot.send_message(chat_id=chat_id, text="It seems that the ID-Number is incorrect. Try again!")
        return 

    cur.execute(
        "INSERT INTO ANSWERS (q_id, user_id, a_text, anon, in_group) VALUES (?,?,?,?,?)", 
        (q_id, user_id, 'ID: ' + a_text, anon, in_group)
        )   

    await context.bot.send_message(chat_id=int(GROUP_ID), text="ID: " + a_text)


async def report_question(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not context.args[0].isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Enter the ID-Number first, followed by your reason!")
        return

    reporter_id = update.effective_user.id
    cur.execute("SELECT user_id FROM QUESTIONS WHERE id=?", (context.args[0],))
    reported_user_id = cur.fetchone()[0]
    
    cur.execute(
        "INSERT INTO  REPORTS (reporter_id, reported_user_id, reported_q_id, why) VALUES (?,?,?,?)", 
        (reporter_id, reported_user_id, context.args[0], ' '.join(context.args[1:]))
        )   

async def report_answer(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not context.args[0].isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Enter the ID-Number first, followed by your reason!")
        return

    reporter_id = update.effective_user.id
    cur.execute("SELECT user_id FROM ANSWERS WHERE id=?", (context.args[0],))
    reported_user_id = cur.fetchone()[0]
    
    cur.execute(
        "INSERT INTO  REPORTS (reporter_id, reported_user_id, reported_a_id, why) VALUES (?,?,?,?)", 
        (reporter_id, reported_user_id, context.args[0], ' '.join(context.args[1:]))
        )   

#HELPERS
async def user_auth(chat_id, user_id, context):
    if context.bot.get_chat_member(chat_id, user_id):
        #TODO Set auth in DB

        cur.execute("SELECT telegram_id FROM USER WHERE telegram_id=?", (user_id,))
        entry = cur.fetchall()
        if len(entry) == 0:
            # Create Data Entry
            with con:
                con.execute(
                "INSERT INTO USER (telegram_id) VALUES (?)", (user_id,)
                )
        else:
            await context.bot.send_message(chat_id=chat_id, text="You are already authorised!")
            return True

        await context.bot.send_message(chat_id=chat_id, text="Congrats you can now use the bot! Enter the /help command to see how everything works")
        return True
    else:
        await context.bot.send_message(chat_id=chat_id, text="Seems like you are not in the group or there was a mistake while trying to authenticate you, pls try /start again or enter the command /password followed by the password for our special website")
        return False
    
async def user_auth_pw(chat_id, user_id, context, password):
    if password == os.environ.get("AUTH"):
        #TODO Set auth in DB

        # TODO Repetitive 
        cur.execute("SELECT telegram_id FROM USER WHERE telegram_id=?", (user_id,))
        entry = cur.fetchall()
        if len(entry) == 0:
            # Create Data Entry
            with con:
                con.execute(
                "INSERT INTO USER (telegram_id) VALUES (?)", (user_id,)
                )
        else:
            await context.bot.send_message(chat_id=chat_id, text="You are already authorised!")
            return True
        
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
    #handlers.append(CommandHandler('report', report))
    handlers.append(MessageHandler(filters.POLL, create_poll))

    #handlers.append(MessageHandler(filters.REPLY), answer_q_reply)
    handlers.append(CommandHandler('a', answer_q_command))
    handlers.append(CommandHandler('a_group', answer_q_group_command))
    
    application.add_handlers(handlers=handlers)
    
    application.run_polling()

    