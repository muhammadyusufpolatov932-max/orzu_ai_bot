import os
import logging
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


SYSTEM_PROMPT = """
Sen Orzu ismli professional AI yordamchisan.

Qoidalar:

- Foydalanuvchi qaysi tilda yozsa, o'sha tilda javob ber.
- Doimo muloyim, aniq va foydali javob ber.
- Bilmagan narsani uydirma qilma.
- Ishonching past bo'lsa, buni ochiq ayt.
- Faktlar, sanalar va tarixiy ma'lumotlarda iloji boricha aniq bo'l.
- Dasturlash, matematika, fan, futbol, texnologiya va kundalik savollarda yordam ber.
- Javobni tartibli yoz.
- Kerak bo'lsa punktlardan foydalan.
- Juda uzun yozma, foydalanuvchi batafsil so'rasa kengroq tushuntir.
- Hazilni tushun, lekin doimo hurmat bilan javob ber.
"""


memory = {}
MAX_HISTORY = 20


def ask_groq(user_id, text):

    if user_id not in memory:
        memory[user_id] = []


    memory[user_id].append({
        "role": "user",
        "content": text
    })


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ] + memory[user_id][-MAX_HISTORY:]


    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.3
        },
        timeout=60,
    )


    response.raise_for_status()

    answer = response.json()["choices"][0]["message"]["content"]


    memory[user_id].append({
        "role": "assistant",
        "content": answer
    })


    memory[user_id] = memory[user_id][-MAX_HISTORY:]


    return answer

def analyze_image(image_url, question):

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4.1-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": question
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        },
        timeout=60,
    )

    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Salom!\n\n"
        "Men Orzu AI botman.\n"
        "🤖 Matn savollariga javob beraman.\n"
        "🖼 Rasm yuborsangiz tahlil qilaman.\n"
        "🌍 Ko‘p tillarda gaplasha olaman."
    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📌 Buyruqlar:\n"
        "/start - Boshlash\n"
        "/help - Yordam\n"
        "/clear - Xotirani tozalash"
    )



async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    memory[update.effective_user.id] = []

    await update.message.reply_text(
        "🗑 Xotira tozalandi."
    )



async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    waiting = await update.message.reply_text(
        "🤖 O‘ylayapman..."
    )

    try:

        answer = ask_groq(
            update.effective_user.id,
            update.message.text
        )

        await waiting.delete()
        await update.message.reply_text(answer)


    except Exception as e:

        await waiting.edit_text(
            f"❌ Xatolik:\n{e}"
        )



async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        await update.message.reply_text(
            "🖼 Rasm tekshirilmoqda..."
        )


        photo = update.message.photo[-1]

        file = await context.bot.get_file(
            photo.file_id
        )


        image_url = file.file_path


        answer = analyze_image(
            image_url,
            "Bu rasmda nima borligini tushuntir."
        )


        await update.message.reply_text(answer)


    except Exception as e:

        await update.message.reply_text(
            f"❌ Rasm xatosi:\n{e}"
        )



def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY topilmadi!")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY topilmadi!")


    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("clear", clear)
    )


    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_handler
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )


    print("✅ Orzu AI ishga tushdi!")

    app.run_polling()


if __name__ == "__main__":
    main()

