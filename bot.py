import json
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_EMAIL = os.getenv("USER_EMAIL")

def get_token():
    with open("tokens.json", "r") as f:
        return json.loads(f.read())["access_token"]

def get_list_id(token, name):
    url = f"https://graph.microsoft.com/v1.0/me/todo/lists"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    for l in r.json().get("value", []):
        if l["displayName"] == name:
            return l["id"]
    # якщо не існує — створити
    r = requests.post(url, headers=headers, json={"displayName": name})
    return r.json().get("id")

def create_task(token, list_id, title):
    url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"title": title}
    return requests.post(url, headers=headers, json=data)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = get_token()
    list_id = get_list_id(token, "Купити")
    r = create_task(token, list_id, update.message.text)
    if r.status_code == 201:
        await update.message.reply_text("✅ Додано в список 'Купити'")
    else:
        await update.message.reply_text(f"❌ Помилка: {r.text}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
    app.run_polling()

if __name__ == "__main__":
    main()
