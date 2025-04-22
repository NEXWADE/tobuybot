
import os
import json
import logging
import msal
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Telegram Token
TELEGRAM_TOKEN = "7290625782:AAHCUfq-Whva1tMQz_K_BiIuVuV76Nq-YA8"

# Microsoft Graph config
CLIENT_ID = "371faded-c039-4f6e-9c40-b27b0d494226"
CLIENT_SECRET = "CGY8Q~-tvqxjjQQjYscrY66gu_ay0wdNrC8TXdeK"
TENANT_ID = "62fdf1b9-4d46-455a-b861-3f055235b05c"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Tasks.ReadWrite", "offline_access"]

# Token cache file
TOKEN_FILE = "tokens.json"

def load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_FILE):
        cache.deserialize(open(TOKEN_FILE, "r").read())
    return cache

def save_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_FILE, "w") as f:
            f.write(cache.serialize())

def get_access_token():
    cache = load_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    else:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise Exception("Failed to create device flow")
        print(f"Go to {flow['verification_uri']} and enter code {flow['user_code']}")
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        save_cache(cache)
        return result["access_token"]
    else:
        raise Exception(f"Auth failed: {result.get('error_description')}")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_email = "glibkovalenko@outlook.com"
    list_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/todo/lists"
    task_url_template = "https://graph.microsoft.com/v1.0/users/{}/todo/lists/{}/tasks"

    access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    list_resp = requests.get(list_url, headers=headers)
    if list_resp.status_code != 200:
        await update.message.reply_text(f"❌ Список не отримано: {list_resp.text}")
        return

    todo_lists = list_resp.json().get("value", [])
    if not todo_lists:
        await update.message.reply_text("❌ Список завдань не знайдено.")
        return

    default_list_id = todo_lists[0]["id"]
    task_url = task_url_template.format(user_email, default_list_id)
    payload = {"title": text}

    task_resp = requests.post(task_url, headers=headers, json=payload)
    if task_resp.status_code == 201:
        await update.message.reply_text("✅ Завдання додано!")
    else:
        await update.message.reply_text(f"❌ Помилка додавання: {task_resp.text}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
