"""
Implementation of echo bot.
"""

import os
import telebot

bot = telebot.TeleBot(os.environ.get("TOKEN"), parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Send info about bot to user."""
    bot.reply_to(message, "I will echo all your messages except help and start")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    """Echo message."""
    bot.reply_to(message, message.text)

bot.infinity_polling()
