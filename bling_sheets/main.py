import schedule
import time
import requests
import os
import gspread
import base64
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv, set_key
from datetime import datetime

load_dotenv()

def refresh_token():
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
    credenciais_base64 = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    response = requests.post(
        "https://www.bling.com.br/Api/v3/oauth/token",
        headers={"Authorization": f"Basic {credenciais_base64}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN}
    )
    if response.status_code == 200:
        dados = response.json()
        set_key(".env", "ACCESS_TOKEN", dados["access_token"])
        set_key(".env", "REFRESH_TOKEN", dados["refresh_token"])
        load_dotenv(override=True)
        print("✅ Token renovado!")

def atualizar_planilha():
    print(f"🔄 Atualizando... {datetime.now().strftime('%H:%M:%S')}")
    refresh_token()

    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
    response = requests.get("https://api.bling.com.br/Api/v3/produtos?limite=100", headers=headers)
    produtos = response.json()["data"]

    client = gspread.service_account(filename="google_credentials.json")
    sheet = client.open("📦 Estoque Revendedores").sheet1

    sheet.clear()

    # Título principal
    sheet.update(values=[["📦 ESTOQUE REVENDEDORES — ATUALIZADO AUTOMATICAMENTE VIA API BLING"]], range_name="A1")
    sheet.merge_cells("A1:F1")
    sheet.format("A1:F1", {
        "backgroundColor": {"red": 0.07, "green": 0.25, "blue": 0.11},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 13},
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE"
    })

    # Resumo
    total_produtos = len(produtos)
    estoque_baixo = sum(1 for p in produtos if p["estoque"]["saldoVirtualTotal"] < 10)
    estoque_medio = sum(1 for p in produtos if 10 <= p["estoque"]["saldoVirtualTotal"] < 20)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    sheet.update(values=[[
        f"Total: {total_produtos} produtos",
        f"⚠️ Estoque crítico: {estoque_baixo}",
        f"🟡 Estoque baixo: {estoque_medio}",
        "",
        "",
        f"Última atualização: {agora}"
    ]], range_name="A2")
    sheet.format("A2:F2", {
        "backgroundColor": {"red": 0.93, "green": 0.93, "blue": 0.93},
        "textFormat": {"bold": False, "foregroundColor": {"red": 0.3, "green": 0.3, "blue": 0.3}, "fontSize": 10},
        "horizontalAlignment": "LEFT",
        "verticalAlignment": "MIDDLE"
    })
    sheet.format("F2", {
        "textFormat": {"bold": True, "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}, "fontSize": 10},
        "horizontalAlignment": "RIGHT"
    })

    # Cabeçalho da tabela
    sheet.update(values=[["#", "Nome do Produto", "Código SKU", "Preço (R$)", "Estoque", "Status"]], range_name="A3")
    sheet.format("A3:F3", {
        "backgroundColor": {"red": 0.18, "green": 0.62, "blue": 0.27},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 11},
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE"
    })

    # Dados
    linhas = []
    for i, p in enumerate(produtos, 1):
        estoque = p["estoque"]["saldoVirtualTotal"]
        if estoque < 10:
            status = "🔴 CRÍTICO"
        elif estoque < 20:
            status = "🟡 BAIXO"
        else:
            status = "🟢 OK"
        linhas.append([i, p["nome"], p["codigo"], p["preco"], estoque, status])

    sheet.update(values=linhas, range_name="A4")

    # Formatação zebrada em lote
    requests_batch = []
    for i, linha in enumerate(linhas):
        row = i + 4
        estoque = linha[4]
        if estoque < 10:
            bg = {"red": 1.0, "green": 0.88, "blue": 0.88}
        elif estoque < 20:
            bg = {"red": 1.0, "green": 0.97, "blue": 0.82}
        elif i % 2 == 0:
            bg = {"red": 0.95, "green": 0.99, "blue": 0.95}
        else:
            bg = {"red": 1.0, "green": 1.0, "blue": 1.0}
        requests_batch.append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": row-1, "endRowIndex": row, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"backgroundColor": bg, "horizontalAlignment": "CENTER", "textFormat": {"fontSize": 10}}},
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)"
            }
        })

    sheet.spreadsheet.batch_update({"requests": requests_batch})

    # Largura automática das colunas
    sheet.columns_auto_resize(0, 5)
    sheet.spreadsheet.batch_update({"requests": [{"updateSheetProperties": {"properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 3}}, "fields": "gridProperties.frozenRowCount"}}]})

    print(f"✅ Planilha atualizada! {total_produtos} produtos | {estoque_baixo} críticos | {estoque_medio} baixos")

atualizar_planilha()
schedule.every(1).hours.do(atualizar_planilha)

print("⏰ Agendador rodando... (Ctrl+C para parar)")
while True:
    schedule.run_pending()
    time.sleep(60)
