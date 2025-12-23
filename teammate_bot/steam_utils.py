# steam_utils.py
import re
import requests
from config import STEAM_API_KEY

def get_steamid64_from_url(steam_url):
    match = re.search(r'steamcommunity\.com/profiles/(\d+)', steam_url)
    if match:
        return match.group(1)
    match = re.search(r'steamcommunity\..com/id/([^/?]+)', steam_url)
    if not match:
        return None
    custom_url = match.group(1)
    try:
        api_url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {'key': STEAM_API_KEY, 'vanityurl': custom_url}
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()
        if data['response']['success'] == 1:
            return data['response']['steamid']
    except Exception:
        pass
    return None