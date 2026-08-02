import asyncio
import logging
import sqlite3
import json
import os
import base64
from datetime import datetime, timedelta
import random
import requests
from cryptography.fernet import Fernet

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import speech_recognition as sr
from pydub import AudioSegment

# ============================================
# 🔑 ВСЕ ТВОИ КЛЮЧИ
# ============================================

TOKEN = "8676324805:AAHfJbQ5nYbwI8-ljdo9nfIZlifU9aPjtHg"
SHAZAM_API_KEY = "8937f67c8cmshbd3264f29d90e1cp1bb54cjsn9edcf12be753"
GIGACHAT_AUTH_KEY = "MDE5ZmJlYzUtYzA0Mi03ZWY4LWI3ZmYtOWNjYmE0ODZhMWE0OjRmY2Y4NTE4LWUzYzgtNDcyYi1hM2FjLTdkYzJhMThhMzc5Yw=="

# ============================================
# 🔐 ШИФРОВАНИЕ ФАЙЛОВ
# ============================================

KEY_FILE = "encryption.key"

def get_encryption_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        return key

ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)

# ============================================
# 📚 ТЕКСТЫ НА РАЗНЫХ ЯЗЫКАХ
# ============================================

TEXTS = {
    'ru': {
        'start': "Приветсвую!, {name}🪷\nЯ твой личный помощник\n\n🌍 Я говорю на русском 🇷🇺, английском 🇬🇧 и испанском 🇪🇸\n\n🏆 Уровень: {level}\n⭐️ XP: {xp}\n🔥 Серия: {streak} дней\n\n👇 Нажми на кнопки внизу, чтобы узнать команды или сменить язык!",
        'help': "📚 **Команды Helper:**\n\n📸 **Фото** — решу задачу (+25 XP)\n🎤 **Голосовое** — распознаю речь\n🎵 **Аудио** — определю песню (+10 XP)\n\n🔹 `Запомни: ...` — запомню факт\n🔹 `найди музыку ...` — найду песню\n🔹 `статистика` — твой профиль\n\n🌍 **Языки:**\nНажми на кнопку 'Языки' внизу, чтобы сменить язык!",
        'language_changed': "✅ Язык изменён на русский!",
        'photo_analyze': "📸 Анализирую фото через GigaChat...",
        'photo_error': "❌ Не удалось обработать фото. Попробуй другое (не более 10 МБ).",
        'listening': "🎤 Слушаю...",
        'not_recognized': "❌ Не распознано",
        'recognized': "🗣 Ты сказал: {text}",
        'done': "✅ {action}! +{bonus} XP! 🏆 Уровень: {level}",
        'memory_saved': "✅ Запомнил! +3 XP! 🏆 Уровень: {level}",
        'music_search': "🔍 Ищу: {query}...",
        'music_found': "✅ Нашёл! 🎵 {title}\n+15 XP! 🏆 Уровень: {level}",
        'music_not_found': "❌ Не нашёл",
        'stats': "📊 **Твой профиль:**\n\n🏆 Уровень: {level}\n⭐️ XP: {xp}\n🔥 Серия: {streak} дней\n📸 Решено по фото: {photos}",
        'no_memory': "📝 Пока ничего не запомнил. Напиши 'Запомни: ...'",
        'memory_list': "🧠 Я помню:\n{facts}",
        'thinking': "🤔 Думаю...",
        'useful_action': "🎯 {praise}\n✅ {action}!\n⭐ +{bonus} XP!\n🏆 Уровень: {level} | 🔥 Серия: {streak} дней",
        'no_useful': "Распознано! Если сделал полезное дело — напиши об этом.",
        'photo_solved': "🧠 {answer}\n\n✅ +{bonus} XP! 🏆 Уровень: {level}",
        'no_token': "❌ Не удалось получить токен GigaChat. Проверь ключ!",
        'error': "❌ Ошибка: {error}",
        'welcome': "🌍 Выбери язык / Choose language / Elige idioma:",
    },
    'en': {
        'start': "Welcome!, {name}🪷\nI'm your personal assistant\n\n🌍 I speak Russian 🇷🇺, English 🇬🇧 and Spanish 🇪🇸\n\n🏆 Level: {level}\n⭐️ XP: {xp}\n🔥 Streak: {streak} days\n\n👇 Click the buttons below to see commands or change language!",
        'help': "📚 **Helper Commands:**\n\n📸 **Photo** — solve problem (+25 XP)\n🎤 **Voice** — recognize speech\n🎵 **Audio** — identify song (+10 XP)\n\n🔹 `Remember: ...` — save fact\n🔹 `find music ...` — find song\n🔹 `stats` — profile\n\n🌍 **Languages:**\nClick 'Languages' button below to change language!",
        'language_changed': "✅ Language changed to English!",
        'photo_analyze': "📸 Analyzing photo through GigaChat...",
        'photo_error': "❌ Failed to process photo. Try another (max 10 MB).",
        'listening': "🎤 Listening...",
        'not_recognized': "❌ Not recognized",
        'recognized': "🗣 You said: {text}",
        'done': "✅ {action}! +{bonus} XP! 🏆 Level: {level}",
        'memory_saved': "✅ Remembered! +3 XP! 🏆 Level: {level}",
        'music_search': "🔍 Searching: {query}...",
        'music_found': "✅ Found! 🎵 {title}\n+15 XP! 🏆 Level: {level}",
        'music_not_found': "❌ Not found",
        'stats': "📊 **Your Profile:**\n\n🏆 Level: {level}\n⭐️ XP: {xp}\n🔥 Streak: {streak} days\n📸 Solved by photo: {photos}",
        'no_memory': "📝 I haven't remembered anything yet. Write 'Remember: ...'",
        'memory_list': "🧠 I remember:\n{facts}",
        'thinking': "🤔 Thinking...",
        'useful_action': "🎯 {praise}\n✅ {action}!\n⭐ +{bonus} XP!\n🏆 Level: {level} | 🔥 Streak: {streak} days",
        'no_useful': "Recognized! If you did something useful — write about it.",
        'photo_solved': "🧠 {answer}\n\n✅ +{bonus} XP! 🏆 Level: {level}",
        'no_token': "❌ Failed to get GigaChat token. Check your key!",
        'error': "❌ Error: {error}",
        'welcome': "🌍 Choose language / Выбери язык / Elige idioma:",
    },
    'es': {
        'start': "¡Bienvenido!, {name}🪷\nSoy tu asistente personal\n\n🌍 Hablo ruso 🇷🇺, inglés 🇬🇧 y español 🇪🇸\n\n🏆 Nivel: {level}\n⭐️ XP: {xp}\n🔥 Racha: {streak} días\n\n👇 ¡Haz clic en los botones de abajo para ver comandos o cambiar idioma!",
        'help': "📚 **Comandos Helper:**\n\n📸 **Foto** — resolver problema (+25 XP)\n🎤 **Voz** — reconocer habla\n🎵 **Audio** — identificar canción (+10 XP)\n\n🔹 `Recordar: ...` — guardar hecho\n🔹 `buscar música ...` — encontrar canción\n🔹 `estadísticas` — perfil\n\n🌍 **Idiomas:**\n¡Haz clic en el botón 'Idiomas' abajo para cambiar el idioma!",
        'language_changed': "✅ ¡Idioma cambiado a español!",
        'photo_analyze': "📸 Analizando foto a través de GigaChat...",
        'photo_error': "❌ No se pudo procesar la foto. Intenta otra (máximo 10 MB).",
        'listening': "🎤 Escuchando...",
        'not_recognized': "❌ No reconocido",
        'recognized': "🗣 Dijiste: {text}",
        'done': "✅ ¡{action}! +{bonus} XP! 🏆 Nivel: {level}",
        'memory_saved': "✅ ¡Recordado! +3 XP! 🏆 Nivel: {level}",
        'music_search': "🔍 Buscando: {query}...",
        'music_found': "✅ ¡Encontrado! 🎵 {title}\n+15 XP! 🏆 Nivel: {level}",
        'music_not_found': "❌ No encontrado",
        'stats': "📊 **Tu Perfil:**\n\n🏆 Nivel: {level}\n⭐️ XP: {xp}\n🔥 Racha: {streak} días\n📸 Resuelto por foto: {photos}",
        'no_memory': "📝 No he recordado nada aún. Escribe 'Recordar: ...'",
        'memory_list': "🧠 Recuerdo:\n{facts}",
        'thinking': "🤔 Pensando...",
        'useful_action': "🎯 {praise}\n✅ ¡{action}!\n⭐ +{bonus} XP!\n🏆 Nivel: {level} | 🔥 Racha: {streak} días",
        'no_useful': "¡Reconocido! Si hiciste algo útil — escríbelo.",
        'photo_solved': "🧠 {answer}\n\n✅ +{bonus} XP! 🏆 Nivel: {level}",
        'no_token': "❌ No se pudo obtener el token de GigaChat. ¡Comprueba tu clave!",
        'error': "❌ Error: {error}",
        'welcome': "🌍 Elige idioma / Choose language / Выбери язык:",
    }
}

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
        else:
            print(f"❌ Ошибка токена: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
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
        else:
            return f"❌ Ошибка GigaChat: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

def ask_giga_with_image(question, image_path, token):
    try:
        file_size = os.path.getsize(image_path) / (1024 * 1024)
        if file_size > 10:
            return "❌ Файл слишком большой! Максимум 10 МБ."
        
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
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
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
        else:
            return f"❌ Ошибка GigaChat: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

# ============================================
# 📋 СПИСОК ПОЛЕЗНЫХ ДЕЛ
# ============================================

USEFUL_ACTIONS = {
    'решил задачу': 20, 'сделал домашку': 15, 'сделал контрольную': 25,
    'выучил слова': 12, 'прочитал главу': 10, 'написал код': 20,
    'сделал проект': 25, 'подготовился к экзамену': 20,
    'написал статью': 20, 'решил пример': 15, 'перевел текст': 12,
    'помыл посуду': 7, 'убрался в комнате': 10, 'вынес мусор': 5,
    'приготовил еду': 12, 'купил продукты': 8, 'полил цветы': 5,
    'погладил одежду': 8, 'починил вещь': 15, 'сделал уборку': 12,
    'позанимался спортом': 15, 'сделал зарядку': 8, 'пробежал': 15,
    'сходил в зал': 18, 'сходил на прогулку': 5, 'выпил воду': 3,
    'поел полезное': 5, 'поспал 8 часов': 8, 'помедитировал': 10,
    'почитал книгу': 12, 'послушал подкаст': 8, 'выучил новое': 15,
    'записал идею': 5, 'составил план': 10, 'подумал о целях': 8,
    'помог другу': 15, 'позвонил родителям': 8, 'поздравил с праздником': 5,
    'сказал доброе слово': 3, 'извинился': 10, 'заплатил долг': 10,
    'сделал сбережение': 15, 'запланировал бюджет': 12,
    'переустановил винду': 30, 'настроил программу': 15,
    'починил технику': 20, 'обновил драйвера': 10, 'настроил систему': 15,
}

# ============================================
# 💾 БАЗА ДАННЫХ
# ============================================

def init_db():
    conn = sqlite3.connect('helper_data.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            memory TEXT DEFAULT '{}',
            language TEXT DEFAULT 'ru',
            last_active TEXT,
            daily_streak INTEGER DEFAULT 0,
            last_daily TEXT,
            photos_solved INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('helper_data.db')
    cur = conn.cursor()
    cur.execute("SELECT xp, level, memory, language, daily_streak, last_daily, photos_solved FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    if result:
        return {
            'xp': result[0], 
            'level': result[1],
            'memory': json.loads(result[2]),
            'language': result[3] or 'ru',
            'daily_streak': result[4] or 0,
            'last_daily': result[5],
            'photos_solved': result[6] or 0
        }
    else:
        cur.execute("INSERT INTO users (user_id, xp, level, memory, language) VALUES (?, 0, 1, '{}', 'ru')", (user_id,))
        conn.commit()
        conn.close()
        return {'xp': 0, 'level': 1, 'memory': {}, 'language': 'ru', 'daily_streak': 0, 'last_daily': None, 'photos_solved': 0}

def update_user(user_id, xp_increment=0, memory_update=None, check_daily=False, language=None):
    conn = sqlite3.connect('helper_data.db')
    cur = conn.cursor()
    user = get_user(user_id)
    new_xp = user['xp'] + xp_increment
    memory = user['memory']
    daily_streak = user['daily_streak']
    photos_solved = user.get('photos_solved', 0)
    lang = user['language']
    
    if language:
        lang = language
    
    if memory_update:
        memory.update(memory_update)
    
    if check_daily and xp_increment > 0:
        today = datetime.now().date().isoformat()
        if user['last_daily'] != today:
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            if user['last_daily'] == yesterday:
                daily_streak += 1
            else:
                daily_streak = 1
            new_xp += daily_streak
            cur.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (today, user_id))
    
    new_level = 1 + (new_xp // 100)
    
    cur.execute(
        "UPDATE users SET xp = ?, level = ?, memory = ?, language = ?, daily_streak = ?, photos_solved = ? WHERE user_id = ?",
        (new_xp, new_level, json.dumps(memory), lang, daily_streak, photos_solved, user_id)
    )
    conn.commit()
    conn.close()
    return new_xp, new_level, daily_streak, lang

# ============================================
# 🎤 РАСПОЗНАВАНИЕ РЕЧИ
# ============================================

async def speech_to_text(file_path):
    try:
        r = sr.Recognizer()
        audio = AudioSegment.from_ogg(file_path)
        wav_path = file_path.replace('.ogg', '.wav')
        audio.export(wav_path, format="wav")
        
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            try:
                return r.recognize_google(audio_data, language="ru-RU")
            except:
                try:
                    return r.recognize_google(audio_data, language="en-US")
                except:
                    return None
    except:
        return None

# ============================================
# 🎵 РАСПОЗНАВАНИЕ МУЗЫКИ
# ============================================

async def recognize_music(file_path):
    try:
        url = "https://shazam.p.rapidapi.com/songs/detect"
        with open(file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            headers = {
                'x-rapidapi-key': SHAZAM_API_KEY,
                'x-rapidapi-host': 'shazam.p.rapidapi.com'
            }
            response = requests.post(url, files=files, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'matches' in data and data['matches']:
                    track = data['matches'][0]
                    return f"🎵 **{track.get('title', 'Неизвестно')}** - {track.get('subtitle', 'Неизвестный исполнитель')}"
            return None
    except:
        return None

# ============================================
# 🎵 ПОИСК МУЗЫКИ
# ============================================

async def download_music(query):
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'music/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if info and info.get('entries'):
                entry = info['entries'][0]
                return ydl.prepare_filename(entry), entry.get('title', 'Неизвестно')
        return None, None
    except:
        return None, None

# ============================================
# 🤖 ОБЩЕНИЕ С GIGACHAT
# ============================================

async def ai_chat(user_id, text, lang):
    token = get_giga_token()
    if not token:
        return TEXTS[lang]['no_token']
    
    user_data = get_user(user_id)
    facts = "\n".join([f"- {v}" for k, v in user_data['memory'].items() if k.startswith('fact_')])
    question = f"Вот информация о пользователе: {facts}\n\nВопрос: {text}" if facts else text
    
    return ask_giga(question, token)

async def solve_photo(user_id, photo_path, caption, lang):
    token = get_giga_token()
    if not token:
        return TEXTS[lang]['no_token']
    
    question = f"Проанализируй фото и реши задачу. Дополнительно: {caption if caption else 'Нет уточнений'}. Ответ на русском языке."
    return ask_giga_with_image(question, photo_path, token)

# ============================================
# 🏆 ОБРАБОТКА XP
# ============================================

def get_xp_bonus(user_id, xp_amount):
    user = get_user(user_id)
    return xp_amount + (1 + user['level'] // 5)

# ============================================
# 📨 ОБРАБОТЧИКИ
# ============================================

def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")
    )
    return keyboard

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def process_language_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = callback_query.data.split('_')[1]
    
    update_user(user_id, language=lang)
    
    await callback_query.answer(TEXTS[lang]['language_changed'])
    
    user = get_user(user_id)
    await callback_query.message.edit_text(
        TEXTS[lang]['start'].format(
            name=callback_query.from_user.first_name,
            level=user['level'],
            xp=user['xp'],
            streak=user['daily_streak']
        )
    )

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    init_db()
    user = get_user(user_id)
    
    await message.reply(
        TEXTS[user['language']]['start'].format(
            name=user_name,
            level=user['level'],
            xp=user['xp'],
            streak=user['daily_streak']
        )
    )

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user['language']
    
    await message.reply(TEXTS[lang]['help'])

@dp.message_handler(commands=['language'])
async def language_command(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user['language']
    
    await message.reply(
        TEXTS[lang]['welcome'],
        reply_markup=get_language_keyboard()
    )

@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    lang = user_data['language']
    
    await message.reply(
        TEXTS[lang]['stats'].format(
            level=user_data['level'],
            xp=user_data['xp'],
            streak=user_data['daily_streak'],
            photos=user_data.get('photos_solved', 0)
        )
    )

@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user['language']
    
    await message.reply(TEXTS[lang]['photo_analyze'])
    
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        
        if file.file_size > 10 * 1024 * 1024:
            await message.reply(TEXTS[lang]['photo_error'])
            return
        
        temp_path = f"photos/temp_{photo.file_id}.jpg"
        encrypted_path = f"photos/{photo.file_id}.jpg.enc"
        
        await bot.download_file(file.file_path, temp_path)
        
        with open(temp_path, 'rb') as f:
            file_data = f.read()
        encrypted_data = cipher.encrypt(file_data)
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        os.remove(temp_path)
        
        decrypted_path = f"photos/dec_{photo.file_id}.jpg"
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = cipher.decrypt(encrypted_data)
        with open(decrypted_path, 'wb') as f:
            f.write(decrypted_data)
        
        answer = await solve_photo(user_id, decrypted_path, message.caption or "", lang)
        
        if os.path.exists(decrypted_path):
            os.remove(decrypted_path)
        
        bonus = get_xp_bonus(user_id, 25)
        new_xp, new_level, streak, _ = update_user(user_id, xp_increment=bonus, check_daily=True)
        
        await message.reply(
            TEXTS[lang]['photo_solved'].format(
                answer=answer[:4000] if len(answer) > 4000 else answer,
                bonus=bonus,
                level=new_level
            )
        )
    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}\n\nПопробуй другое фото или напиши текстом.")

@dp.message_handler(content_types=['voice'])
async def handle_voice(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user['language']
    
    await message.reply(TEXTS[lang]['listening'])
    
    voice = message.voice
    file = await bot.get_file(voice.file_id)
    
    temp_path = f"voices/temp_{voice.file_id}.ogg"
    encrypted_path = f"voices/{voice.file_id}.ogg.enc"
    
    await bot.download_file(file.file_path, temp_path)
    
    with open(temp_path, 'rb') as f:
        file_data = f.read()
    encrypted_data = cipher.encrypt(file_data)
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted_data)
    os.remove(temp_path)
    
    decrypted_path = f"voices/dec_{voice.file_id}.ogg"
    with open(encrypted_path, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = cipher.decrypt(encrypted_data)
    with open(decrypted_path, 'wb') as f:
        f.write(decrypted_data)
    
    text = await speech_to_text(decrypted_path)
    
    if os.path.exists(decrypted_path):
        os.remove(decrypted_path)
    
    if text:
        await message.reply(TEXTS[lang]['recognized'].format(text=text))
        for action, xp in USEFUL_ACTIONS.items():
            if action in text.lower():
                bonus = get_xp_bonus(user_id, xp)
                new_xp, new_level, streak, _ = update_user(user_id, xp_increment=bonus, check_daily=True)
                await message.reply(TEXTS[lang]['done'].format(action=action, bonus=bonus, level=new_level))
                return
        await message.reply(TEXTS[lang]['no_useful'])
    else:
        await message.reply(TEXTS[lang]['not_recognized'])

@dp.message_handler(content_types=['audio'])
async def handle_audio(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user['language']
    
    if message.audio:
        await message.reply("🎵 Определяю песню...")
        
        file = await bot.get_file(message.audio.file_id)
        
        temp_path = f"audios/temp_{message.audio.file_id}.mp3"
        encrypted_path = f"audios/{message.audio.file_id}.mp3.enc"
        
        await bot.download_file(file.file_path, temp_path)
        
        with open(temp_path, 'rb') as f:
            file_data = f.read()
        encrypted_data = cipher.encrypt(file_data)
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        os.remove(temp_path)
        
        decrypted_path = f"audios/dec_{message.audio.file_id}.mp3"
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = cipher.decrypt(encrypted_data)
        with open(decrypted_path, 'wb') as f:
            f.write(decrypted_data)
        
        track = await recognize_music(decrypted_path)
        
        if os.path.exists(decrypted_path):
            os.remove(decrypted_path)
        
        if track:
            new_xp, new_level, streak, _ = update_user(user_id, xp_increment=10, check_daily=True)
            await message.reply(f"{track}\n🎵 +10 XP! 🏆 Уровень: {new_level}")
        else:
            await message.reply(TEXTS[lang]['music_not_found'])

@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user['language']
    text = message.text
    
    if text.lower().startswith("запомни:") or text.lower().startswith("remember:") or text.lower().startswith("recordar:"):
        fact = text[text.find(':')+1:].strip()
        if not fact:
            await message.reply("❌ Напиши что запомнить!")
            return
        update_user(user_id, memory_update={f"fact_{datetime.now().timestamp()}": fact})
        new_xp, new_level, streak, _ = update_user(user_id, xp_increment=3, check_daily=True)
        await message.reply(TEXTS[lang]['memory_saved'].format(level=new_level))
        return
    
    if text.lower().startswith("найди музыку") or text.lower().startswith("find music") or text.lower().startswith("buscar música"):
        query = text[text.find(' '):].strip()
        if not query:
            await message.reply("❌ Напиши что искать!")
            return
        await message.reply(TEXTS[lang]['music_search'].format(query=query))
        file_path, title = await download_music(query)
        if file_path and title:
            try:
                await bot.send_audio(message.chat.id, open(file_path, 'rb'))
                new_xp, new_level, streak, _ = update_user(user_id, xp_increment=15, check_daily=True)
                await message.reply(TEXTS[lang]['music_found'].format(title=title, level=new_level))
            except Exception as e:
                await message.reply(TEXTS[lang]['error'].format(error=str(e)))
        else:
            await message.reply(TEXTS[lang]['