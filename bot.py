import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Telegram Token
TELEGRAM_TOKEN = "7290625782:AAHCUfq-Whva1tMQz_K_BiIuVuV76Nq-YA8"

# Microsoft credentials
TENANT_ID = "62fdf1b9-4d46-455a-b861-3f055235b05c"
CLIENT_ID = "371faded-c039-4f6e-9c40-b27b0d494226"
CLIENT_SECRET = "CGY8Q~-tvqxjjQQjYscrY66gu_ay0wdNrC8TXdeK"
USER_EMAIL = "glibkovalenko@outlook.com"

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_API = "https://graph.microsoft.com/v1.0"


def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": GRAPH_SCOPE,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_list_id(access_token):
    url = f"{GRAPH_API}/users/{USER_EMAIL}/todo/lists"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    lists = response.json().get("value", [])
    if not lists:
        raise Exception("No To Do lists found.")
    return lists[0]["id"]  # використовуємо перший список


def add_task_to_list(access_token, list_id, task_title):
    url = f"{GRAPH_API}/users/{USER_EMAIL}/todo/lists/{list_id}/tasks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    json_data = {"title": task_title}
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        access_token = get_access_token()
        list_id = get_list_id(access_token)
        task = add_task_to_list(access_token, list_id, user_message)
        await update.message.reply_text(f"✅ Додано до списку: {task['title']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle)
    app.add_handler(handler)

    print("🤖 Bot is running...")
    app.run_polling()
