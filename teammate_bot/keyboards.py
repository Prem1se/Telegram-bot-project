# keyboards.py
from telebot import types

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📄 Моя анкета"),
        types.KeyboardButton("✏️ Редактировать анкету"),
        types.KeyboardButton("🔍 Найти тиммейтов"),
        types.KeyboardButton("👥 Мои тиммейты"),
        types.KeyboardButton("❓ Помощь"),
        types.KeyboardButton("🗑️ Удалить анкету")
    )
    return markup

def edit_profile_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("👤 Имя/Ник"),
        types.KeyboardButton("🎂 Возраст"),
        types.KeyboardButton("⚧ Пол"),
        types.KeyboardButton("🔗 Steam профиль"),
        types.KeyboardButton("🎮 Основные игры"),
        types.KeyboardButton("💬 Обо мне"),
        types.KeyboardButton("↩️ Назад в меню")
    )
    return markup

def gender_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("👨 Мужской"),
        types.KeyboardButton("👩 Женский"),
        types.KeyboardButton("🤷 Не указано"),
        types.KeyboardButton("↩️ Назад в меню")
    )
    return markup

def games_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    games = [
        "🎯 CS2 / CS:GO", "⚔️ Dota 2",
        "🔫 Valorant", "🏆 League of Legends",
        "⛏️ Minecraft", "👑 Apex Legends",
        "🦸 Overwatch 2", "🏰 Fortnite",
        "🌍 PUBG", "📱 Mobile Legends"
    ]
    buttons = [types.KeyboardButton(g) for g in games]
    buttons.append(types.KeyboardButton("✅ Завершить выбор игр"))
    buttons.append(types.KeyboardButton("↩️ Назад в меню"))
    markup.add(*buttons)
    return markup

def confirm_delete_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("✅ Да, удалить анкету"),
        types.KeyboardButton("❌ Нет, вернуться в меню")
    )
    return markup

def teammate_action_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        types.KeyboardButton("❤️ Лайк"),
        types.KeyboardButton("⏭️ Скип"),
        types.KeyboardButton("🏠 Вернуться в меню")
    )
    return markup

def teammate_list_menu(nicknames):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for nick in nicknames:
        markup.add(types.KeyboardButton(f"✉️ Написать {nick}"))
    markup.add(types.KeyboardButton("↩️ Назад в меню"))
    return markup