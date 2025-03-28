import os
import asyncio
from telegram import Bot, Update
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

# Налаштування Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1rVUe1wHurLiq9qNoUHy3FyTI3NXi78IlcpXA3IYlhOw/edit?gid=0#gid=0"

# Ініціалізація Google Sheets
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    print(f"Помилка Google Sheets: {e}")
    exit(1)

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

# Обробка оновлень
async def handle_updates(bot):
    offset = None
    
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    text = update.message.text.strip()
                    chat_id = update.message.chat_id
                    user = update.message.from_user.username or update.message.from_user.first_name

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

                offset = update.update_id + 1

        except Exception as e:
            print(f"Помилка: {e}")
            await asyncio.sleep(5)

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Помилка: BOT_TOKEN не заданий!")
        return
    bot = Bot(token=token)
    print("Бот запущений!")
    
    # Запускаємо обробку оновлень
    await handle_updates(bot)

if __name__ == "__main__":
    asyncio.run(main())
