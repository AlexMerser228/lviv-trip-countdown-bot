import os
import asyncio
from telegram import Bot
from datetime import datetime

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

async def handle_updates(bot):
    offset = None
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                if update.message and update.message.text == "/time":
                    now = datetime.now()
                    delta = END_DATE - now
                    if delta.total_seconds() <= 0:
                        await bot.send_message(
                            chat_id=update.message.chat_id,
                            text="Час вийшов! Руки на стіл!"
                        )
                    else:
                        days, seconds = delta.days, delta.seconds
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        seconds = seconds % 60
                        await bot.send_message(
                            chat_id=update.message.chat_id,
                            text=f"До прийняття остаточного рішення залишилось: {days} днів, {hours} годин, {minutes} хвилин, {seconds} секунд"
                        )
                offset = update.update_id + 1
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)  # Пауза перед повторною спробою

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    print("Bot started!")
    await handle_updates(bot)

if __name__ == "__main__":
    asyncio.run(main())
