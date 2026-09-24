import os
import json
import requests
import re
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Konfiguracja
URL = "https://www.camper.com/pl_PL/men/shoes/peu/camper-peu_path_-K300558-002"
SHEET_ID = os.environ.get("SHEET_ID")
GCP_JSON = os.environ.get("GCP_CREDENTIALS")

def get_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. Próba znalezienia ceny w ustandaryzowanych metadanych e-commerce
    price_tag = soup.find("meta", property="product:price:amount")
    if price_tag:
        return f"{price_tag['content']} zł"
    
    # 2. Alternatywa: szukanie ścisłego wzorca (np. "715 zł", "1 299,00 zł") w tekście
    text = soup.get_text(separator=' ')
    match = re.search(r'(\d[\d\s\xa0.,]*zł)', text)
    if match:
        # Zwracamy czysty wynik pozbawiony sztucznych twardych spacji
        return re.sub(r'\s+', ' ', match.group(1)).strip()
            
    return "Nie znaleziono ceny"

def update_sheet(price):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = json.loads(GCP_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID).sheet1
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    sheet.append_row([date_now, price, URL])
    print(f"Dodano wpis: {date_now} - {price}")

if __name__ == "__main__":
    price = get_price()
    update_sheet(price)
