import requests
import asyncio
import re
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, CallbackContext, Application, MessageHandler, filters, Dispatcher
import os

TOKEN = os.getenv("BOT_TOKEN")  # Utilisation des variables d'environnement
APP_URL = os.getenv("APP_URL")  # L'URL Railway (à ajouter après le 1er déploiement)

CHANNEL_ID = -1002345807441  
GROUP_ID = -1002330333384  

WELCOME_MESSAGE = """
📢 **Welcome to our group!** / **¡Bienvenido a nuestro grupo!**

I post **manhwas in English and Spanish**. / Publico **manhwas en inglés y español**.

⚠️ **Check the language before downloading!** / ⚠️ **¡Verifica el idioma antes de descargar!**

🔍 **Click on the tags** to find chapters faster. / 🔍 **Haz clic en las etiquetas** para encontrar los capítulos más rápido.

👍 **Like to support me!** / 👍 **¡Dale me gusta para apoyarme!**
"""

bot = Bot(token=TOKEN)
app = Flask(__name__)
dp = Dispatcher(bot, None, workers=0)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    dp.process_update(update)
    return "OK", 200

def get_last_chapter_link():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url).json()
    if "result" in response:
        for message in reversed(response["result"]):
            if "message" in message and "text" in message["message"]:
                last_message = message["message"]["text"]
                if "http" in last_message:
                    return last_message
    return "Aucun lien trouvé. / Ningún enlace encontrado."

async def chapitre(update: Update, context: CallbackContext) -> None:
    last_chapter = get_last_chapter_link()
    message = f"📖 **Last available chapter:** / **Último capítulo disponible:**\n{last_chapter}"
    await update.message.reply_text(message, parse_mode="Markdown")

async def welcome_message(update: Update, context: CallbackContext) -> None:
    welcome_msg = await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")
    await asyncio.sleep(600)
    await welcome_msg.delete()

def get_channel_updates():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url).json()
    if "result" in response:
        today = datetime.now().date()
        chapters_list = []
        for message in reversed(response["result"]):
            if "message" in message and "text" in message["message"]:
                text = message["message"]["text"]
                date_message = datetime.fromtimestamp(message["message"]["date"]).date()
                if date_message == today:
                    match = re.search(r"Name:\s*(.*?)\s*Language:\s*(.*?)\s*Chapters:\s*(\d+)", text)
                    if match:
                        chapters_list.append({
                            "name": match.group(1),
                            "language": match.group(2),
                            "chapters": match.group(3),
                        })
        return chapters_list
    return []

async def send_daily_summary(time_label, time_label_es):
    chapters = get_channel_updates()
    if not chapters:
        message = f"📢 **No chapters were uploaded this {time_label}.** / **No se subieron capítulos este {time_label_es}.**"
    else:
        message = f"📅 **Chapters uploaded this {time_label}:** / **Capítulos subidos este {time_label_es}:**\n\n"
        for i, chapter in enumerate(chapters, 1):
            message += f"📌 {i}. {chapter['name']} chapters {chapter['chapters']} ({chapter['language']})\n"
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")

def setup():
    dp.add_handler(CommandHandler("chapitre", chapitre))
    dp.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))

    # Configurer Webhook
    bot.delete_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

setup()

if __name__ == "__main__":
    app.run(port=5000)
