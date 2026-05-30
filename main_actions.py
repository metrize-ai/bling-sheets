import requests
import os
import gspread
import base64
import json
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
from nacl import encoding, public

# ── Autenticação Google ────────────────────────────────────────────────────────
def get_sheets_client():
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# ── Atualiza secret no GitHub ──────────────────────────────────────────────────
def atualizar_secret_github(nome, valor):
    pat       = os.environ["PAT_TOKEN"]
    repo      = "metrize-ai/bling-sheets"
    headers   = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Pega a chave pública do repositório
    r = requests.get(f"https://api.github.com/repos/{repo}/actions/secrets/public-key", headers=headers)
    r.raise_for_status()
    key_data   = r.json()
    public_key = public.PublicKey(key_data["key"].encode(), encoding.Base64Encoder())
    sealed     = public.SealedBox(public_key).encrypt(valor.encode(), encoding.Base64Encoder())

    # Atualiza o secret
    requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{nome}",
        headers=headers,
        json={"encrypted_value": sealed.decode(), "key_id": key_data["key_id"]},
    ).raise_for_status()
    print(f"✅ Secret {nome} atualizado no GitHub.")

# ── Renova token Bling ─────────────────────────────────────────────────────────
def refresh_token():
    CLIENT_ID     = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
    REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

    credenciais_base64 = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    response = requests.post(
        "https://www.bling.com.br/Api/v3/oauth/token",
        headers={
            "Authorization": f"Basic {credenciais_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
    )

    if response.status_code == 200:
        dados = response.json()
        os.environ["ACCESS_TOKEN"]  = dados["access_token"]
        os.environ["REFRESH_TOKEN"] = dados["refresh_token"]

        # Salva novos tokens de volta no GitHub automaticamente
        atualizar_secret_github("ACCESS_TOKEN",  dados["access_token"])
        atualizar_secret_github("REFRESH_TOKEN", dados["refresh_token"])
        print("✅ Tokens renovados e salvos no GitHub!")
    else:
        raise Exception(f"Erro ao renovar token: {response.status_code} {response.text}")

# ── Atualiza planilha ──────────────────────────────────────────────────────────
def atualizar_planilha():
    print(f"🔄 Iniciando atualização... {datetime.now().strftime('%H:%M:%S')}")

    refresh_token()

    headers  = {"Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}"}
    response = requests.get("https://api.bling.com.br/Api/v3/produtos?limite=100", headers=headers)
    response.raise_for_status()
    produtos = response.json()["data"]

    client = get_sheets_client()
    sheet  = client.open("📦 Estoque Revendedores").sheet1
    sheet.clear()

    sheet.update(values=[["📦 ESTOQUE REVENDEDORES — ATUALIZADO AUTOMATICAMENTE VIA API BLING"]], range_name="A1")
    sheet.merge_cells("A1:F1")
    sheet.format("A1:F1", {
        "backgroundColor": {"red": 0.07, "green": 0.25, "blue": 0.11},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 13},
        "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE",
    })

    total_produtos = len(produtos)
    estoque_baixo  = sum(1 for p in produtos if p["estoque"]["saldoVirtualTotal"] < 10)
    estoque_medio  = sum(1 for p in produtos if 10 <= p["estoque"]["saldoVirtualTotal"] < 20)
    agora          = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M:%S")

    sheet.update(values=[[
        f"Total: {total_produtos} produtos",
        f"⚠️ Estoque crítico: {estoque_baixo}",
        f"🟡 Estoque baixo: {estoque_medio}",
        "", "", f"Última atualização: {agora}",
    ]], range_name="A2")

    sheet.update(values=[["#", "Nome do Produto", "Código SKU", "Preço (R$)", "Estoque", "Status"]], range_name="A3")
    sheet.format("A3:F3", {
        "backgroundColor": {"red": 0.18, "green": 0.62, "blue": 0.27},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 11},
        "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE",
    })

    linhas = []
    for i, p in enumerate(produtos, 1):
        estoque = p["estoque"]["saldoVirtualTotal"]
        status  = "🔴 CRÍTICO" if estoque < 10 else ("🟡 BAIXO" if estoque < 20 else "🟢 OK")
        linhas.append([i, p["nome"], p["codigo"], p["preco"], estoque, status])

    sheet.update(values=linhas, range_name="A4")

    requests_batch = []
    for i, linha in enumerate(linhas):
        row     = i + 4
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
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)",
            }
        })

    sheet.spreadsheet.batch_update({"requests": requests_batch})
    sheet.columns_auto_resize(0, 5)

    print(f"✅ Planilha atualizada! {total_produtos} produtos | {estoque_baixo} críticos | {estoque_medio} baixos")

if __name__ == "__main__":
    atualizar_planilha()
