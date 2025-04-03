import os
import asyncio
from telegram import Bot, Update
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import json

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
                            days, seconds
