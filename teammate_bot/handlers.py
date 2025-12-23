# handlers.py
import json
import re
from telebot import types
from database import Database
from keyboards import *
from steam_utils import get_steamid64_from_url
from match_logic import notify_match

user_selected_games = {}
user_search_sessions = {}

# Обработчики
def register_handlers(bot, db):
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        username = message.from_user.username
        db.save_profile(user_id, telegram_username=username)
        welcome = f"""🎮 Привет, {message.from_user.first_name}!
Я бот для поиска тиммейтов. Все настройки — через меню.
🚀 **Начните с создания анкеты!**"""
        bot.send_message(message.chat.id, welcome, reply_markup=main_menu())
        bot.send_message(
            message.chat.id,
            "⚠️ **ВАЖНО:** Установите @username в Telegram, чтобы другие могли вам писать напрямую.",
            parse_mode='Markdown'
        )

    @bot.message_handler(func=lambda m: m.text == "📄 Моя анкета")
    def show_profile(message):
        user_id = message.from_user.id
        profile = db.get_profile(user_id)
        if not profile or not profile.get('nickname'):
            bot.send_message(message.chat.id, "📭 У вас ещё нет анкеты!", reply_markup=main_menu())
            return

        try:
            games = ", ".join(json.loads(profile.get('main_games', '[]')))
        except:
            games = "Не указаны"

        text = f"""📄 **ВАША АНКЕТА**
👤 **Никнейм:** {profile.get('nickname', 'Не указан')}
🎂 **Возраст:** {profile.get('age', 'Не указан')}
⚧ **Пол:** {profile.get('gender', 'Не указан')}
🔗 **Steam:** {profile.get('steam_url', 'Не указан')}
🎮 **Игры:** {games}
💬 **Обо мне:**
{profile.get('about', 'Не заполнено')}"""

        if profile.get('steamid64'):
            text += f"\n🔢 **SteamID64:** `{profile.get('steamid64')}`"
        if profile.get('csstats_url'):
            text += f"\n📊 **Статистика CS2:** {profile.get('csstats_url')}"
        text += f"\n📅 *Обновлено:* {profile.get('updated_at', '')}"

        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())

    @bot.message_handler(func=lambda m: m.text == "✏️ Редактировать анкету")
    def edit_profile(message):
        bot.send_message(message.chat.id, "✏️ **Выберите поле:**", reply_markup=edit_profile_menu(), parse_mode='Markdown')

    # === Обработка полей ===
    @bot.message_handler(func=lambda m: m.text == "👤 Имя/Ник")
    def ask_nickname(message):
        bot.send_message(message.chat.id, "👤 Введите ваш игровой никнейм:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, lambda m: save_field(m, 'nickname'))

    def save_field(message, field):
        if field == 'nickname':
            db.save_profile(message.from_user.id, nickname=message.text)
            bot.send_message(message.chat.id, f"✅ Никнейм сохранён: *{message.text}*", parse_mode='Markdown', reply_markup=edit_profile_menu())
        elif field == 'age':
            try:
                age = int(message.text)
                if 10 <= age <= 100:
                    db.save_profile(message.from_user.id, age=age)
                    bot.send_message(message.chat.id, f"✅ Возраст: *{age}*", parse_mode='Markdown', reply_markup=edit_profile_menu())
                    return
            except:
                pass
            bot.send_message(message.chat.id, "❌ Возраст от 10 до 100", reply_markup=edit_profile_menu())
        elif field == 'about':
            db.save_profile(message.from_user.id, about=message.text)
            bot.send_message(message.chat.id, "✅ Раздел 'Обо мне' сохранён!", reply_markup=edit_profile_menu())

    @bot.message_handler(func=lambda m: m.text == "🎂 Возраст")
    def ask_age(message):
        bot.send_message(message.chat.id, "🎂 Введите возраст (число):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, lambda m: save_field(m, 'age'))

    @bot.message_handler(func=lambda m: m.text == "💬 Обо мне")
    def ask_about(message):
        bot.send_message(message.chat.id, "💬 Расскажите о себе:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, lambda m: save_field(m, 'about'))

    # === Пол ===
    @bot.message_handler(func=lambda m: m.text == "⚧ Пол")
    def choose_gender(message):
        bot.send_message(message.chat.id, "⚧ Выберите пол:", reply_markup=gender_menu(), parse_mode='Markdown')

    @bot.message_handler(func=lambda m: m.text in ["👨 Мужской", "👩 Женский", "🤷 Не указано"])
    def save_gender(message):
        db.save_profile(message.from_user.id, gender=message.text)
        bot.send_message(message.chat.id, f"✅ Пол: *{message.text}*", parse_mode='Markdown', reply_markup=edit_profile_menu())

    # === Игры ===
    @bot.message_handler(func=lambda m: m.text == "🎮 Основные игры")
    def choose_games(message):
        uid = message.from_user.id
        if uid not in user_selected_games:
            user_selected_games[uid] = []
        current = "\n".join(f"• {g}" for g in user_selected_games[uid]) if user_selected_games[uid] else "ничего"
        bot.send_message(message.chat.id, f"🎮 Текущий выбор:\n{current}\nВыберите игры:", reply_markup=games_menu(), parse_mode='Markdown')

    @bot.message_handler(func=lambda m: m.text in [
        "🎯 CS2 / CS:GO", "⚔️ Dota 2", "🔫 Valorant", "🏆 League of Legends",
        "⛏️ Minecraft", "👑 Apex Legends", "🦸 Overwatch 2", "🏰 Fortnite",
        "🌍 PUBG", "📱 Mobile Legends"
    ])
    def toggle_game(message):
        uid = message.from_user.id
        if uid not in user_selected_games:
            user_selected_games[uid] = []
        if message.text in user_selected_games[uid]:
            user_selected_games[uid].remove(message.text)
            action = "удалена"
        else:
            user_selected_games[uid].append(message.text)
            action = "добавлена"
        current = "\n".join(f"• {g}" for g in user_selected_games[uid])
        bot.send_message(message.chat.id, f"🎮 **{message.text}** {action}!\nТекущий выбор:\n{current}", reply_markup=games_menu(), parse_mode='Markdown')

    @bot.message_handler(func=lambda m: m.text == "✅ Завершить выбор игр")
    def finish_games(message):
        uid = message.from_user.id
        if uid not in user_selected_games or not user_selected_games[uid]:
            bot.send_message(message.chat.id, "❌ Вы не выбрали игры!", reply_markup=games_menu())
            return
        games_json = json.dumps(user_selected_games[uid])
        db.save_profile(uid, main_games=games_json)

        has_cs2 = any('cs2' in g.lower() or 'cs:go' in g.lower() for g in user_selected_games[uid])
        if has_cs2:
            profile = db.get_profile(uid)
            if profile and profile.get('steamid64'):
                cs_url = f"https://csstats.gg/player/{profile['steamid64']}"
                db.save_profile(uid, csstats_url=cs_url)

        games_list = ", ".join(user_selected_games[uid])
        del user_selected_games[uid]
        bot.send_message(message.chat.id, f"✅ **Игры сохранены:**\n{games_list}", parse_mode='Markdown', reply_markup=edit_profile_menu())

    # === Steam ===
    @bot.message_handler(func=lambda m: m.text == "🔗 Steam профиль")
    def ask_steam(message):
        bot.send_message(message.chat.id, "🔗 Введите ссылку на Steam:\n• https://steamcommunity.com/id/...\n• https://steamcommunity.com/profiles/...", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, save_steam)

    def save_steam(message):
        url = message.text.strip()
        if 'steamcommunity.com' not in url:
            bot.send_message(message.chat.id, "❌ Неверный формат.", reply_markup=edit_profile_menu())
            return
        msg = bot.send_message(message.chat.id, "🔄 Получаю SteamID64...")
        try:
            steamid64 = get_steamid64_from_url(url)
            response = ""
            if steamid64:
                db.save_profile(message.from_user.id, steam_url=url, steamid64=steamid64)
                response = f"✅ Steam профиль успешно сохранён!\n🔗 {url}\n🔢 {steamid64}"
                profile = db.get_profile(message.from_user.id)
                if profile and profile.get('main_games'):
                    try:
                        games = json.loads(profile['main_games'])
                        if any('cs2' in g.lower() or 'cs:go' in g.lower() for g in games):
                            cs_url = f"https://csstats.gg/player/{steamid64}"
                            db.save_profile(message.from_user.id, csstats_url=cs_url)
                            response += f"\n📊 Статистика CS2: {cs_url}"
                    except:
                        pass
            else:
                db.save_profile(message.from_user.id, steam_url=url)
                response = "❌ Не удалось получить SteamID64. Ссылка сохранена."
            bot.delete_message(message.chat.id, msg.message_id)
            bot.send_message(message.chat.id, response, reply_markup=edit_profile_menu())
        except Exception as e:
            bot.delete_message(message.chat.id, msg.message_id)
            db.save_profile(message.from_user.id, steam_url=url)
            bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=edit_profile_menu())

    # === Удаление ===
    @bot.message_handler(func=lambda m: m.text == "🗑️ Удалить анкету")
    def confirm_delete(message):
        bot.send_message(message.chat.id, "⚠️ Удалить анкету? Все данные будут утеряны.", reply_markup=confirm_delete_menu(), parse_mode='Markdown')

    @bot.message_handler(func=lambda m: m.text == "✅ Да, удалить анкету")
    def delete_profile(message):
        if db.delete_user_data(message.from_user.id):
            bot.send_message(message.chat.id, "✅ Анкета удалена!", reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "❌ Ошибка удаления.", reply_markup=main_menu())

    @bot.message_handler(func=lambda m: m.text == "❌ Нет, вернуться в меню")
    def cancel_delete(message):
        bot.send_message(message.chat.id, "↩️ Удаление отменено.", reply_markup=main_menu())

    @bot.message_handler(func=lambda m: m.text == "↩️ Назад в меню")
    def back_to_main(message):
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())

    # === Поиск тиммейтов ===
    def get_available_teammates(uid):
        liked = db.cursor.execute("SELECT to_user_id FROM likes WHERE from_user_id = ?", (uid,)).fetchall()
        exclude = [r[0] for r in liked]
        return db.get_all_profiles_except(uid, exclude)

    def show_teammate(chat_id, uid):
        if uid not in user_search_sessions:
            bot.send_message(chat_id, "❌ Сессия завершена.", reply_markup=main_menu())
            return
        session = user_search_sessions[uid]
        if session['index'] >= len(session['list']):
            bot.send_message(chat_id, "🔍 Больше анкет нет.", reply_markup=main_menu())
            del user_search_sessions[uid]
            return
        tm = session['list'][session['index']]
        try:
            games = ", ".join(json.loads(tm.get('main_games', '[]')))
        except:
            games = "Не указаны"
        text = f"""👤 **АНКЕТА ИГРОКА**
👤 **Никнейм:** {tm.get('nickname', '—')}
🎂 **Возраст:** {tm.get('age', '—')}
⚧ **Пол:** {tm.get('gender', '—')}
🎮 **Игры:** {games}
💬 **Обо мне:**
{tm.get('about', '—')}"""
        if tm.get('steam_url'):
            text += f"\n🔗 **Steam:** {tm['steam_url']}"
        if tm.get('csstats_url'):
            text += f"\n📊 **CS2 Stats:** {tm['csstats_url']}"
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=teammate_action_menu())

    @bot.message_handler(func=lambda m: m.text == "🔍 Найти тиммейтов")
    def search_teammates(message):
        uid = message.from_user.id
        if not db.get_profile(uid) or not db.get_profile(uid).get('nickname'):
            bot.send_message(message.chat.id, "❌ Сначала заполните анкету!", reply_markup=main_menu())
            return
        teammates = get_available_teammates(uid)
        if not teammates:
            bot.send_message(message.chat.id, "😔 Нет анкет для просмотра.", reply_markup=main_menu())
            return
        user_search_sessions[uid] = {'list': teammates, 'index': 0}
        show_teammate(message.chat.id, uid)

    @bot.message_handler(func=lambda m: m.text == "❤️ Лайк" and m.from_user.id in user_search_sessions)
    def like_teammate(message):
        uid = message.from_user.id
        session = user_search_sessions[uid]
        tm = session['list'][session['index']]
        tm_id = tm['user_id']
        if not db.add_like(uid, tm_id):
            bot.send_message(message.chat.id, "❌ Уже лайкали.")
            session['index'] += 1
            show_teammate(message.chat.id, uid)
            return
        if db.is_mutual_like(uid, tm_id):
            db.create_match(uid, tm_id)
            notify_match(bot, uid, tm_id, db)
            notify_match(bot, tm_id, uid, db)
            bot.send_message(message.chat.id, "🎉 **Взаимный лайк!**", parse_mode='Markdown')
        session['index'] += 1
        show_teammate(message.chat.id, uid)

    @bot.message_handler(func=lambda m: m.text == "⏭️ Скип" and m.from_user.id in user_search_sessions)
    def skip_teammate(message):
        uid = message.from_user.id
        user_search_sessions[uid]['index'] += 1
        show_teammate(message.chat.id, uid)

    @bot.message_handler(func=lambda m: m.text == "🏠 Вернуться в меню")
    def back_to_menu(message):
        uid = message.from_user.id
        if uid in user_search_sessions:
            del user_search_sessions[uid]
        bot.send_message(message.chat.id, "↩️ Возвращаемся в меню.", reply_markup=main_menu())

    # === Мои тиммейты ===
    @bot.message_handler(func=lambda m: m.text == "👥 Мои тиммейты")
    def my_teammates(message):
        uid = message.from_user.id
        matches = db.get_matches_for_user(uid)
        if not matches:
            bot.send_message(message.chat.id, "📭 Нет тиммейтов.", reply_markup=main_menu())
            return
        teammates = []
        nicknames = []
        for tm_id, _ in matches:
            p = db.get_profile(tm_id)
            if p:
                teammates.append((tm_id, p))
                nicknames.append(p.get('nickname', 'Игрок'))
        user_search_sessions[uid] = {'teammates': dict(teammates)}
        bot.send_message(message.chat.id, "Выберите тиммейта:", reply_markup=teammate_list_menu(nicknames))

    @bot.message_handler(func=lambda m: m.text.startswith("✉️ Написать ") and m.from_user.id in user_search_sessions)
    def start_direct_message(message):
        uid = message.from_user.id
        nickname = message.text.replace("✉️ Написать ", "")
        teammates = user_search_sessions[uid].get('teammates', {})
        tm_id = None
        for tid, prof in teammates.items():
            if prof.get('nickname') == nickname:
                tm_id = tid
                break
        if not tm_id:
            bot.send_message(message.chat.id, "❌ Не найден.", reply_markup=main_menu())
            return
        teammate = db.get_profile(tm_id)
        if not teammate:
            bot.send_message(message.chat.id, "❌ Профиль удалён.", reply_markup=main_menu())
            return
        try:
            chat = bot.get_chat(tm_id)
            if hasattr(chat, 'username') and chat.username:
                bot.send_message(
                    message.chat.id,
                    f"💬 **Чтобы написать {teammate.get('nickname', 'этому игроку')}, перейдите по ссылке:**\nhttps://t.me/{chat.username}",
                    parse_mode='Markdown',
                    reply_markup=main_menu()
                )
                return
        except Exception as e:
            print(f"Ошибка получения username: {e}")
        # Пересылка через бота
        bot.send_message(
            message.chat.id,
            f"📨 Напишите сообщение для {teammate.get('nickname', 'этого игрока')}.\nОно будет переслано анонимно.",
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove()
        )
        user_search_sessions[uid]['awaiting_message'] = True
        user_search_sessions[uid]['recipient_id'] = tm_id

    @bot.message_handler(func=lambda m: m.from_user.id in user_search_sessions and
                                     user_search_sessions[m.from_user.id].get('awaiting_message'))
    def forward_message(message):
        uid = message.from_user.id
        rec_id = user_search_sessions[uid]['recipient_id']
        sender = db.get_profile(uid)
        recipient = db.get_profile(rec_id)
        games = "Не указаны"
        if sender and sender.get('main_games'):
            try:
                games = ", ".join(json.loads(sender['main_games']))
            except:
                pass
        forward_text = f"""📩 **Новое сообщение от тиммейта**
👤 **Отправитель:** {sender.get('nickname', '—')} (ID: {uid})
🎮 **Игры:** {games}
💬 **Сообщение:**
{message.text}
🔔 Ответьте через раздел '👥 Мои тиммейты'."""
        try:
            bot.send_message(rec_id, forward_text, parse_mode='Markdown')
            bot.send_message(uid, f"✅ Сообщение для {recipient.get('nickname', 'игрока')} отправлено!", parse_mode='Markdown', reply_markup=main_menu())
        except Exception as e:
            bot.send_message(uid, f"❌ Не удалось отправить: {e}", parse_mode='Markdown', reply_markup=main_menu())
        del user_search_sessions[uid]

    @bot.message_handler(func=lambda message: message.text == "❓ Помощь")
    def show_help(message):
        help_text = """
    ❓ **Помощь и инструкции**

    📋 **Как создать анкету:**
    1. Нажмите '✏️ Редактировать анкету'
    2. Заполните все поля по порядку:
       • 👤 Имя/Ник - ваш игровой никнейм
       • 🎂 Возраст - только число от 10 до 100
       • ⚧ Пол - нажмите на нужный вариант
       • 🔗 Steam профиль - ссылка на Steam
       • 🎮 Основные игры - выберите из списка (можно несколько)
       • 💬 Обо мне - расскажите о себе
    3. Нажмите '✅ Сохранить анкету'

    🎮 **Особенности поиска тиммейтов:**
    • Нажмите '🔍 Найти тиммейтов' для просмотра анкет
    • Используйте ❤️ чтобы лайкнуть понравившегося игрока
    • Используйте ⏭️ чтобы пропустить анкету
    • При взаимном лайке вы получите уведомление и игрок добавится в ваши контакты

    👤 **Как связаться с тиммейтом:**
    • Если у игрока есть публичный username (@username), вы перейдете в чат по кнопке
    • Если username отсутствует, вы сможете написать сообщение через этого бота

    🗑️ **Как удалить анкету:**
    • Нажмите кнопку '🗑️ Удалить анкету' в главном меню
    • Подтвердите удаление
    • Все ваши данные будут полностью удалены из базы

    📌 **Советы:**
    • Для Steam ссылки используйте полный URL
    • Можно выбрать несколько игр
    • Обновляйте анкету при изменении предпочтений

    """
        bot.send_message(message.chat.id, help_text, parse_mode='Markdown')