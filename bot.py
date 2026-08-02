from pyrogram import Client, filters
import requests
import base64
import os
import json
from datetime import datetime

# ============================================
# 🔑 ВСЕ ТВОИ КЛЮЧИ
# ============================================

TOKEN = "8676324805:AAHfJbQ5nYbwI8-ljdo9nfIZlifU9aPjtHg"
SHAZAM_API_KEY = "8937f67c8cmshbd3264f29d90e1cp1bb54cjsn9edcf12be753"
GIGACHAT_AUTH_KEY = "MDE5ZmJlYzUtYzA0Mi03ZWY4LWI3ZmYtOWNjYmE0ODZhMWE0OjRmY2Y4NTE4LWUzYzgtNDcyYi1hM2FjLTdkYzJhMThhMzc5Yw=="

# ============================================
# 🤖 НАСТРОЙКА БОТА
# ============================================

app = Client(
    "helper_bot",
    bot_token=TOKEN,
    api_id=6,  # для ботов можно использовать 6
    api_hash=""
)

# ============================================
# 🌐 ФУНКЦИИ ДЛЯ GIGACHAT
# ============================================

def get_giga_token():
    try:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": "123e4567-e89b-12d3-a456-426614174000",
            "Authorization": f"Basic {GIGACHAT_AUTH_KEY}"
        }
        data = {"scope": "GIGACHAT_API_PERS"}
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except:
        return None

def ask_giga(question, token):
    try:
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=90)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа")
        return f"❌ Ошибка: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

# ============================================
# 📨 ОБРАБОТЧИКИ СООБЩЕНИЙ
# ============================================

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🤖 Привет! Я Helper. Отправь фото — решу задачу!")

@app.on_message(filters.photo)
async def handle_photo(client, message):
    await message.reply("📸 Получил фото! Анализирую...")
    
    token = get_giga_token()
    if not token:
        await message.reply("❌ Ошибка токена GigaChat")
        return
    
    # Скачиваем фото
    file_path = await client.download_media(message.photo)
    
    with open(file_path, "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    os.remove(file_path)
    
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Реши задачу на фото. Ответ на русском."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    response = requests.post(url, headers=headers, json=data, verify=False, timeout=120)
    if response.status_code == 200:
        result = response.json()
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа")
        await message.reply(f"🧠 {answer}")
    else:
        await message.reply(f"❌ Ошибка GigaChat: {response.status_code}")

# ============================================
# 🚀 ЗАПУСК
# ============================================

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    app.run()
