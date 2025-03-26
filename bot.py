import os
from telegram.ext import Updater, CommandHandler
from datetime import datetime

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

def countdown(update, context):
    now = datetime.now()
    delta = END_DATE - now
    if delta.total_seconds() <= 0:
        update.message.reply_text("Час вийшов! Руки на стіл!")
    else:
        days, seconds = delta.days, delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        update.message.reply_text(
            f"До прийняття остаточного рішення залишилось: {days} днів, {hours} годин, {minutes} хвилин, {seconds} секунд"
        )

def main():
    # Використовуємо змінну оточення замість прямого токена
    updater = Updater(os.getenv("7654360166:AAHcIMr_a44DdlI-6IGw7bnD6-PyBt3WqZc"), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("time", countdown))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
