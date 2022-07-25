import sqlite3 as sl
import os 
from dotenv import load_dotenv
load_dotenv()
DB_NAME = os.environ.get("DB_NAME")
con = sl.connect(DB_NAME)

