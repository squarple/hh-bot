from datetime import datetime
from telebot import types
from telebot import types
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_date(date_str):
  if date_str == 'N/A':
    return 'N/A'
  try:
    if '.' in date_str:
      date_str = date_str.split('.')[0] + 'Z'
    dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    formatted_date = dt.strftime('%d.%m.%Y %H:%M')
    return formatted_date
  except ValueError:
    return 'N/A'

def get_headers(user) -> dict:
  return { 'Authorization': f'Bearer {user.accessToken}' }

def send_error_message(bot, chat_id, response):
  bot.send_message(chat_id, f"Ошибка: {response.status_code}\n\n{response.text}")

def create_keyboard():
  keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
  buttons = [
    ('Авторизоваться', 'auth'),
    ('Мои решения', 'my_reviews'),
    ('На проверку', 'reviews_to_do'),
    ('Домашки', 'homeworks')
  ]
  for text, _ in buttons:
    keyboard.add(types.KeyboardButton(text))
  return keyboard

def fetch_data(url: str, headers: dict = None):
  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      return response.json()
    else:
      logging.error(f"Error fetching data from {url}: {response.status_code}")
      print(response.text)
      return None
  except Exception as e:
    logging.error(f"Exception occurred: {e}")
    return None
