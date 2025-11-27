import asyncio
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.utils import executor

TOKEN = "TOKEN"
CHANNEL_ID = -100123456789

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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

# Старт команды
@dp.message_handler(commands=["post"])
async def cmd_post(message: types.Message):
    await message.reply("Кинь текст поста")
    dp.register_message_handler(get_text, state=None, chat_id=message.chat.id)

async def get_text(message: types.Message):
    text = message.text
    await message.reply("Пришли фото или напиши 'нет', если фото не нужно")
    
    async def get_photo_inner(photo_msg: types.Message):
        photo_path = None
        if photo_msg.content_type == ContentType.PHOTO:
            file_info = await bot.get_file(photo_msg.photo[-1].file_id)
            downloaded_file = await bot.download_file(file_info.file_path)
            photo_path = os.path.join(photos_dir, f"{file_info.file_id}.jpg")
            with open(photo_path, "wb") as f:
                f.write(downloaded_file.read())
        await photo_msg.reply("Кинь дату и время в формате 2025-11-27 20:00")
        
        async def get_datetime(dt_msg: types.Message):
            dt = datetime.strptime(dt_msg.text, "%Y-%m-%d %H:%M")
            ts = int(dt.timestamp())
            tasks = load_tasks()
            tasks.append({
                "chat_id": CHANNEL_ID,
                "text": text,
                "photo": photo_path,
                "timestamp": ts
            })
            save_tasks(tasks)
            await dt_msg.reply("Готово. Пост запланирован")
            dp.unregister_message_handler(get_datetime)
        
        dp.register_message_handler(get_datetime, state=None, chat_id=photo_msg.chat.id)
        dp.unregister_message_handler(get_photo_inner)

    dp.register_message_handler(get_photo_inner, state=None, chat_id=message.chat.id)
    dp.unregister_message_handler(get_text)

# Фоновый автопостинг
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

# Запуск
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp)