import sqlite3 as sl
import os 
from dotenv import load_dotenv

def create_db():
    """Create the database including of the USER, QUESTIONS, ANSWERS and REPORTS tables."""

    load_dotenv()
    DB_NAME = os.environ.get("DB_NAME")
    con = sl.connect(DB_NAME)

    with con:
        con.execute("""
                    CREATE TABLE USER (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        q_proposed INTEGER DEFAULT 0 NOT NULL,
                        a_given INTEGER DEFAULT 0 NOT NULL,
                        been_reported INTEGER DEFAULT 0 NOT NULL,
                        has_reported INTEGER DEFAULT 0 NOT NULL,
                        last_reported DATETIME,
                        banned_until DATE
                    );
        """)

    with con:
        con.execute("""
                    INSERT INTO USER (telegram_id) values(0);
                    """)

    with con:
        con.execute("""
                    CREATE TABLE QUESTIONS(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        q_text TEXT NOT NULL,
                        num_reported INTEGER DEFAULT 0 NOT NULL,
                        num_answers INTEGER DEFAULT 0 NOT NULL,
                        created_at DATETIME DEFAULT (datetime('now','localtime')),
                        message_id INTEGER,
                        banned BOOLEAN DEFAULT 0 NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES USER(id)
                    );
        """)

    with con:
        con.execute("""
                    INSERT INTO QUESTIONS (user_id, q_text) values(1, "");
                    """)

    with con:
        con.execute("""
                    CREATE TABLE ANSWERS(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        q_id INTEGER,
                        user_id INTEGER,
                        a_text TEXT NOT NULL,
                        anon BOOLEAN NOT NULL CHECK (anon IN(0, 1)),
                        in_group BOOLEAN NOT NULL CHECK (in_group IN(0, 1)),
                        num_reported INTEGER DEFAULT 0 NOT NULL,
                        created_at DATETIME DEFAULT (datetime('now','localtime')),
                        message_id INTEGER,
                        banned BOOLEAN DEFAULT 0 NOT NULL CHECK (banned IN(0, 1)),
                        FOREIGN KEY(q_id) REFERENCES QUESTIONS(id),
                        FOREIGN KEY(user_id) REFERENCES USERS(id)
                    );
        """)

    with con:
        con.execute("""
                    INSERT INTO ANSWERS (q_id, user_id, a_text, anon, in_group) values (1, 1, "", 0, 0);
                    """)

    #TODO Delte from Table when older than x (run regularly)

    with con:
        con.execute("""
                    CREATE TABLE REPORTS(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        reporter_id INTEGER,
                        reported_user_id INTEGER,
                        reported_q_id INTEGER DEFAULT 1,
                        reported_a_id INTEGER DEFAULT 1,
                        why TEXT,
                        reported_at DATETIME DEFAULT (datetime('now', 'localtime')),
                        FOREIGN KEY(reporter_id) REFERENCES USER(id),
                        FOREIGN KEY(reported_user_id) REFERENCES USER(id),
                        FOREIGN KEY(reported_q_id) REFERENCES QUESTIONS(id),
                        FOREIGN KEY(reported_a_id) REFERENCES ANSWERS(id)
                    );
        """)

if __name__ == "__main__":
    create_db()