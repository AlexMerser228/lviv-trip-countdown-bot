import os
from telegram.ext import Application, CommandHandler
from datetime import datetime

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

async def countdown(update, context):
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
    # Вимикаємо JobQueue, щоб уникнути apscheduler
    app = Application.builder().token(os.getenv("BOT_TOKEN")).job_queue(None).build()
    app.add_handler(CommandHandler("time", countdown))
    app.run_polling()

if __name__ == "__main__":
    main()
