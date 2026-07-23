import telebot
import base64
import os
import time
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Не заданы переменные окружения")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

ANTIQUE_PROMPT = (
    "Ты — опытный антиквар. Рассмотри фото внимательно.\n"
    "Ответь по пунктам:\n"
    "1. Название предмета.\n"
    "2. Примерный возраст (век/период).\n"
    "3. Материалы и техника.\n"
    "4. Состояние (сохранность).\n"
    "5. Ориентировочная стоимость в рублях.\n"
    "Если не уверен — напиши 'не могу определить'."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🕵️ Привет! Отправь фото старинного предмета для описания и оценки.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        bot.reply_to(message, "🔍 Анализирую... Подождите.")

        base64_image = base64.b64encode(downloaded_file).decode('utf-8')

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANTIQUE_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=600
        )

        answer = response.choices[0].message.content
        bot.reply_to(message, answer)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.message_handler(content_types=['text'])
def echo_text(message):
    bot.reply_to(message, "Пришли мне фото!")

if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Перезапуск через 15 сек: {e}")
            time.sleep(15)
