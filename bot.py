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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

SYSTEM_PROMPT = """
Sen Orzu ismli sun'iy intellektsan.
Har doim foydalanuvchiga muloyim va foydali javob ber.
Foydalanuvchi qaysi tilda yozsa, o'sha tilda javob qaytar.
"""

user_memory = {}
MAX_HISTORY = 10


def ask_groq(user_id, text):
    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(
        {"role": "user", "content": text}
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + user_memory[user_id][-MAX_HISTORY:]

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": messages,
        },
        timeout=60,
    )

    response.raise_for_status()

    answer = response.json()["choices"][0]["message"]["content"]

    user_memory[user_id].append(
        {"role": "assistant", "content": answer}
    )

    user_memory[user_id] = user_memory[user_id][-MAX_HISTORY:]

    return answer
  async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom!\n\n"
        "Men Orzu AI botman.\n"
        "Menga istalgan savolni yozing."
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_memory[update.effective_user.id] = []
    await update.message.reply_text("🗑 Suhbat xotirasi tozalandi.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Buyruqlar:\n"
        "/start - Botni ishga tushirish\n"
        "/clear - Xotirani tozalash\n"
        "/help - Yordam"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = await update.message.reply_text("🤖 O'ylayapman...")

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
      def main():
    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN topilmadi. Render Environment Variables ga qo'shing."
        )

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY topilmadi. Render Environment Variables ga qo'shing."
        )

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
