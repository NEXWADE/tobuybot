import os
import requests
from flask import Flask, request, redirect
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

client_id = os.getenv("CLIENT_ID")
redirect_uri = os.getenv("REDIRECT_URI")

@app.route("/")
def home():
    return redirect(f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
                    f"?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}"
                    f"&response_mode=query&scope=offline_access Tasks.ReadWrite User.Read")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "scope": "offline_access Tasks.ReadWrite User.Read",
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    r = requests.post(token_url, data=data)
    if r.status_code == 200:
        with open("tokens.json", "w") as f:
            f.write(r.text)
        return "✅ Успіх! Тепер запусти файл bot.py"
    else:
        return f"❌ Помилка: {r.text}"

if __name__ == "__main__":
    app.run(port=5000)
