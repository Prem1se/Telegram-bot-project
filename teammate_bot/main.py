# main.py
from config import TOKEN
import telebot
from database import Database
from handlers import register_handlers

bot = telebot.TeleBot(TOKEN)
db = Database()

register_handlers(bot, db)

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 БОТ ЗАПУЩЕН")
    print("=" * 50)
    bot.polling(none_stop=True)