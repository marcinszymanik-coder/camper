import os
import json
import requests
import re
import smtplib
from email.mime.text import MIMEText
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

# Dane do e-maila
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def get_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Szukanie ceny w metadanych e-commerce
    price_tag = soup.find("meta", property="product:price:amount")
    if price_tag:
        return f"{price_tag['content']} zł"
    
    # Alternatywa: szukanie wzorca ceny w tekście
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
    
    try:
        creds_dict = json.loads(GCP_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        sheet.append_rows(data_rows)
        print("Zapisano dane w Arkuszu Google.")
    except Exception as e:
        print(f"Błąd podczas zapisu do Arkusza Google: {e}")

def send_email(data_rows):
    if not SENDER_EMAIL or not EMAIL_PASSWORD or not RECEIVER_EMAIL:
        print("Brak danych logowania e-mail. Pomijam wysyłanie wiadomości.")
        return

    subject = "Raport cenowy: Buty Camper"
    body = "Cześć,\n\noto aktualne ceny butów z dzisiejszego sprawdzenia:\n\n"
    
    for row in data_rows:
        body += f"- Cena: {row[1]} (Link: {row[2]})\n"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL # Nagłówek maila akceptuje format po przecinku

    # Podział tekstu po przecinku na listę adresów (dla wielu odbiorców)
    receiver_list = [email.strip() for email in RECEIVER_EMAIL.split(',')]

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        
        # Wysłanie wiadomości do listy odbiorców
        server.sendmail(SENDER_EMAIL, receiver_list, msg.as_string())
        server.quit()
        print(f"Wysłano powiadomienie e-mail na adresy: {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"Wystąpił błąd podczas wysyłania e-maila: {e}")

if __name__ == "__main__":
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    results = []
    
    for url in URLS:
        price = get_price(url)
        results.append([date_now, price, url])
        print(f"Pobrano: {price} dla linku {url[-11:]}")
        
    update_sheet(results)
    send_email(results)
