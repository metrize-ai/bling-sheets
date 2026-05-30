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
            headers = {"Authorization": f"Basic {credenciais_base64}", "Content-Type": "application"}




    )
