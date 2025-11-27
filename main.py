import asyncio
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.filters import Command

TOKEN = "8535684697:AAH4aMEsE6P1AqPWGDwBfqhpV7tkVKrEuLA"
CHANNEL_ID = -1003328340709

bot = Bot(token=TOKEN)
dp = Dispatcher()

tasks_file = "tasks.json"
photos_dir = "photos"
os.makedirs(photos_dir, exist_ok=True)

# Работа с задачами
def load_tasks():
    try:
        with open(tasks_file, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    with open(tasks_file, "w", encoding="utf8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# Словарь для хранения промежуточных данных
user_data = {}

@dp.message(Command("post"))
async def cmd_post(message: types.Message):
    await message.reply("Кинь текст поста")
    user_data[message.from_user.id] = {}
    dp.message.register(get_text, lambda m: m.from_user.id == message.from_user.id)

async def get_text(message: types.Message):
    user_data[message.from_user.id]["text"] = message.text
    await message.reply("Пришли фото или напиши 'нет', если фото не нужно")
    dp.message.register(get_photo, lambda m: m.from_user.id == message.from_user.id)

async def get_photo(message: types.Message):
    photo_path = None
    if message.content_type == ContentType.PHOTO:
        file_info = await bot.get_file(message.photo[-1].file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        photo_path = os.path.join(photos_dir, f"{file_info.file_id}.jpg")
        with open(photo_path, "wb") as f:
            f.write(downloaded_file.read())
    user_data[message.from_user.id]["photo"] = photo_path
    await message.reply("Кинь дату и время в формате 2025-11-27 20:00")
    dp.message.register(get_datetime, lambda m: m.from_user.id == message.from_user.id)

async def get_datetime(message: types.Message):
    dt = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    ts = int(dt.timestamp())
    data = user_data.pop(message.from_user.id)
    tasks = load_tasks()
    tasks.append({
        "chat_id": CHANNEL_ID,
        "text": data["text"],
        "photo": data["photo"],
        "timestamp": ts
    })
    save_tasks(tasks)
    await message.reply("Готово. Пост запланирован")

async def scheduler():
    while True:
        tasks = load_tasks()
        now = int(datetime.now().timestamp())
        new_tasks = []
        for t in tasks:
            if t["timestamp"] <= now:
                if t.get("photo"):
                    with open(t["photo"], "rb") as f:
                        await bot.send_photo(t["chat_id"], f, caption=t["text"])
                else:
                    await bot.send_message(t["chat_id"], t["text"])
            else:
                new_tasks.append(t)
        save_tasks(new_tasks)
        await asyncio.sleep(2)

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())