import os
import json
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

def get_token():
    with open("tokens.json", "r") as f:
        return json.loads(f.read())["access_token"]

def get_list_id(token, name):
    url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    for l in r.json().get("value", []):
        if l["displayName"] == name:
            return l["id"]
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

def handle(update: Update, context):
    token = get_token()
    list_id = get_list_id(token, "Купити")
    r = create_task(token, list_id, update.message.text)
    if r.status_code == 201:
        update.message.reply_text("✅ Додано в список 'Купити'")
    else:
        update.message.reply_text(f"❌ Помилка: {r.text}")

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))

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
