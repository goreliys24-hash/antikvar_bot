import telebot
import base64
import os
import time
import logging
from openai import OpenAI

# === ЧИТАЕМ ТОКЕНЫ ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Не заданы переменные окружения")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# === ПРОМПТ ===
ANTIQUE_PROMPT = (
    "Ты — опытный антиквар. Внимательно рассмотри фото. "
    "Дай ответ строго по пунктам:\n"
    "1. Название предмета.\n"
    "2. Примерный возраст (век или период).\n"
    "3. Материал и техника.\n"
    "4. Состояние (сохранность).\n"
    "5. Предположительная рыночная стоимость в рублях.\n"
    "Если не уверен, напиши 'не могу точно определить'."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🕵️ Привет! Отправь фото старинного предмета — я опишу и оценю.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        bot.reply_to(message, "🔍 Анализирую... Подождите.")

        base64_image = base64.b64encode(downloaded_file).decode('utf-8')

        # === ИСПОЛЬЗУЕМ openrouter/free (самый надёжный) ===
        response = client.chat.completions.create(
           model="google/gemini-2.5-flash-lite:free", ,   # <-- заменили на универсальный
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
        # Теперь ошибка будет видна пользователю
        error_text = f"❌ Ошибка: {str(e)}"
        bot.reply_to(message, error_text)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "🕵️ Привет! Я бот-антиквар.\n"
        "📸 Для точной оценки присылай фото:\n"
        "- при хорошем освещении\n"
        "- с разных ракурсов (если возможно)\n"
        "- добавь в описание, что знаешь о предмете\n\n"
        "Отправь фото, и я опишу и оценю его."
    )
if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Перезапуск через 15 сек: {e}")
            time.sleep(15)
