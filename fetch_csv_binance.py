import pandas as pd
from binance.client import Client
import os
import requests
import csv

client = Client()

def get_top_100_coingecko():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
    }
    headers = {
    "Accept": "application/json",
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        coins = response.json()
        symbols = [coin["symbol"].upper() for coin in coins]
        print(symbols)
        return symbols
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        return []  # Return empty list or consider re-raising the exception

def get_binance_tradable_top_100():
    # Step 1: Get top 50 from CoinGecko
    coingecko_symbols = get_top_100_coingecko() 
    
    # Step 2: Get Binance's tradable pairs
    exchange_info = client.get_exchange_info()
    binance_symbols = {s['symbol'] for s in exchange_info['symbols']}
    
    # Step 3: Filter to only symbols available on Binance
    top_100_tradable = []
    for coin in coingecko_symbols:
        usdt_pair = f"{coin}USDT"  # e.g., "BTCUSDT"
        if usdt_pair in binance_symbols:
            top_100_tradable.append(usdt_pair)
    return top_100_tradable

def fetch_crypto_data(symbol, interval, start_date, end_date="2025-01-01"):
    """
    Fetch historical crypto data from Binance and format for QuantConnect.
    Fixed version: Handles timestamp conversion correctly.
    """
    client = Client()

    filepath = r"F:/QuantConnect/data/crypto/binance/hour"
    filename = f"{filepath}/{symbol}_{interval}_{start_date}_to_{end_date}.csv"
    
    if os.path.exists(filename):
        print(f"File '{filename}' already exists. Exiting function.")
        return

    interval_map = {
        "1m": Client.KLINE_INTERVAL_1MINUTE,
        "1h": Client.KLINE_INTERVAL_1HOUR,
        "1d": Client.KLINE_INTERVAL_1DAY
    }
    binance_interval = interval_map.get(interval, Client.KLINE_INTERVAL_1HOUR)
    
    print(f"Fetching {symbol} {interval} data from {start_date} to {end_date}...")
    
    # Fetch data
    klines = client.get_historical_klines(
        symbol=symbol,
        interval=binance_interval,
        start_str=start_date,
        end_str=end_date
    )
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['time', 'open', 'high', 'low', 'close', 'volume'])

        # Write data rows
        for kline in klines:
          # Convert timestamp from ms to seconds and create datetime
            timestamp_ms = int(kline[0])
            dt = pd.to_datetime(timestamp_ms, unit='ms').strftime('%Y-%m-%dT%H:%M:%SZ')

            writer.writerow([
                dt,        # time in ISO format
                kline[1],  # open
                kline[2],  # high
                kline[3],  # low
                kline[4],  # close
                kline[5],  # volume
        ])
            
    print(f"Data saved to {filename}")
    #print(f"First 5 rows:\n{df.head()}")

if __name__ == "__main__":
    top_100_symbols = get_binance_tradable_top_100()
    print("All symbols are:")
    print(top_100_symbols)
    top_100_symbols = ['BTCUSDT']
    
    for symbol in top_100_symbols:
        total_symbols = len(top_100_symbols)
        sym_ind = top_100_symbols.index(symbol)
        print("Fetching " + symbol + " " +str(sym_ind+1) + " out of " + str(total_symbols) + ".....")
        fetch_crypto_data(symbol,"1h","2015-01-01","2025-06-01")  # Default: BTCUSDT 1h for January 2023

