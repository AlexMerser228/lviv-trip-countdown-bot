import os
import asyncio
from telegram import Bot, Update
from telegram.ext import ContextTypes, CommandHandler
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

async def main():
    # Створюємо бота
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    
    # Налаштовуємо обробник команд
    from telegram.ext import Application
    app = Application.builder().bot(bot).build()
    app.add_handler(CommandHandler("time", countdown))
    
    # Запускаємо polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Тримаємо бота активним
    while True:
        await asyncio.sleep(3600)  # Чекаємо годину перед повторною ітерацією

if __name__ == "__main__":
    asyncio.run(main())
