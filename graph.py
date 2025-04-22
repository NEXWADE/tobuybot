import requests
import os
from dotenv import load_dotenv
import yaml

load_dotenv()

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

client_id = config["microsoft"]["client_id"]
client_secret = os.getenv("MS_CLIENT_SECRET")
tenant_id = config["microsoft"]["tenant_id"]
user_email = config["microsoft"]["user_email"]

def get_access_token():
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

def create_list(token, list_name):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/todo/lists"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"displayName": list_name}
    response = requests.post(url, headers=headers, json=data)
    return response

def get_list_id(token, list_name):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/todo/lists"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    lists = response.json().get("value", [])
    for l in lists:
        if l["displayName"] == list_name:
            return l["id"]
    # створюємо список, якщо не знайдено
    create_response = create_list(token, list_name)
    if create_response.status_code == 201:
        return create_response.json()["id"]
    return None

def create_task(token, list_id, title):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/todo/lists/{list_id}/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"title": title}
    return requests.post(url, headers=headers, json=data)
