import os
import time
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()

auth_token = os.getenv("TARGET_AUTH_TOKEN")
if not auth_token:
    print("ERROR: Authentication token not found in .env file.")
    exit()

print("="*40)
print("   TARGET STREAM SCRAPER (V2)   ")
print("="*40)

ticker_symbol = input("Enter stock ticker (e.g., BBCA): ").strip().upper() or "BBCA"
days_input = input("Enter number of days to scrape (Default 30): ").strip()
days_back = int(days_input) if days_input.isdigit() else 30

cutoff_date = datetime.now() - timedelta(days=days_back)

base_url_env = os.getenv("TARGET_STREAM_URL")
if not base_url_env:
    print("ERROR: TARGET_STREAM_URL not found in .env")
    exit()

base_url = f"{base_url_env}/{ticker_symbol}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Authorization": auth_token
}

print(f"\n--- STARTING SCRAPER FOR: {ticker_symbol} ---")
print(f"Target Cutoff Date: {cutoff_date.strftime('%Y-%m-%d')}")
print("-" * 30)

all_streams = []
current_cursor = None
max_loops = 50000 
is_finished = False

for i in range(max_loops):
    if is_finished: break

    print(f"Fetching batch {i+1}...", end=" ")

    params = {"category": "STREAM_CATEGORY_ALL", "limit": 20}
    if current_cursor: params["last_stream_id"] = current_cursor

    try:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            data_json = response.json()
            stream_list = data_json.get('data', {}).get('stream', [])
            next_cursor = data_json.get('data', {}).get('pagination', {}).get('next_cursor')
            
            if not stream_list:
                print("[STOP] No more messages.")
                break
                
            batch_count = 0
            last_date_str = ""

            for msg in stream_list:
                try:
                    msg_date = parser.parse(msg.get('created_at')).replace(tzinfo=None)
                except: continue

                if msg_date < cutoff_date:
                    print(f"\n[STOP] Reached cutoff: {msg_date.strftime('%Y-%m-%d')}")
                    is_finished = True
                    break

                sentiment_label = msg.get('news_feed', {}).get('label', 'neutral')
                if not sentiment_label: sentiment_label = 'neutral' 

                target_price_data = msg.get('target_price', [])
                prediction_signal = "none"
                
                if target_price_data:
                    tp_info = target_price_data[0] 
                    last_px = tp_info.get('last_price', 0)
                    target_px = tp_info.get('target_price', 0)
                    
                    if last_px > 0 and target_px > 0:
                        if target_px > last_px:
                            prediction_signal = "bullish_target"
                        elif target_px < last_px:
                            prediction_signal = "bearish_target"

                row = {
                    "stream_id": msg.get('stream_id'),
                    "date": msg_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "username": msg.get('user', {}).get('username'),
                    "content": msg.get('content_original', msg.get('content')), 
                    "sentiment_label": sentiment_label,       
                    "prediction_signal": prediction_signal,   
                    "likes": msg.get('total_likes', 0),
                    "replies": msg.get('total_replies', 0)
                }
                all_streams.append(row)
                batch_count += 1
                last_date_str = msg_date.strftime('%Y-%m-%d')

            print(f"[OK] +{batch_count} msgs. (Last: {last_date_str})")
            
            if next_cursor: current_cursor = next_cursor
            else: break
        else:
            print(f"[FAIL] {response.status_code}")
            break
            
    except Exception as e:
        print(f"[ERROR] {e}")
        break

    time.sleep(random.uniform(1.5, 3))

print("-" * 30)

if all_streams:
    df = pd.DataFrame(all_streams)
    csv_filename = f"stream_{ticker_symbol}_{days_back}days.csv"

    print(f"\n📊 Quick Analysis for {len(df)} messages:")
    print(f"- Bullish Targets Found: {len(df[df['prediction_signal']=='bullish_target'])}")
    print(f"- Bearish Targets Found: {len(df[df['prediction_signal']=='bearish_target'])}")
    
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n✅ SAVED: {csv_filename}")
    except PermissionError:
        print(f"\n⛔ ERROR: File '{csv_filename}' currently running. close it first!")
else:
    print("❌ No data retrieved.")