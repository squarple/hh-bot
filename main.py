from bot_handlers import bot, start, handle_message

@bot.message_handler(commands=['start'])
def on_start(message):
  start(message)

@bot.message_handler(func=lambda message: True)
def on_message(message):
  handle_message(message)

if __name__ == '__main__':
  bot.polling()
