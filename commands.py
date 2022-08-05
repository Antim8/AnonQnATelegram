import os
import math 
import sqlite3 as sl
from dotenv import load_dotenv
from telegram.ext import ContextTypes
from telegram import Update
from helpers import user_auth, user_auth_pw, check_status

load_dotenv()
GROUP_ID = os.environ.get('GROUP_ID')

DB_NAME = os.environ.get("DB_NAME")
con = sl.connect(DB_NAME)
cur = con.cursor()

async def start(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Induce the authentication process of the user."""

    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
    
    await context.bot.send_message(chat_id=chat_id, text="Hey there, pls wait while I try to authenticate you")
    await user_auth(chat_id=chat_id, user_id=update.effective_user.id, context=context, cur=cur)
    con.commit()
    
async def help_cmd(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Descriptions of the telegram bot commands."""

    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return

    #TODO Change into usefull helptext
    await context.bot.send_message(chat_id=chat_id, text="HELPTEXT")

async def pw_auth(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Authenticate by password."""
    chat_id = update.effective_chat.id
    if chat_id == int(GROUP_ID):
        return
        
    await user_auth_pw(chat_id=chat_id, context=context, user_id=update.effective_user.id,password=' '.join(context.args), cur=cur)
    con.commit()
    
async def ask_q(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """The bot sends the received question into the telegram group without the questioners identiy. """
    
    chat_id, telegram_user_id = update.effective_chat.id, update.effective_user.id

    permitted = await check_status(chat_id=chat_id, user_id=telegram_user_id, context=context, cur=cur, group_id=GROUP_ID)
    con.commit()
    if not permitted:
        return
    
    with con:

        cur.execute("SELECT id FROM USER WHERE telegram_id=?", (telegram_user_id,))
        user_id = cur.fetchone()[0]

        cur.execute("SELECT id FROM QUESTIONS ORDER BY id DESC LIMIT 1")
        max_id = cur.fetchone()[0]
        id = int(max_id) + 1

        message = await context.bot.send_message(chat_id=GROUP_ID, text=(' '.join(context.args) + "\n\n" + "\u2753" + "ID: "  + str(id)))

        cur.execute(
            "INSERT INTO QUESTIONS (user_id, q_text, message_id) VALUES (?,?,?)", (user_id, ' '.join(context.args), message.message_id)
            )

        con.commit()

async def create_poll(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """The bot sends a received poll into the telegram group without the senders identiy."""
    
    chat_id, telegram_user_id = update.effective_chat.id, update.effective_user.id

    permitted = await check_status(chat_id=chat_id, user_id=telegram_user_id, context=context, cur=cur, group_id=GROUP_ID)
    con.commit()
    if not permitted:
        return

    poll = update.effective_message.poll
    with con:
        
        cur.execute("SELECT id FROM USER WHERE telegram_id=?", (telegram_user_id,))
        user_id = cur.fetchone()[0]
        
        group_poll = await context.bot.send_poll(
            chat_id=GROUP_ID,
            question=poll.question, 
            options=[i.text for i in poll.options],
            is_anonymous=poll.is_anonymous,
            allows_multiple_answers=poll.allows_multiple_answers
            )
        
        cur.execute("INSERT INTO QUESTIONS(user_id, q_text, message_id) VALUES(?,?,?)",(user_id, poll.question, group_poll.message_id ))
        con.commit()
        
async def answer_q_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the answer of an anonymous question to the questioner without the answers identity."""
   
    chat_id, telegram_user_id = update.effective_chat.id, update.effective_user.id

    permitted = await check_status(chat_id=chat_id, user_id=telegram_user_id, context=context, cur=cur, group_id=GROUP_ID)
    con.commit()
    if not permitted:
        return
    
    a_text = ' '.join(context.args[1:])
    user_id = update.effective_user.id
    anon = True
    in_group = False

    q_id = context.args[0]
    
    if not q_id.isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="Please enter the ID-Number first and then your reply.")
        return 
    
    cur.execute("SELECT id FROM QUESTIONS WHERE id=?", (q_id,))
    entry = cur.fetchone()
    if entry == None:
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
    await context.bot.send_message(chat_id=int(chat_id), text="\u2753ID: "+ q_id + "\n\n" + a_text + "\n\n\u2757ID: " + str(id))
    con.commit()

#? Answering in group shouldnt be a command but rather a Message Handler
async def answer_q_group_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the answer of an anonymous question in the group without the answers identity."""

    chat_id, telegram_user_id = update.effective_chat.id, update.effective_user.id

    permitted = await check_status(chat_id=chat_id, user_id=telegram_user_id, context=context, cur=cur, group_id=GROUP_ID)
    con.commit()
    if not permitted:
        return
    
    a_text = ' '.join(context.args[1:])
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
    entry = cur.fetchone()
    if entry == None:
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
    message = await context.bot.send_message(chat_id=int(GROUP_ID), text="\u2753ID: "+ q_id + "\n\n" + a_text + "\n\n\u2757ID: " + str(id))

    cur.execute("UPDATE ANSWERS SET message_id=? WHERE id=?", (message.message_id, id))
    con.commit()



async def report_question(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Report a question."""
    
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
    con.commit()
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
        con.commit()
        #! Hardcoded answer
        await context.bot.send_message(chat_id=telegram_id, text="Your Question with the ID: " + context.args[0] +  " received mutiple reports! You are banned for three days.")
    
        
async def report_answer(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Report an answer."""
    
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
    if permitted is not None:
        await context.bot.send_message(chat_id=chat_id, text="You already reported the answer!")
        return 

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
    con.commit()

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
        con.commit()
        #! Hardcoded answer
        await context.bot.send_message(chat_id=reported_user_id, text="Your Answer with the ID: " + context.args[0] +  " received mutiple reports! You are banned for three days.")
