import requests
import os
import base64
import webbrowser
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Abre o navegador automaticamente
url_auth = f"https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id={CLIENT_ID}&state=123"
webbrowser.open(url_auth)

# Você cola o código aqui
code = input("Cole o código da URL aqui e pressione Enter: ")

# Já troca o código pelo token na hora
credenciais = f"{CLIENT_ID}:{CLIENT_SECRET}"
credenciais_base64 = base64.b64encode(credenciais.encode()).decode()

headers = {
    "Authorization": f"Basic {credenciais_base64}",
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(
    "https://www.bling.com.br/Api/v3/oauth/token",
    headers=headers,
    data={"grant_type": "authorization_code", "code": code}
)

print("Status:", response.status_code)
print("Resposta:", response.json())