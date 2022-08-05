import asyncio
import os

async def user_auth(chat_id, user_id, context, cur):
    if await context.bot.get_chat_member(chat_id, user_id):
        #TODO Set auth in DB

    
        cur.execute("SELECT telegram_id FROM USER WHERE telegram_id=?;", (user_id,))
        entry = cur.fetchall()
        if len(entry) == 0:
            # Create Data Entry
            cur.execute(
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
    
async def user_auth_pw(chat_id, user_id, context, password, cur):
    if password == os.environ.get("AUTH"):
        #TODO Set auth in DB

        # TODO Repetitive 
        cur.execute("SELECT telegram_id FROM USER WHERE telegram_id=?", (user_id,))
        entry = cur.fetchall()
        if len(entry) == 0:
            # Create Data Entry
            with cur:
                cur.execute(
                "INSERT INTO USER (telegram_id) VALUES (?)", (user_id,)
                )
        else:
            await context.bot.send_message(chat_id=chat_id, text="You are already authorised!")
            return True
        
        await context.bot.send_message(chat_id=chat_id, text="Congrats you can now use the bot! Enter the /help command to see how everything works")
        return True
    else:
        await context.bot.send_message(chat_id=chat_id, text="Wrong password, pls try again")
        #TODO pw try count up
        return False

async def check_status(chat_id, user_id, context, cur):

    
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
    