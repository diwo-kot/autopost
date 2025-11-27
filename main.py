import telebot
import json
import time
from datetime import datetime
import threading
import os

TOKEN = "8535684697:AAH4aMEsE6P1AqPWGDwBfqhpV7tkVKrEuLA"
CHANNEL_ID = -1003328340709
adminid = [8426624904, 909538208]
bot = telebot.TeleBot(TOKEN)

text = '''
Используй /post для создания поста
'''

tasks_file = "tasks.json"
photos_dir = "photos"
os.makedirs(photos_dir, exist_ok=True)

def load_tasks():
    try:
        with open(tasks_file, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    with open(tasks_file, "w", encoding="utf8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if message.from_user.id in adminid:
        bot.reply_to(message, text)
    else:
        bot.send_message(message.chat.id, '🔴')

@bot.message_handler(commands=["post"])
def ask_text(message):
    if message.from_user.id in adminid:
        bot.send_message(message.chat.id, "Кинь текст поста")
        bot.register_next_step_handler(message, get_text)
    else:
        bot.send_message(message.chat.id, '🔴')

def get_text(message):
    text = message.text
    bot.send_message(message.chat.id, "Пришли фото или напиши 'нет', если фото не нужно")
    bot.register_next_step_handler(message, lambda m: get_photo(m, text))

def get_photo(message, text):
    photo_path = None
    if message.content_type == "photo":
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        photo_path = os.path.join(photos_dir, f"{file_info.file_id}.jpg")
        with open(photo_path, "wb") as f:
            f.write(downloaded_file)
    bot.send_message(message.chat.id, "Кинь дату и время в формате 2025-11-27 20:00")
    bot.register_next_step_handler(message, lambda m: save_task(m, text, photo_path))

def save_task(message, text, photo_path):
    dt = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    ts = int(dt.timestamp())
    tasks = load_tasks()
    tasks.append({
        "chat_id": CHANNEL_ID,
        "text": text,
        "photo": photo_path,
        "timestamp": ts
    })
    save_tasks(tasks)
    bot.send_message(message.chat.id, "Готово. Пост запланирован")

def scheduler():
    while True:
        tasks = load_tasks()
        now = int(time.time())
        new_tasks = []
        for t in tasks:
            if t["timestamp"] <= now:
                if t.get("photo"):
                    with open(t["photo"], "rb") as f:
                        bot.send_photo(t["chat_id"], f, caption=t["text"])
                else:
                    bot.send_message(t["chat_id"], t["text"])
            else:
                new_tasks.append(t)
        save_tasks(new_tasks)
        time.sleep(2)

threading.Thread(target=scheduler, daemon=True).start()
bot.infinity_polling()