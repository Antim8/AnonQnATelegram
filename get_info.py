import asyncio
from re import L
import telegram
import dotenv
import os

async def main():
    dotenv.load_dotenv()
    TOKEN = os.environ.get('TELEGRAM_API_KEY')
    bot = telegram.Bot(token=TOKEN)
    async with bot:
        bot = await bot.get_me()
        print("Information about the bot: ")
        print("Name: ", bot['username'])
        print("ID: ", bot['id'])
        
if __name__ == "__main__":
    asyncio.run(main())