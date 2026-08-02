from pyrogram import Client, filters
import requests
import base64
import os

# ============================================
# 🔑 КЛЮЧИ
# ============================================

TOKEN = "8676324805:AAHfJbQ5nYbwI8-ljdo9nfIZlifU9aPjtHg"
GIGACHAT_AUTH_KEY = "MDE5ZmJlYzUtYzA0Mi03ZWY4LWI3ZmYtOWNjYmE0ODZhMWE0OjRmY2Y4NTE4LWUzYzgtNDcyYi1hM2FjLTdkYzJhMThhMzc5Yw=="

# ============================================
# 🤖 НАСТРОЙКА БОТА
# ============================================

app = Client(
    "helper_bot",
    bot_token=TOKEN,
    api_id=6,
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

def ask_giga_with_image(question, image_path, token):
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
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
                        {"type": "text", "text": question},
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
            return result.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа")
        return f"❌ Ошибка: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

# ============================================
# 📨 ОБРАБОТЧИКИ
# ============================================

@app.on_message(filters.command("start"))
async def start(client, message):
    name = message.from_user.first_name
    await message.reply(
        f"🤖 Привет, {name}!\n"
        f"Я Helper — твой личный помощник!\n\n"
        f"📸 Отправь фото — я решу задачу!\n"
        f"💬 Напиши любой вопрос — я отвечу!"
    )

@app.on_message(filters.photo)
async def handle_photo(client, message):
    await message.reply("📸 Анализирую фото через GigaChat...")
    
    token = get_giga_token()
    if not token:
        await message.reply("❌ Не удалось получить токен GigaChat")
        return
    
    file_path = await client.download_media(message.photo)
    
    answer = ask_giga_with_image("Реши задачу на фото. Ответ на русском.", file_path, token)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    await message.reply(f"🧠 {answer}")

@app.on_message(filters.text & ~filters.command("start"))
async def handle_text(client, message):
    await message.reply("🤔 Думаю...")
    
    token = get_giga_token()
    if not token:
        await message.reply("❌ Не удалось получить токен GigaChat")
        return
    
    answer = ask_giga(message.text, token)
    await message.reply(answer)

# ============================================
# 🚀 ЗАПУСК
# ============================================

if __name__ == "__main__":
    os.makedirs('photos', exist_ok=True)
    print("="*50)
    print("🤖 БОТ HELPER ЗАПУЩЕН!")
    print("="*50)
    print("✅ Все ключи установлены")
    print("✅ Бот работает на Render")
    print("="*50)
    app.run()
