import os
import asyncio
from telegram import Bot, Update
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

# Налаштування Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1rVUe1wHurLiq9qNoUHy3FyTI3NXi78IlcpXA3IYlhOw/edit?gid=0#gid=0"

# Ініціалізація Google Sheets
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1

# Змінні для розіграшу
current_winner = None
last_draw_date = None
group_members = set()
ADMIN_USERNAME = "ТвійЮзернейм"  # Заміни на свій Telegram-юзернейм, наприклад, "@Sanya123"

# Функція для додавання витрати в таблицю
def add_expense_to_sheet(amount, sponsor, comment):
    try:
        amount_value = float(amount.strip())
    except ValueError:
        return "Помилка: сума має бути числом (наприклад, '200')"
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    next_row = len(sheet.get_all_values()) + 1
    sheet.update([[current_date, sponsor, amount_value, comment]], f"A{next_row}:D{next_row}")
    return f"Додано: {current_date}, {sponsor}, {amount_value} грн, {comment}"

# Функція для отримання всіх учасників групи
async def update_group_members(bot, chat_id):
    global group_members
    try:
        chat_members = await bot.get_chat_members(chat_id=chat_id)
        group_members.clear()
        for member in chat_members:
            if not member.user.is_bot:  # Виключаємо ботів
                username = member.user.username or member.user.first_name
                group_members.add(username)
        print(f"Оновлено список учасників: {len(group_members)}")
    except Exception as e:
        print(f"Помилка при отриманні учасників: {e}")

# Функція для розіграшу
async def conduct_draw(bot, chat_id):
    global current_winner, last_draw_date, group_members
    if group_members:
        current_winner = random.choice(list(group_members))
        last_draw_date = datetime.now()
        await bot.send_message(
            chat_id=chat_id,
            text=f"Проводиться розіграш локальної вахти підара...\nСьогодні на вахті буде @{current_winner}!"
        )
    else:
        await bot.send_message(chat_id=chat_id, text="Немає учасників для розіграшу!")

# Щоденний розіграш о 9:00
async def schedule_draw(bot, chat_id):
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            await conduct_draw(bot, chat_id)
            await asyncio.sleep(60)  # Чекаємо хвилину, щоб уникнути повторів
        else:
            seconds_to_next_minute = 60 - now.second
            await asyncio.sleep(seconds_to_next_minute)

async def handle_updates(bot):
    global group_members, current_winner
    offset = None
    chat_id = None
    
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    text = update.message.text.strip()
                    chat_id = update.message.chat_id if chat_id is None else chat_id
                    user = update.message.from_user.username or update.message.from_user.first_name

                    # Оновлюємо список учасників при першому повідомленні
                    if not group_members:
                        await update_group_members(bot, chat_id)

                    # Обробка команди "Що там по часу"
                    if text == "Що там по часу":
                        now = datetime.now()
                        delta = END_DATE - now
                        if delta.total_seconds() <= 0:
                            await bot.send_message(chat_id=chat_id, text="<b>⏰ Час вийшов!</b>\nРуки на стіл! 🖐️", parse_mode="HTML")
                        else:
                            days, seconds = delta.days, delta.seconds
                            hours = seconds // 3600
                            minutes = (seconds % 3600) // 60
                            seconds = seconds % 60
                            await bot.send_message(
                                chat_id=chat_id,
                                text=(
                                    "<b>⏳ До прийняття рішення залишилось:</b>\n"
                                    f"<code>{days}</code> <i>днів</i> 🌞\n"
                                    f"<code>{hours}</code> <i>годин</i> ⏰\n"
                                    f"<code>{minutes}</code> <i>хвилин</i> ⏱️\n"
                                    f"<code>{seconds}</code> <i>секунд</i> ⚡"
                                ),
                                parse_mode="HTML"
                            )

                    # Обробка витрат
                    elif text.startswith("Витрата:"):
                        try:
                            parts = text.replace("Витрата:", "").strip().split(", ")
                            if len(parts) == 2:
                                amount, comment = parts
                                sponsor = f"@{user}" if user.startswith("@") else user
                                result = add_expense_to_sheet(amount, sponsor, comment)
                                await bot.send_message(chat_id=chat_id, text=result)
                            else:
                                await bot.send_message(chat_id=chat_id, text="Неправильний формат. Використовуй: Витрата: сума, коментар (наприклад, '200, кава')")
                        except Exception as e:
                            await bot.send_message(chat_id=chat_id, text=f"Помилка: {e}")

                    # Обробка питання "Хто на вахті?"
                    elif text.lower() == "хто на вахті?":
                        if current_winner:
                            await bot.send_message(chat_id=chat_id, text=f"@{current_winner} підар")
                        else:
                            await bot.send_message(chat_id=chat_id, text="Сьогодні ще нікого не обрали. Чекай 9:00 або попроси адміна зробити розіграш!")

                    # Команда для ручного розіграшу (тільки для адміна)
                    elif text == "/draw" and user == ADMIN_USERNAME:
                        await conduct_draw(bot, chat_id)

                offset = update.update_id + 1
            
            # Запускаємо щоденний розіграш, якщо chat_id відомий
            if chat_id and not hasattr(bot, 'draw_scheduled'):
                asyncio.create_task(schedule_draw(bot, chat_id))
                bot.draw_scheduled = True

        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    print("Bot started!")
    await handle_updates(bot)

if __name__ == "__main__":
    asyncio.run(main())
