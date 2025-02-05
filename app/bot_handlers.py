from telebot import TeleBot
from models import BotUser, User, Homework, Review, json_to_user, json_to_homework, json_to_review
from utils import send_error_message, create_keyboard, get_headers, homework_to_message, review_to_message
import os
from dotenv import load_dotenv
import requests
import yaml
from database import add_user, is_user_exist, get_user

users = dict()
user_states = dict() # chat_id: state
chat_id_login_temp = dict() # chat_id: {login: '', password: ''}

load_dotenv()
token = os.getenv('AUTH_TOKEN')
bot = TeleBot(token)

with open('hhdev_api.yaml', 'r', encoding='utf-8') as config_file:
  hhdev_api = yaml.safe_load(config_file)

def start(message):
  chat_id = message.chat.id
  if chat_id in users:
    bot.send_message(chat_id, "Привет! Я бот.", reply_markup=create_keyboard())
  elif is_user_exist(message.chat.id):
    bot_user = get_user(chat_id)
    payload = {"username": bot_user.username, "password": bot_user.password}
    response = requests.post(hhdev_api['auth_url'], json=payload)
    if response.status_code == 200:
      user = json_to_user(response.json())
      users[chat_id] = user
      bot.send_message(chat_id, "Авторизация прошла успешно!", reply_markup=create_keyboard())
    else:
      send_error_message(bot, chat_id, response)
  else:
    user_states[chat_id] = 'login'
    bot.send_message(message.chat.id, "Привет! Я бот. Для начала работы введите свой логин.")

def handle_message(message):
  chat_id = message.chat.id
  handlers = {
    'Авторизоваться': authorize,
    'Мои решения': my_reviews,
    'На проверку': reviews_to_do,
    'Домашки': view_homeworks
  }
  action = handlers.get(message.text)
  if chat_id in user_states:
    authorize(message)
  elif action:
    if chat_id in users:
      action(message)
    elif is_user_exist(chat_id):
      bot_user = get_user(chat_id)
      payload = {"username": bot_user.username, "password": bot_user.password}
      response = requests.post(hhdev_api['auth_url'], json=payload)
      if response.status_code == 200:
        user = json_to_user(response.json())
        users[chat_id] = user
        bot.send_message(chat_id, "Авторизация прошла успешно!", reply_markup=create_keyboard())
        if action != authorize:
          action(message)
      else:
        send_error_message(bot, chat_id, response)
  else:
    bot.reply_to(message, 'Неизвестная команда')

def authorize(message):
  global users
  chat_id = message.chat.id
  if chat_id in users:
    bot.send_message(chat_id, "Авторизация прошла успешно!", reply_markup=create_keyboard())
  if is_user_exist(chat_id):
    bot_user = get_user(chat_id)
    payload = {"username": bot_user.username, "password": bot_user.password}
    response = requests.post(hhdev_api['auth_url'], json=payload)
    if response.status_code == 200:
      user = json_to_user(response.json())
      users[chat_id] = user
      bot.send_message(chat_id, "Авторизация прошла успешно!", reply_markup=create_keyboard())
    else:
      send_error_message(bot, chat_id, response)
  else:
    if chat_id in user_states:
      if user_states[chat_id] == 'login':
        chat_id_login_temp[chat_id] = {'login': message.text}
        user_states[chat_id] = 'password'
        bot.send_message(chat_id, "Введите пароль:")
      elif user_states[chat_id] == 'password':
        login = chat_id_login_temp[chat_id]['login']
        del chat_id_login_temp[chat_id]
        payload = {"username": login, "password": message.text}
        response = requests.post(hhdev_api['auth_url'], json=payload)
        if response.status_code == 200:
          bot_user = BotUser(username=login, password=message.text, chat_id=chat_id)
          users[chat_id] = json_to_user(response.json())
          if add_user(bot_user):
            bot.send_message(chat_id, "Пользователь успешно зарегистрирован!")
            users[chat_id] = json_to_user(response.json())
            bot.send_message(chat_id, "Авторизация прошла успешно!", reply_markup=create_keyboard())
          else:
            bot.send_message(chat_id, "Неправильные логин или пароль!")
            user_states[chat_id] = 'login'
            bot.send_message(chat_id, "Введите логин:")

        else:
          bot.send_message(chat_id, "Неправильные логин или пароль!")
          user_states[chat_id] = 'login'
          bot.send_message(chat_id, "Введите логин:")
    else:
      user_states[chat_id] = 'login'
      bot.send_message(chat_id, "Введите логин:")

