import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    delta = END_DATE - now
    if delta.total_seconds() <= 0:
        await update.message.reply_text("Час вийшов! Руки на стіл!")
    else:
        days, seconds = delta.days, delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        await update.message.reply_text(
            f"До прийняття остаточного рішення залишилось: {days} днів, {hours} годин, {minutes} хвилин, {seconds} секунд"
        )

def main():
    # Створюємо Application
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("time", countdown))
    app.run_polling()

if __name__ == "__main__":
    main()
