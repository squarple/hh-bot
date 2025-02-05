from datetime import datetime
from telebot import types
from models import User, Homework, Review

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

def get_headers(user:User) -> dict:
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

def homework_to_message(hw:Homework):
  return f"<b>{hw.name}</b>\n" \
          f"<a href='{hw.repositoryLink}'>Repo Link</a>\n" \
          f"Deadline: {parse_date(hw.completionDeadline)}\n" \
          f"Status: <b>{hw.status}</b>\n\n"

def review_to_message(r:Review):
  message_to_send = f"reviewId: {r.reviewId}\n"
  message_to_send += f"Status: <b>{r.status}</b>\n"
  if r.reviewAttempts and len(r.reviewAttempts) > 0:
    resolution = r.reviewAttempts[0].get('resolution', 'Нет комментария')
    message_to_send += f"Комментарий: <i>{resolution}</i>\n\n"
  else:
    message_to_send += "\n"
  return message_to_send
