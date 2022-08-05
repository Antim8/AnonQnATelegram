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


import sqlite3 as sl

#TODO Prevent bots from sending messages by checking update effetive user is_bot
#TODO Evtl. Emojis oder ahnliches hinzufuegen um die IDs besser unterscheiden zu koennen 
#TODO Poll
#TODO teilweise inkosistent da manchmal die telegram_id abgespeichert wird und andernmal die DB-ID 
#TODO help_cmd HelpText schreiben
#TODO Testing 
# No encouragement to "Try again!". redundant and not fitting -> No exclamation marks 

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
    #! repetetive
    permitted, banned_until = await check_status(chat_id=chat_id, user_id=update.effective_user.id, context=context)
    if not permitted:
        if banned_until == 0:
            #? Wofür ist das return?
            return 
        await context.bot.send_message(chat_id=chat_id, text="You are banned until " + banned_until + '!')
        return
    
    cur.execute("SELECT id FROM USER WHERE telegram_id=?", (update.effective_user.id,))
    user_id = cur.fetchone()[0]

    # change structure, update not necessary
    cur.execute(
        "INSERT INTO QUESTIONS (user_id, q_text) VALUES (?,?)", (user_id, ' '.join(context.args))
        )
    id = cur.lastrowid
    message = await context.bot.send_message(chat_id=GROUP_ID, text=(' '.join(context.args) + "\n\nID: " + str(id)))
    
    cur.execute("UPDATE QUESTIONS SET message_id=? WHERE id=?", (message.message_id, id))

    


