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

# ==========================
# TOKENLAR
# ==========================

BOT_TOKEN = "YOUR_BOT_TOKEN"
GROQ_API_KEY = "YOUR_GROQ_API_KEY"

# ==========================
# LOG
# ==========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==========================
# ORZU AI
# ==========================

SYSTEM_PROMPT = """
Sening isming Orzu.

Sen aqlli, muloyim va foydali sun'iy intellekt yordamchisisan.

Qoidalar:
- Foydalanuvchi qaysi tilda yozsa, o'sha tilda javob ber.
- O'zbek, Ingliz, Rus, Turk va boshqa tillarni tushun.
- Javoblar aniq va tushunarli bo'lsin.
- Dasturlash, matematika, fan, tarix va boshqa mavzularda yordam ber.
- Ismingni so'rashsa "Mening ismim Orzu." deb javob ber.
"""

# ==========================
# XOTIRA
# ==========================

memory = {}

MAX_HISTORY = 10
# ==========================
# GROQ AI
# ==========================

def ask_ai(user_id, user_text):
    url = "https://api.groq.com/openai/v1/chat/completions"

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({
        "role": "user",
        "content": user_text
    })

    history = memory[user_id][-MAX_HISTORY:]

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ] + history

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=60
    )

    if response.status_code != 200:
        return f"❌ Xatolik:\n{response.text}"

    result = response.json()

    answer = result["choices"][0]["message"]["content"]

    memory[user_id].append({
        "role": "assistant",
        "content": answer
    })

    memory[user_id] = memory[user_id][-MAX_HISTORY:]

    return answer
    # ==========================
# BUYRUQLAR
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom!\n\n"
        "Men Orzu 🤖\n"
        "Sun'iy intellekt yordamchisiman.\n\n"
        "Menga istalgan tilda savol bering."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Buyruqlar:\n\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam\n"
        "/clear - Xotirani tozalash"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    memory[user_id] = []

    await update.message.reply_text(
        "✅ Suhbat xotirasi tozalandi."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    msg = await update.message.reply_text("⏳ O'ylayapman...")

    try:
        answer = ask_ai(user_id, text)

        await msg.delete()

        await update.message.reply_text(answer)

    except Exception as e:
        await msg.edit_text(f"❌ Xatolik:\n{e}")
        # ==========================
# BOTNI ISHGA TUSHIRISH
# ==========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))

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