def my_reviews(message):
  global users
  chat_id = message.chat.id

  homeworks_error, homeworks = fetch_homeworks(users[chat_id])
  if homeworks_error is None:
    for hw in homeworks:
      if hw.status == None:
        bot.send_message(chat_id, f"<b>{hw.name}</b>\n\nВы еще не отправили домашку на проверку!", parse_mode='HTML')
      elif hw.status != 'COMPLETE':
        message_to_send = ''
        reviews_error, reviews = get_my_reviews(users[chat_id], hw)
        if reviews_error is None:
          if reviews:
            message_to_send += f"<b>{hw.name}</b>\n\n"
            for r in reviews:
              if r.status != 'APPROVED':
                message_to_send += f"reviewId: {r.reviewId}\n"
                message_to_send += f"Status: <b>{r.status}</b>\n"
                if r.reviewAttempts and len(r.reviewAttempts) > 0:
                  resolution = r.reviewAttempts[0].get('resolution', 'Нет комментария')
                  message_to_send += f"Комментарий: <i>{resolution}</i>\n"
                message_to_send += "\n"
            bot.send_message(chat_id, message_to_send, parse_mode='HTML', disable_web_page_preview=True)
        else:
          bot.send_message(chat_id, "Ошибка при получении данных, попробуйте позже!")
          bot.send_message(chat_id, reviews_error)
  else:
    bot.send_message(chat_id, "Ошибка при получении данных, попробуйте позже!")
    bot.send_message(chat_id, homeworks_error)

def reviews_to_do(message):
  global users
  is_reviews_to_do_exists = False
  chat_id = message.chat.id
  homeworks_error, homeworks = fetch_homeworks(users[chat_id])
  if homeworks_error is None:
    for hw in homeworks:
      if hw.status != 'COMPLETE':
        message_to_send = ''
        reviews_error, reviews = get_reviews_to_do(users[chat_id], hw)
        if reviews_error is None:
          if reviews:
            message_to_send += f"<b>{hw.name}</b>\n\n"
            for r in reviews:
              if r.status != 'APPROVED':
                is_reviews_to_do_exists = True
                message_to_send += review_to_message(r)
            bot.send_message(chat_id, message_to_send, parse_mode='HTML', disable_web_page_preview=True)
        else:
          bot.send_message(chat_id, "Ошибка при получении данных, попробуйте позже!")
          bot.send_message(chat_id, reviews_error)
  else:
    bot.send_message(chat_id, "Ошибка при получении данных, попробуйте позже!")
    bot.send_message(chat_id, homeworks_error)
  if is_reviews_to_do_exists == False:
    bot.send_message(chat_id, "Нет заданий на проверку!")

def view_homeworks(message):
  global users
  chat_id = message.chat.id
  error, homeworks = fetch_homeworks(users[chat_id])
  if error is None:
    message_to_send = ''
    for hw in homeworks:
      if hw.status != 'COMPLETE':
        message_to_send += homework_to_message(hw)
    if message_to_send:
      bot.send_message(chat_id, message_to_send, parse_mode='HTML', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, "Нет новых домашних заданий!")
  else:
    bot.send_message(chat_id, "Ошибка при получении данных, попробуйте позже!")
    bot.send_message(chat_id, error)

def fetch_homeworks(user:User):
  url = hhdev_api['homeworks_url']
  headers = get_headers(user)
  try:
    response = requests.get(url=url, headers=headers)
    homeworks = list()
    if response.status_code == 200:
      homeworks = [
        json_to_homework(json_item) 
        for json_item 
        in response.json().get('data', [])
      ]
      return None, homeworks
    else:
      return f"Error fetching data from {url}: {response.status_code}", None
  except Exception as e:
    return f"Exception occurred: {e}", None

def get_reviews_to_do(user:User, homework:Homework):
  return fetch_reviews(user, hhdev_api['reviews_to_do_url'].format(homework_id=homework.id))

def get_my_reviews(user:User, homework:Homework):
  return fetch_reviews(user, hhdev_api['my_reviews_url'].format(homework_id=homework.id))

def fetch_reviews(user:User, url:str):
  headers = get_headers(user)
  try:
    response = requests.get(url=url, headers=headers)
    reviews = list()
    if response.status_code == 200:
      reviews = [
        json_to_review(json_item) 
        for json_item 
        in response.json().get('data', [])
      ]
      return None, reviews
    else:
      return f"Error fetching data from {url}: {response.status_code}", None
  except Exception as e:
    return f"Exception occurred: {e}", None
