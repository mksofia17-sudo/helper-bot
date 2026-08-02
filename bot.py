import asyncio
import logging
import sqlite3
import json
import os
import base64
from datetime import datetime, timedelta
import random
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# 🔑 ВСЕ ТВОИ КЛЮЧИ
# ============================================

TOKEN = "8676324805:AAHfJbQ5nYbwI8-ljdo9nfIZlifU9aPjtHg"
SHAZAM_API_KEY = "8937f67c8cmshbd3264f29d90e1cp1bb54cjsn9edcf12be753"
GIGACHAT_AUTH_KEY = "MDE5ZmJlYzUtYzA0Mi03ZWY4LWI3ZmYtOWNjYmE0ODZhMWE0OjRmY2Y4NTE4LWUzYzgtNDcyYi1hM2FjLTdkYzJhMThhMzc5Yw=="

# ============================================
# 🤖 НАСТРОЙКА БОТА
# ============================================

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

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

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_name = message.from_user.first_name
    await message.reply(
        f"🤖 Привет, {user_name}!\n"
        f"Я Helper — твой личный помощник!\n\n"
        f"📸 Отправь фото — я решу задачу!\n"
        f"💬 Напиши любой вопрос — я отвечу!"
    )

@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    await message.reply("📸 Анализирую фото через GigaChat...")
    
    token = get_giga_token()
    if not token:
        await message.reply("❌ Не удалось получить токен GigaChat")
        return
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = f"photos/{photo.file_id}.jpg"
    await bot.download_file(file.file_path, file_path)
    
    answer = ask_giga_with_image("Реши задачу на фото. Ответ на русском.", file_path, token)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    await message.reply(f"🧠 {answer}")

@dp.message_handler()
async def handle_text(message: types.Message):
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

if __name__ == '__main__':
    os.makedirs('photos', exist_ok=True)
    os.makedirs('voices', exist_ok=True)
    os.makedirs('audios', exist_ok=True)
    os.makedirs('music', exist_ok=True)
    
    print("="*50)
    print("🤖 БОТ HELPER ЗАПУЩЕН!")
    print("="*50)
    print("✅ Все ключи установлены")
    print("✅ Бот работает на Render")
    print("="*50)
    
    executor.start_polling(dp, skip_updates=True)
