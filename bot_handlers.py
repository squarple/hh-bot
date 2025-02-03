from telebot import TeleBot
from models import User, Homework, Review, json_to_user, json_to_homework, json_to_review
from utils import fetch_data, parse_date, send_error_message, create_keyboard, get_headers
import os
from dotenv import load_dotenv
import requests
import yaml

load_dotenv()
token = os.getenv('AUTH_TOKEN')
bot = TeleBot(token)
user = None

login = os.getenv('HHDEV_LOGIN')
password = os.getenv('HHDEV_PASSWORD')

with open('hhdev_api.yaml', 'r', encoding='utf-8') as config_file:
  hhdev_api = yaml.safe_load(config_file)

def start(message):
  bot.send_message(message.chat.id, "Привет! Я бот.", reply_markup=create_keyboard())

def handle_message(message):
  handlers = {
    'Авторизоваться': authorize,
    'Мои решения': my_reviews,
    'На проверку': reviews_to_do,
    'Домашки': view_homeworks
  }
  action = handlers.get(message.text)
  if action:
    action(message.chat.id)
  else:
    bot.reply_to(message, 'Неизвестная команда')

def authorize(chat_id):
  global user
  payload = {"username": login, "password": password}
  response = requests.post(hhdev_api['auth_url'], json=payload)
  if response.status_code == 200:
    user = json_to_user(response.json())
    bot.send_message(chat_id, "Авторизация прошла успешно!")
  else:
    send_error_message(bot, chat_id, response)

def my_reviews(chat_id):
  global user
  homeworks = fetch_data(hhdev_api['homeworks_url'], headers=get_headers(user))
  if homeworks:
    hw_reviews_dict = {}
    for hw in homeworks.get('data', []):
      reviews = fetch_data(hhdev_api['my_reviews_url'].format(homework_id=hw['id']), headers=get_headers(user))
      if reviews:
        hw_reviews_dict[hw['name']] = [json_to_review(r) for r in reviews.get('data', [])]
    if hw_reviews_dict:
      for hw_name, reviews in hw_reviews_dict.items():
        message = f"<b>{hw_name}</b>\n\n"
        for r in reviews:
          message += f"reviewId: {r.reviewId}\nСтатус: <b>{r.status}</b>\n"
          if r.reviewAttempts and len(r.reviewAttempts) > 0:
            resolution = r.reviewAttempts[0].get('resolution', 'Нет комментария')
            message += f"Комментарий: <i>{resolution}</i>\n\n"
        bot.send_message(chat_id, message, parse_mode='HTML', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, "Нет доступных решений.")
  else:
    bot.send_message(chat_id, "Ошибка при получении данных.")

def reviews_to_do(chat_id):
  global user
  homeworks = fetch_data(hhdev_api['homeworks_url'], headers=get_headers(user))
  if homeworks:
    hw_reviews_dict = {}
    for hw in homeworks.get('data', []):
      reviews = fetch_data(hhdev_api['reviews_to_do_url'].format(homework_id=hw['id']), headers=get_headers(user))
      if reviews:
        hw_reviews_dict[hw['name']] = [json_to_review(r) for r in reviews.get('data', [])]
    if hw_reviews_dict:
      for hw_name, reviews in hw_reviews_dict.items():
        message = f"<b>{hw_name}</b>\n\n"
        for r in reviews:
          message += f"reviewId: {r.reviewId}\nСтатус: <b>{r.status}</b>\n"
          if r.reviewAttempts and len(r.reviewAttempts) > 0:
            resolution = r.reviewAttempts[0].get('resolution', 'Нет комментария')
            message += f"Комментарий: <i>{resolution}</i>\n\n"
        bot.send_message(chat_id, message, parse_mode='HTML', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, "Нет ревью для проверки.")
  else:
    bot.send_message(chat_id, "Ошибка при получении данных.")

def view_homeworks(chat_id):
  global user
  homeworks = fetch_data(hhdev_api['homeworks_url'], headers=get_headers(user))
  if homeworks:
    formatted_homeworks = "\n".join([
      f"<b>{hw['name']}</b>\n<a href='{hw['repositoryLink']}'>Repo Link</a>\n"
      f"Deadline: {parse_date(hw['completionDeadline'])}\nStatus: <b>{hw['status']}</b>\n"
      for hw in homeworks.get('data', []) if hw['status'] != 'COMPLETE'
    ])
    if formatted_homeworks:
      bot.send_message(chat_id, formatted_homeworks, parse_mode='HTML', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, "Нет доступных домашек.")
  else:
    bot.send_message(chat_id, "Ошибка при получении данных.")
