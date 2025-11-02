import os
import requests

token = os.getenv("TOKEN")

print("Проверяем токен Telegram бота...")

try:
    resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    data = resp.json()
    if data.get("ok"):
        user = data["result"]
        print(f"✅ Токен валиден! Бот: @{user.get('username')}")
    else:
        print(f"❌ Токен недействителен: {data}")
except Exception as e:
    print(f"❌ Ошибка проверки токена: {e}")
