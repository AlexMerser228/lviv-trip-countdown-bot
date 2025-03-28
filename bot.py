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
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    print(f"Помилка Google Sheets: {e}")
    exit(1)

# Змінні для розіграшу
current_winner = None
last_draw_date = None
group_members = set()
ADMIN_USERNAME = "@Merser123"  # Ваш юзернейм

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
        await bot.send_message(chat_id=chat_id, text="Немає учасників для розіграшу! Додай їх через /addmember")

# Щоденний розіграш о 9:00
async def schedule_draw(bot, chat_id):
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0 and (last_draw_date is None or last_draw_date.date() != now.date()):
            await conduct_draw(bot, chat_id)
            await asyncio.sleep(60)  # Чекаємо хвилину, щоб уникнути повторів
        else:
            await asyncio.sleep(60)  # Перевіряємо щохвилини

# Обробка оновлень
async def handle_updates(bot):
    global group_members, current_winner
    offset = None
    
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            print(f"Отримано оновлень: {len(updates)}")  # Відладка
            for update in updates:
                print(f"Оновлення: {update}")  # Відладка
                if update.message and update.message.text:
                    text = update.message.text.strip()
                    chat_id = update.message.chat_id
                    user = update.message.from_user.username or update.message.from_user.first_name
                    print(f"Chat ID: {chat_id}, Текст: {text}")  # Відладка

                    # Додаємо учасника з кожного повідомлення
                    group_members.add(user)

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

                    # Команда для додавання учасника вручну (тільки для адміна)
                    elif text.startswith("/addmember") and user == ADMIN_USERNAME:
                        try:
                            new_member = text.split(" ", 1)[1].strip()
                            group_members.add(new_member)
                            await bot.send_message(chat_id=chat_id, text=f"Додано учасника: {new_member}")
                        except IndexError:
                            await bot.send_message(chat_id=chat_id, text="Вкажи ім'я або @юзернейм після /addmember")

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
    
    # Отримуємо chat_id першої групи, де бот активний, для розіграшу
    updates = await bot.get_updates(timeout=10)
    chat_id = updates[0].message.chat_id if updates else None
    
    if chat_id:
        # Запускаємо обробку оновлень і щоденний розіграш паралельно
        await asyncio.gather(
            handle_updates(bot),
            schedule_draw(bot, chat_id)
        )
    else:
        print("Не вдалося визначити chat_id. Переконайтесь, що бот доданий до групи!")
        await handle_updates(bot)  # Продовжуємо обробку оновлень

if __name__ == "__main__":
    asyncio.run(main())
