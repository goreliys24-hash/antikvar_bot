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
    "Ты — антиквар. Рассмотри фото предмета. Если видишь фигурку, статуэтку, украшение – определи материал (кость, дерево, металл, камень). "
    "Ответь кратко и чётко по пунктам, **не придумывай** несуществующих деталей. Если сомневаешься – напиши 'не уверен'.\n"
    "1. Название предмета (конкретно).\n"
    "2. Примерный возраст (век, период).\n"
    "3. Материал и техника изготовления.\n"
    "4. Состояние (сохранность, дефекты).\n"
    "5. Ориентировочная стоимость в рублях.\n"
    "Если не знаешь – так и скажи."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🕵️ Отправь фото старинного предмета – я опишу и оценю.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        bot.reply_to(message, "🔍 Анализирую... Подождите.")

        base64_image = base64.b64encode(downloaded_file).decode('utf-8')

        response = client.chat.completions.create(
            model="openrouter/free",   # <-- универсальный маршрутизатор
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANTIQUE_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=700
        )

        answer = response.choices[0].message.content
        bot.reply_to(message, answer)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.lower() == '/help':
        bot.reply_to(message, "📸 Отправь фото – я опишу и оценю предмет.")
    else:
        bot.reply_to(message, "Пришли мне фото!")

if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Перезапуск через 15 сек: {e}")
            time.sleep(15)
