import requests
import os
import base64
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

credenciais = f"{CLIENT_ID}:{CLIENT_SECRET}"
credenciais_base64 = base64.b64encode(credenciais.encode()).decode()

headers = {
    "Authorization": f"Basic {credenciais_base64}",
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(
    "https://www.bling.com.br/Api/v3/oauth/token",
    headers=headers,
    data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN}
)

if response.status_code == 200:
    dados = response.json()
    # Salva os tokens novos automaticamente no .env
    set_key(".env", "ACCESS_TOKEN", dados["access_token"])
    set_key(".env", "REFRESH_TOKEN", dados["refresh_token"])
    print("✅ Tokens renovados com sucesso!")
else:
    print("❌ Erro:", response.json())