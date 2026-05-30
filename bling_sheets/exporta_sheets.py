import gspread
import requests
import os
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# Conecta no Google Sheets
creds = Credentials.from_service_account_file(
    "google_credentials.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(creds)
sheet = client.open("Estoque Revendedores").sheet1

# Busca produtos do Bling
headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
response = requests.get("https://api.bling.com.br/Api/v3/produtos", headers=headers)
produtos = response.json()["data"]

# Escreve cabeçalho
sheet.update("A1", [["Nome", "Código", "Preço", "Estoque"]])

# Escreve produtos
linhas = []
for p in produtos:
    linhas.append([p["nome"], p["codigo"], p["preco"], p["estoque"]["saldoVirtualTotal"]])

sheet.update("A2", linhas)
print("✅ Planilha atualizada com sucesso!")