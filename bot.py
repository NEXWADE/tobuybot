import logging
import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from dotenv import load_dotenv

load_dotenv()

# Telegram і Graph налаштування
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4)

# Отримання Graph токена
def get_graph_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Додавання завдання до списку "Купити"
def add_task_to_graph(task_title):
    access_token = get_graph_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Отримуємо ID списку "Купити"
    list_url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    response = requests.get(list_url, headers=headers)
    response.raise_for_status()
    lists = response.json()["value"]
    list_id = next((l["id"] for l in lists if l["displayName"].lower() == "купити"), None)

    if not list_id:
        raise Exception("Список 'Купити' не знайдено.")

    # Створюємо завдання
    task_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
    data = {"title": task_title}
    task_response = requests.post(task_url, headers=headers, json=data)
    task_response.raise_for_status()
    return task_response.json()

# Обробка повідомлення
def handle_message(update: Update, context):
    try:
        task = update.message.text
        add_task_to_graph(task)
        update.message.reply_text(f"✅ Додано до списку 'Купити': {task}")
    except Exception as e:
        logging.error(f"❌ Помилка: {e}")
        update.message.reply_text(f"❌ Сталася помилка: {str(e)}")

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Бот працює 👋"

if __name__ == "__main__":
    bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
