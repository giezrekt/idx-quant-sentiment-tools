import os
import time
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

auth_token = os.getenv("TARGET_AUTH_TOKEN")
if not auth_token:
    print("ERROR: Authentication token not found in .env file.")
    exit()

base_url_env = os.getenv("TARGET_PRICE_URL")
if not base_url_env:
    print("ERROR: TARGET_PRICE_URL not found in .env file.")
    exit()

print("="*40)
print("   TARGET PRICES SCRAPER   ")
print("="*40)

ticker_symbol = input("Enter stock ticker (e.g., BBCA): ").strip().upper() or "BBCA"

end_date_obj = datetime.now()
start_date_obj = end_date_obj - timedelta(days=365)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Authorization": auth_token
}

print(f"--- STARTING SCRAPER FOR: {ticker_symbol} ---")
print(f"Target Period: {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}")

all_price_data = []
curr_date = start_date_obj

target_url = f"{base_url_env}/{ticker_symbol}"

while curr_date < end_date_obj:
    batch_end = min(curr_date + timedelta(days=30), end_date_obj)
    
    start_str = curr_date.strftime("%Y-%m-%d")
    end_str = batch_end.strftime("%Y-%m-%d")
    
    print(f"Fetching batch: {start_str} to {end_str}...", end=" ")
    
    params = {
        "period": "HS_PERIOD_DAILY",
        "start_date": start_str,
        "end_date": end_str,
        "limit": 50,
        "page": 1
    }
    
    try:
        response = requests.get(target_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data_json = response.json()
            batch_result = data_json.get('data', {}).get('result', [])
            
            if batch_result:
                all_price_data.extend(batch_result)
                print(f"[OK] Retrieved {len(batch_result)} records.")
            else:
                print("[WARNING] Result empty.")
                
        else:
            print(f"[FAILED] Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

    time.sleep(random.uniform(1, 3)) 
    curr_date = batch_end

print("-" * 30)

if all_price_data:
    df = pd.DataFrame(all_price_data)
    
    if not df.empty and 'date' in df.columns:
        df = df.drop_duplicates(subset=['date']).sort_values('date', ascending=False)
    
    csv_filename = f"prices_{ticker_symbol}.csv"
    
    try:
        df.to_csv(csv_filename, index=False)
        print(f"SUCCESS! Total clean data: {len(df)} rows.")
        print(f"Data saved to file: '{csv_filename}'")
        print("\nFirst 5 rows preview:")
        print(df.head())
    except PermissionError:
         print(f"[ERROR] Could not save file. Close '{csv_filename}' first!")
else:
    print("FAILED. No data retrieved.")