import os
from datetime import datetime

async def user_auth(chat_id, user_id, context, cur):
    """Insert a new user into the database if not already existing.
    
    Keyword arguments:
    chat_id -- the telegram id of the chat
    user_id -- the telegram id of the user
    context -- convenience class to gather customizable types of the telegram.ext.CallbackContext interface
    cur     -- curser object of the sql database connection
    """
    if await context.bot.get_chat_member(chat_id, user_id):
        
        cur.execute("SELECT telegram_id FROM USER WHERE telegram_id=?;", (user_id,))
        entry = cur.fetchone()
        if entry == None:
            # Insert the new user into the table USER
            cur.execute(
            "INSERT INTO USER (telegram_id) VALUES (?)", (user_id,)
            )
        else:
            # The telegram id of the user already exists in the table USER
            await context.bot.send_message(chat_id=chat_id, text="You are already authorised!")
            return True

        await context.bot.send_message(chat_id=chat_id, text="Congrats you can now use the bot! Enter the /help command to see how everything works")
        return True
    else:
        await context.bot.send_message(chat_id=chat_id, text="Seems like you are not in the group or there was a mistake while trying to authenticate you, pls try /start again or enter the command /password followed by the password for our special website")
        return False
    
async def user_auth_pw(chat_id, user_id, context, password, cur):
    """Insert a new user into the database if not already existing.
    
    Keyword arguments:
    chat_id  -- the telegram id of the chat
    user_id  -- the telegram id of the user
    context  -- convenience class to gather customizable types of the telegram.ext.CallbackContext interface
    password -- the correct password 
    cur      -- curser object of the sql database connection
    """
    if password == os.environ.get("AUTH"):
        #TODO Set auth in DB

        # TODO Repetitive 
        cur.execute("SELECT telegram_id FROM USER WHERE telegram_id=?", (user_id,))
        entry = cur.fetchone()
        if entry == None:
            # Insert the new User into the table USER
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

async def check_status(chat_id, user_id, context, cur, group_id):
    """Check the status of the user and handel it respectively. 

    Keyword arguments:
    chat_id  -- the telegram id of the chat
    user_id  -- the telegram id of the user
    context  -- convenience class to gather customizable types of the telegram.ext.CallbackContext interface
    cur      -- curser object of the sql database connection
    group_id -- the telegram id of the group
    """

    # Check if the chat id is not the group id 
    if chat_id == int(group_id):
        return False

    # Check if the user is already authenticated 
    cur.execute("SELECT id FROM USER WHERE telegram_id=?", (user_id,))
    user_id = cur.fetchone()
    if user_id is None:
        await context.bot.send_message(chat_id=chat_id, text="Authenticate with /Start .")
        return False
    user_id = user_id[0]
    
    # Check if the command message included content
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=chat_id, text="You have to specify an ID, followed by the respective content.")
        return False

    cur.execute("SELECT banned_until from USER WHERE id=?", (user_id,))
    banned_until = cur.fetchone()[0]
    
    if banned_until == None:
        return True
    
    # Check if the user is still banned
    current_date = datetime.today().date() 
    banned_date  = datetime.strptime(banned_until, '%Y-%m-%d').date()

    if current_date > banned_date:
        return True
    else:
        await context.bot.send_message(chat_id=chat_id, text="You are banned until " + banned_until + '.')
        return False
    