async def create_poll(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    permitted, banned_until = await check_status(chat_id=chat_id, user_id=update.effective_user.id, context=context)
    if not permitted:
        if banned_until == 0:
            return 
        await context.bot.send_message(chat_id=chat_id, text="You are banned until " + banned_until + '!')
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
    permitted, banned_until = await check_status(chat_id=chat_id, user_id=update.effective_user.id, context=context)
    if not permitted:
        if banned_until == 0:
            return 
        await context.bot.send_message(chat_id=chat_id, text="You are banned until " + banned_until + '!')
        return
    
    a_text = ' '.join(context.args)
    user_id = update.effective_user.id
    anon = True
    in_group = False

    q_id = context.args[0]
    
    #? Check auf int besser?
    if not q_id.isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Please enter the ID-Number first and then your reply.")
        return 
    
    cur.execute("SELECT id FROM QUESTIONS WHERE id=?", (q_id,))
    #! to be made uniform, sometime fetchall sometime fetchonce <- There can only be one
    entry = cur.fetchall()
    if len(entry) == 0:
        await context.bot.send_message(chat_id=chat_id, text="It seems that the ID-Number is incorrect.")
        return 

    cur.execute(
        "INSERT INTO ANSWERS (q_id, user_id, a_text, anon, in_group) VALUES (?,?,?,?,?)", 
        (q_id, user_id, 'ID: ' + a_text, anon, in_group)
        )   
    id = cur.lastrowid

    cur.execute("SELECT user_id FROM QUESTIONS WHERE id=?", (q_id,))
    user_id = cur.fetchone()

    # Increase the number of answers the question received 
    cur.execute("UPDATE QUESTIONS SET num_answers = num_answers + 1 WHERE id=? ", (q_id,))

    cur.execute("SELECT telegram_id FROM USER WHERE id=?", user_id)
    chat_id = cur.fetchone()[0]

    #TODO The user asking the question cannot really connect it to an ID and AnswerId not helpfull either
    #TODO if needed to report rather report as answer to it? <- not necessary though
    await context.bot.send_message(chat_id=int(chat_id), text="ID: " + a_text + "\n\nID: " + str(id))

#? Answering in group shouldnt be a command but rather a Message Handler
async def answer_q_group_command(update:Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    permitted, banned_until = await check_status(chat_id=chat_id, user_id=update.effective_user.id, context=context)
    if not permitted:
        if banned_until == 0:
            return 
        await context.bot.send_message(chat_id=chat_id, text="You are banned until " + banned_until + '!')
        return
    
    a_text = ' '.join(context.args)
    user_id = update.effective_user.id
    #! Answering in Group can logically never be anon
    anon = True
    in_group = True

    q_id = context.args[0]
    
    #! same as above not for group communication
    if not q_id.isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Please enter first the ID-Number and then your reply. Try again!")
        return 
    
    cur.execute("SELECT id FROM QUESTIONS WHERE id=?", (q_id,))
    entry = cur.fetchall()
    if len(entry) == 0:
        await context.bot.send_message(chat_id=chat_id, text="It seems that the ID-Number is incorrect. Try again!")
        return 

    # Increase the number of answers the question received 
    cur.execute("UPDATE QUESTIONS SET num_answers = num_answers + 1 WHERE id=? ", (q_id,))

    #! same as above 
    cur.execute(
        "INSERT INTO ANSWERS (q_id, user_id, a_text, anon, in_group) VALUES (?,?,?,?,?)", 
        (q_id, user_id, 'ID: ' + a_text, anon, in_group)
        )   
    id = cur.lastrowid

    #! same as above on normal q
    message = await context.bot.send_message(chat_id=int(GROUP_ID), text="ID: " + a_text + "\n\nID: " + str(id))

    cur.execute("UPDATE ANSWERS SET message_id=? WHERE id=?", (message.message_id, id))



async def report_question(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # TODO Here Reporter_ID is the telegram chat ID and reported_user_id is the id by the database 
    #? Reporter Id should be telegram user ID <- if new user add him to the system

    if not context.args[0].isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Enter the ID-Number first, followed by your reason")
        return

    reporter_id = update.effective_user.id
    cur.execute("SELECT user_id FROM QUESTIONS WHERE id=?", (context.args[0],))
    entry = cur.fetchone()
    if entry == None:
        await context.bot.send_message(chat_id=chat_id, text="It seems that the ID-Number is incorrect. Try again!")
        return 
    reported_user_id = entry[0]

    cur.execute("SELECT 1 FROM REPORTS WHERE reporter_id=? AND reported_q_id=?", (reporter_id, int(context.args[0])))
    permitted = cur.fetchone()
    if permitted is not None:
        #? Message seems unnecassary
        await context.bot.send_message(chat_id=chat_id, text="You already reported the question!")
        return 

    if len(context.args) < 2:
        await context.bot.send_message(chat_id=chat_id, text="Please give a reason after the ID-Number!")
        return 

    # increase num_reported of the question
    cur.execute(
        "UPDATE QUESTIONS SET num_reported = num_reported + 1 WHERE id=?", 
        (context.args[0],)
        )  
    
    cur.execute(
        "INSERT INTO  REPORTS (reporter_id, reported_user_id, reported_q_id, why) VALUES (?,?,?,?)", 
        (reporter_id, reported_user_id, context.args[0], ' '.join(context.args[1:]))
        )   

    num_group_members = await context.bot.get_chat_member_count(chat_id=int(GROUP_ID))
    required_reports_to_ban = math.isqrt(num_group_members)
    #! Time check needed 
    cur.execute("SELECT COUNT(reported_q_id) FROM REPORTS WHERE reported_q_id=?", (context.args[0],))
    num_reports = cur.fetchone()[0]

    if required_reports_to_ban <= num_reports:

        cur.execute("SELECT banned FROM QUESTIONS WHERE id=?", (context.args[0],))
        banned = cur.fetchone()[0]
    
        if banned:
            await context.bot.send_message(chat_id=chat_id, text="The respective account is banned.")
            return 

        cur.execute("SELECT message_id FROM QUESTIONS WHERE id=?", (context.args[0],))
        message_id = cur.fetchone()[0]
        await context.bot.delete_message(chat_id=GROUP_ID, message_id=message_id)
        
        cur.execute("UPDATE QUESTIONS SET banned=1 WHERE id=?", (context.args[0],)) 

        cur.execute(
        "UPDATE USER SET banned_until = DATE('now', '+3 day') WHERE id=?", 
        (reported_user_id,)
        )  
        cur.execute("SELECT telegram_id FROM USER WHERE id=?", (reported_user_id,))
        telegram_id = cur.fetchone()[0]
        #! Hardcoded answer
        await context.bot.send_message(chat_id=telegram_id, text="Your Question with the ID: " + context.args[0] +  " received mutiple reports! You are banned for three days.")
    
        
async def report_answer(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not context.args[0].isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Enter the ID-Number first, followed by your reason!")
        return

    reporter_id = update.effective_user.id
    cur.execute("SELECT user_id FROM ANSWERS WHERE id=?", (context.args[0],))
    entry = cur.fetchone()
    if entry == None:
        await context.bot.send_message(chat_id=chat_id, text="It seems that the ID-Number is incorrect. Try again!")
        return 
    reported_user_id = entry[0]

    cur.execute("SELECT 1 FROM REPORTS WHERE reporter_id=? AND reported_a_id=?", (reporter_id, int(context.args[0])))
    #TODO needs cleaning
    permitted = cur.fetchone()
    #if permitted is not None:
    #    await context.bot.send_message(chat_id=chat_id, text="You already reported the answer!")
    #    return 

    if len(context.args) < 2:
        #? Should reason be a need or an option?
        await context.bot.send_message(chat_id=chat_id, text="Please give a reason after the ID-Number!")
        return 
    
    # increase num_reported of the answer
    cur.execute(
        "UPDATE ANSWERS SET num_reported = num_reported + 1 WHERE id=?", 
        (context.args[0],)
        )  
    
    cur.execute(
        "INSERT INTO  REPORTS (reporter_id, reported_user_id, reported_a_id, why) VALUES (?,?,?,?)", 
        (reporter_id, reported_user_id, context.args[0], ' '.join(context.args[1:]))
        )   

    num_group_members = await context.bot.get_chat_member_count(chat_id=int(GROUP_ID))
    required_reports_to_ban = math.isqrt(num_group_members)
    cur.execute("SELECT COUNT(reported_q_id) FROM REPORTS WHERE reported_a_id=?", (context.args[0],))
    num_reports = cur.fetchone()[0]

    if required_reports_to_ban <= num_reports:

        cur.execute("SELECT banned FROM ANSWERS WHERE id=?", (context.args[0],))
        banned = cur.fetchone()[0]
        if banned:
            await context.bot.send_message(chat_id=chat_id, text="The respective account is banned.")
            return
        
        cur.execute("SELECT message_id FROM ANSWERS WHERE id=?", (context.args[0],))
        message_id = cur.fetchone()[0]
        await context.bot.delete_message(chat_id=GROUP_ID, message_id=message_id)
        
        
        cur.execute("UPDATE QUESTIONS SET banned=1 WHERE id=?", (context.args[0],)) 
        #TODO try to delete q 

        cur.execute("SELECT id FROM USER WHERE telegram_id=?", (reported_user_id,))
        id = cur.fetchone()[0]

        cur.execute(
        "UPDATE USER SET banned_until = DATE('now', '+3 day') WHERE id=?", 
        (id,)
        )  
        
        #! Hardcoded answer
        await context.bot.send_message(chat_id=reported_user_id, text="Your Answer with the ID: " + context.args[0] +  " received mutiple reports! You are banned for three days.")


#HELPERS
async def user_auth(chat_id, user_id, context):
    if await context.bot.get_chat_member(chat_id, user_id):
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

async def check_status(chat_id, user_id, context):

    
    cur.execute("SELECT id FROM USER WHERE telegram_id=?", (user_id,))
    user_id = cur.fetchone()
    #TODO irrelevant because should be impossible to reach
    if user_id is None:
        await context.bot.send_message(chat_id=chat_id, text="Authenticate with /Start .")
        return False, 0
    else:
        user_id = user_id[0]
    
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=chat_id, text="You have to specify an ID, followed by the respective content.")
        return False, 0

    
    cur.execute("SELECT banned_until from USER WHERE id=?", (user_id,))
    banned_until = cur.fetchone()[0]
    if banned_until == None:
        return True, 0
    else:
        return False, banned_until
    
    



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

    