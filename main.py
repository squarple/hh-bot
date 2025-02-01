import telebot
from telebot import types
import os
from dotenv import load_dotenv
import requests
from models import User, Homework, Review, json_to_user, json_to_homework, json_to_review
from datetime import datetime
import yaml

load_dotenv() 
token = os.getenv('AUTH_TOKEN')
login = os.getenv('HHDEV_LOGIN')
password = os.getenv('HHDEV_PASSWORD')

with open('hhdev_api.yaml', 'r', encoding='utf-8') as config_file:
    hhdev_api = yaml.safe_load(config_file)

bot = telebot.TeleBot(token)

user : User = None

def main():
  bot.polling()

@bot.message_handler(commands = ['start'])
def start(message):
  keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
  auth_button = types.KeyboardButton('Авторизоваться')
  my_reviews_button = types.KeyboardButton('Мои решения')
  reviews_to_do_button = types.KeyboardButton('На проверку')
  homeworks_button = types.KeyboardButton('Домашки')
  keyboard.add(auth_button, my_reviews_button, reviews_to_do_button, homeworks_button)
  bot.send_message(message.chat.id, "Привет! я бот.", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
  if message.text == 'Авторизоваться':
    authorize(message.chat.id);
  elif message.text == 'Мои решения':
    if user is None:
      authorize(message.chat.id)
    my_reviews(message.chat.id)
  elif message.text == 'На проверку':
    if user is None:
      authorize(message.chat.id)
    reviews_to_do(message.chat.id)
  elif message.text == 'Домашки':
    if user is None:
      authorize(message.chat.id)
    view_homeworks(message.chat.id)
  else:
    bot.reply_to(message, 'Неизвестная команда')

def reviews_to_do(chat_id):
  global user
  hw_response = requests.get(hhdev_api['homeworks_url'], headers=get_headers(user))
  
  if hw_response.status_code == 200:
    homeworks = [json_to_homework(hw) for hw in hw_response.json().get('data', [])]
    hw_reviews_dict = dict()
    
    for hw in homeworks:
      review_url = hhdev_api['reviews_to_do_url'].format(homework_id=hw.id)
      review_response = requests.get(review_url, headers=get_headers(user))
      
      if review_response.status_code == 200:
        reviews = [json_to_review(r) for r in review_response.json().get('data', [])]
        if reviews:
          hw_reviews_dict[hw.name] = reviews
      else:
        if 'No reviews to do' in review_response.text:
          continue
        send_error_message(chat_id, review_response)
    
    if hw_reviews_dict:
      for hw_name, reviews in hw_reviews_dict.items():
        message = ''
        message += f"<b>{hw_name}</b>\n\n"
        for r in reviews:
          message += f"reviewId: {r.reviewId}\n"
          message += f"Статус: <b>{r.status}</b>\n"
          if r.reviewAttempts and len(r.reviewAttempts) > 0:
            resolution = r.reviewAttempts[0].get('resolution', 'Нет комментария')
            message += f"Комментарий: <i>{resolution}</i>\n\n"
        bot.send_message(chat_id, message, parse_mode='HTML', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, "Нет ревью для проверки.")
  else:
    send_error_message(chat_id, hw_response)

def my_reviews(chat_id):
  global user
  hw_response = requests.get(hhdev_api['homeworks_url'], headers=get_headers(user))

  if hw_response.status_code == 200:
    homeworks = [json_to_homework(hw) for hw in hw_response.json().get('data', [])]
    hw_reviews_dict = dict()
    for hw in homeworks:
      hw_reviews_list = list()
      review_url = hhdev_api['my_reviews_url'].format(homework_id=hw.id)
      review_response = requests.get(review_url, headers = get_headers(user))

      if review_response.status_code == 200:
        reviews = [json_to_review(r) for r in review_response.json().get('data', [])]
        hw_reviews_list.append(reviews)
        hw_reviews_dict[hw.name] = hw_reviews_list
      else:
        if 'User has not created a solution yet' in review_response.text:
          continue
        send_error_message(chat_id, review_response)
    for hw_name, reviews_list in hw_reviews_dict.items():
      message = ''
      if reviews_list:
        message += f"<b>{hw_name}</b>\n\n"
        for r in reviews_list[0]:
          message += f"reviewId: {r.reviewId}\n"
          message += f"Статус: <b>{r.status}</b>\n"
          if r.reviewAttempts and len(r.reviewAttempts) > 0:
            resolution = r.reviewAttempts[0].get('resolution', 'Нет комментария')
            message += f"Комментарий: <i>{resolution}</i>\n\n"
      if message:
        bot.send_message(chat_id, message, parse_mode='HTML', disable_web_page_preview=True)
  else:
    send_error_message(chat_id, hw_response)

def view_homeworks(chat_id):
  global user
  response = requests.get(hhdev_api['homeworks_url'], headers=get_headers(user))
  
  if response.status_code == 200:
    homeworks = response.json().get('data', [])
    formatted_homeworks = format_homeworks(homeworks)
    if formatted_homeworks:
      bot.send_message(chat_id, formatted_homeworks, parse_mode='HTML', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, "Нет доступных домашек.")
  else:
    send_error_message(chat_id, response)

def format_homeworks(homeworks):
    result = []
    for hw in homeworks:
      name = hw.get('name', 'N/A')
      repository_link = hw.get('repositoryLink', 'N/A')
      start_date = parse_date(hw.get('startDate', 'N/A'))
      completion_deadline = parse_date(hw.get('completionDeadline', 'N/A'))
      status = hw.get('status', 'N/A') or 'N/A'
      
      repository_link_html = f"<a href='{repository_link}'>Repo Link</a>"
      
      result.append(f"<b>{name}</b>\n{repository_link_html}\nDeadline: {completion_deadline}\nStatus: {status}\n")
    
    return "\n".join(result) if result else ""

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

def authorize(chat_id):
  global user
  payload = {
    "username": login,
    "password": password
  }
  response = requests.post(hhdev_api['auth_url'], json=payload)
  if response.status_code == 200:
    user = json_to_user(response.json())
    bot.send_message(chat_id, "Авторизация прошла успешно!")
  else:
    send_error_message(chat_id, response)

def get_headers(user:User) -> dict:
  return { 'Authorization': f'Bearer {user.accessToken}' }

def send_error_message(chat_id, response):
  bot.send_message(chat_id, f"Код ошибки: {response.status_code}")
  bot.send_message(chat_id, f"Текст ответа: {response.text}")



bot.polling()