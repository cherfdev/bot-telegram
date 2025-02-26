import requests
import asyncio
import nest_asyncio
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application, MessageHandler, filters

nest_asyncio.apply()

TOKEN = "7760342602:AAHFjQUvqQDRM6OdCEdf_HAbQhknIu0Vnhw"
CHANNEL_ID = -1002345807441  # Remplace par l'ID numérique de ton canal
GROUP_ID = -1002330333384

WELCOME_MESSAGE = """
📢 **Welcome to our group!** / **¡Bienvenido a nuestro grupo!**

I post **manhwas in English and Spanish**. / Publico **manhwas en inglés y español**.

⚠️ **Check the language before downloading!** / ⚠️ **¡Verifica el idioma antes de descargar!**

🔍 **Click on the tags** to find chapters faster. / 🔍 **Haz clic en las etiquetas** para encontrar los capítulos más rápido.

👍 **Like to support me!** / 👍 **¡Dale me gusta para apoyarme!**
"""

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

async def send_automatic_message(application):
    last_chapter = get_last_chapter_link()
    message = f"📖 **Last available chapter:** / **Último capítulo disponible:**\n{last_chapter}"
    await application.bot.send_message(chat_id=GROUP_ID, text=message, parse_mode="Markdown")

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

async def send_daily_summary(application, time_label, time_label_es):
    chapters = get_channel_updates()
    if not chapters:
        message = f"📢 **No chapters were uploaded this {time_label}.** / **No se subieron capítulos este {time_label_es}.**"
    else:
        message = f"📅 **Chapters uploaded this {time_label}:** / **Capítulos subidos este {time_label_es}:**\n\n"
        for i, chapter in enumerate(chapters, 1):
            message += f"📌 {i}. {chapter['name']} chapters {chapter['chapters']} ({chapter['language']})\n"
    await application.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")

async def schedule_recap(application):
    while True:
        now = datetime.now()
        target_times = [now.replace(hour=12, minute=0, second=0), now.replace(hour=22, minute=0, second=0)]
        for target_time in target_times:
            if now > target_time:
                target_time += timedelta(days=1)
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            if target_time.hour == 12:
                await send_daily_summary(application, "morning", "mañana")
            elif target_time.hour == 22:
                await send_daily_summary(application, "evening", "noche")

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("chapitre", chapitre))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))
    asyncio.create_task(schedule_recap(application))
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
