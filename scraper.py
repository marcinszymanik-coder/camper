import os
import json
import requests
import re
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Konfiguracja - lista linków do sprawdzenia
URLS = [
    "https://www.camper.com/pl_PL/men/shoes/peu/camper-peu_path_-K300558-005",
    "https://www.camper.com/pl_PL/men/shoes/peu/camper-peu_path_-K300558-004",
    "https://www.camper.com/pl_PL/men/shoes/peu/camper-peu_path_-K300558-002"
]
SHEET_ID = os.environ.get("SHEET_ID")
GCP_JSON = os.environ.get("GCP_CREDENTIALS")

def get_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Szukanie ceny w metadanych
    price_tag = soup.find("meta", property="product:price:amount")
    if price_tag:
        return f"{price_tag['content']} zł"
    
    # Alternatywa w razie braku metadanych (regex)
    text = soup.get_text(separator=' ')
    match = re.search(r'(\d[\d\s\xa0.,]*zł)', text)
    if match:
        return re.sub(r'\s+', ' ', match.group(1)).strip()
            
    return "Nie znaleziono ceny"

def update_sheet(data_rows):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = json.loads(GCP_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Otwarcie arkusza i dodanie wielu wierszy na raz
    sheet = client.open_by_key(SHEET_ID).sheet1
    sheet.append_rows(data_rows)
    
    for row in data_rows:
        print(f"Dodano wpis: {row[0]} - {row[1]} dla linku {row[2][-11:]}")

if __name__ == "__main__":
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    results = []
    
    # Pętla pobierająca ceny dla każdego linku z listy
    for url in URLS:
        price = get_price(url)
        results.append([date_now, price, url])
        
    update_sheet(results)
