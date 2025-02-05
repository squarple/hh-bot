import sqlite3
from models import BotUser

def create_table():
  with sqlite3.connect('bot_users.db') as conn:
    cursor = conn.cursor()
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS users (
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        chat_id INTEGER UNIQUE NOT NULL
      )
    ''')
    conn.commit()

def get_connection():
    return sqlite3.connect('bot_users.db')

def add_user(bot_user: BotUser):
  try:
    with sqlite3.connect('bot_users.db') as conn:
      cursor = conn.cursor()
      cursor.execute('INSERT INTO users (username, password, chat_id) VALUES (?, ?, ?)', 
                      (bot_user.username, bot_user.password, bot_user.chat_id))
      conn.commit()
    return True
  except sqlite3.IntegrityError:
    return False

def is_user_exist(chat_id):
  with sqlite3.connect('bot_users.db') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
  return result is not None

def get_user(chat_id):
  with sqlite3.connect('bot_users.db') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT username, password, chat_id FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
  if result:
    return BotUser(username=result[0], password=result[1], chat_id=result[2])
  return None
