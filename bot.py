import os
import json
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters
from msal import ConfidentialClientApplication

# Telegram bot token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7290625782:AAHCUfq-Whva1tMQz_K_BiIuVuV76Nq-YA8")

# Microsoft credentials
CLIENT_ID = "371faded-c039-4f6e-9c40-b27b0d494226"
CLIENT_SECRET = "CGY8Q~-tvqxjjQQjYscrY66gu_ay0wdNrC8TXdeK"
TENANT_ID = "62fdf1b9-4d46-455a-b861-3f055235b05c"
SCOPES = ["https://graph.microsoft.com/.default"]

# Target user
TARGET_EMAIL = "glibkovalenko@outlook.com"
TODO_LIST_NAME = "Купити"

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, update_queue=None)


def get_graph_token():
    app = ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    result = app.acquire_token_silent(SCOPES, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)
    return result.get("access_token")


def get_list_id(token, email, list_name):
    url = f"https://graph.microsoft.com/v1.0/users/{email}/todo/lists"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for item in response.json().get("value", []):
            if item["displayName"] == list_name:
                return item["id"]
    return None


def add_task_to_list(token, email, list_id, task_title):
    url = f"https://graph.microsoft.com/v1.0/users/{email}/todo/lists/{list_id}/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": task_title
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 201


def handle_message(update: Update, context):
    message = update.message.text
    token = get_graph_token()

    if not token:
        update.message.reply_text("❌ Не вдалося отримати токен Microsoft Graph.")
        return

    list_id = get_list_id(token, TARGET_EMAIL, TODO_LIST_NAME)
    if not list_id:
        update.message.reply_text("❌ Не знайдено список у Microsoft To Do.")
        return

    if add_task_to_list(token, TARGET_EMAIL, list_id, message):
        update.message.reply_text("✅ Додано до списку!")
    else:
        update.message.reply_text("❌ Помилка при додаванні задачі.")


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200


@app.route("/", methods=["GET"])
def index():
    return "бот працює", 200


def main():
    bot.delete_webhook()
    webhook_url = f"https://tobuybot.onrender.com/{TELEGRAM_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"Webhook встановлено на {webhook_url}")


dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    main()
