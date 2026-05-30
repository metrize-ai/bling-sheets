import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(
    "https://api.bling.com.br/Api/v3/produtos",
    headers=headers
)

dados = response.json()

for produto in dados['data']:
    print(f"Nome: {produto['nome']} | Código: {produto['codigo']} | Preço: {produto['preco']} | Estoque: {produto['estoque']['saldoVirtualTotal']}")