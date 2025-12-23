# match_logic.py
import json
from database import Database

def notify_match(bot, user_id, teammate_id, db):
    teammate = db.get_profile(teammate_id)
    if not teammate:
        return

    games_text = "Не указаны"
    try:
        games_list = json.loads(teammate.get('main_games', '[]'))
        if isinstance(games_list, list):
            games_text = ", ".join(games_list)
    except:
        pass

    msg = f"""🎉 **У ВАС НОВЫЙ ТИММЕЙТ!**
👤 **Никнейм:** {teammate.get('nickname', 'Не указан')}
🎂 **Возраст:** {teammate.get('age', 'Не указан')}
⚧ **Пол:** {teammate.get('gender', 'Не указан')}
🎮 **Основные игры:** {games_text}
💬 **Обо мне:**
{teammate.get('about', 'Не заполнено')}"""

    if teammate.get('steam_url'):
        msg += f"\n🔗 **Steam:** {teammate.get('steam_url')}"
    if teammate.get('csstats_url'):
        msg += f"\n📊 **Статистика CS2:** {teammate.get('csstats_url')}"

    telegram_username = teammate.get('telegram_username')
    if telegram_username:
        msg += f"\n💬 **Чтобы написать этому игроку, используйте:** @{telegram_username}"
    else:
        msg += f"\n💬 **Чтобы написать этому игроку, перейдите в раздел '👥 Мои тиммейты'**"
    msg += "\nЭтот игрок добавлен в ваш список тиммейтов."

    try:
        bot.send_message(user_id, msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Ошибка уведомления: {e}")