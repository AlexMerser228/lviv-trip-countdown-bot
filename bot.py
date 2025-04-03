import os
import asyncio
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Кінцева дата: 14 квітня 2025, 23:59:59
END_DATE = datetime(2025, 4, 14, 23, 59, 59)

# Налаштування Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1rVUe1wHurLiq9qNoUHy3FyTI3NXi78IlcpXA3IYlhOw/edit?gid=0#gid=0"

# Ініціалізація Google Sheets
try:
    # Отримуємо credentials.json із змінної середовища
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS не заданий у змінних середовища!")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
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

# Обробник команди "Що там по часу"
async def time_left(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        now = datetime.now()
        delta = END_DATE - now
        if delta.total_seconds() <= 0:
            await update.message.reply_text("<b>⏰ Час вийшов!</b>\nРуки на стіл! 🖐️", parse_mode="HTML")
        else:
            days, seconds = delta.days, delta.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            await update.message.reply_text(
                "<b>⏳ До прийняття рішення залишилось:</b>\n"
                f"<code>{days}</code> <i>днів</i> 🌞\n"
                f"<code>{hours}</code> <i>годин</i> ⏰\n"
                f"<code>{minutes}</code> <i>хвилин</i> ⏱️\n"
                f"<code>{seconds}</code> <i>секунд</i> ⚡",
                parse_mode="HTML"
            )
    except Exception as e:
        await update.message.reply_text(f"Помилка при обчисленні часу: {e}")

# Обробник для витрат
async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text.startswith("Витрата:"):
        return

    try:
        parts = text.replace("Витрата:", "").strip().split(", ")
        if len(parts) == 2:
            amount, comment = parts
            user = update.message.from_user.username or update.message.from_user.first_name
            sponsor = f"@{user}" if user.startswith("@") else user
            result = add_expense_to_sheet(amount, sponsor, comment)
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("Неправильний формат. Використовуй: Витрата: сума, коментар (наприклад, '200, кава')")
    except Exception as e:
        await update.message.reply_text(f"Помилка: {e}")

def main() -> None:
    # Отримуємо токен із змінної середовища
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Помилка: BOT_TOKEN не заданий!")
        return

    # Створюємо додаток
    application = Application.builder().token(token).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("time", time_left))  # Команда /time для "Що там по часу"
    application.add_handler(MessageHandler(filters.Regex(r'^Що там по часу$'), time_left))
    application.add_handler(MessageHandler(filters.Regex(r'^Витрата:'), handle_expense))

    print("Бот запущений!")

    # Запускаємо бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
