import requests
import pandas as pd
from datetime import datetime
import os
import time
import json

CACHE_PATH = os.path.join("data", "cache.json")
CSV_PATH = os.path.join("data", "crypto_data.csv")


def fetch_crypto_data():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1,
        'sparkline': False,
        'price_change_percentage': '24h,7d'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("❌ API Error:", e)
        return pd.DataFrame()

    crypto_data = []
    for coin in data:
        crypto_data.append({
            'Name': coin['name'],
            'Symbol': coin['symbol'].upper(),
            'Price (USD)': coin['current_price'],
            '24h Change (%)': coin['price_change_percentage_24h'],
            '7d Change (%)': coin.get('price_change_percentage_7d_in_currency', 0),
            'Market Cap': coin['market_cap'],
            '24h Volume': coin['total_volume'],
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    return pd.DataFrame(crypto_data)


def save_to_cache(df):
    os.makedirs("data", exist_ok=True)
    try:
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        print(f"💾 Cache updated at {CACHE_PATH}")
    except Exception as e:
        print("❌ Error saving cache:", e)


def save_to_csv(df):
    os.makedirs("data", exist_ok=True)
    try:
        old_df = pd.read_csv(CSV_PATH)
        combined_df = pd.concat([old_df, df], ignore_index=True)
    except FileNotFoundError:
        combined_df = df
    combined_df.to_csv(CSV_PATH, index=False)
    print(f"✅ CSV saved to {CSV_PATH}")


def run_background_scraper(interval=60):
    print("🚀 Starting background scraper... Press Ctrl+C to stop.")
    try:
        while True:
            df = fetch_crypto_data()
            if not df.empty:
                save_to_cache(df)
                save_to_csv(df)
            else:
                print("⚠️ Empty data received, skipping save.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("👋 Scraper stopped by user.")


if __name__ == "__main__":
    run_background_scraper(interval=60)
