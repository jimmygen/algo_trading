import ccxt
import pandas as pd
import pytz # For timezone handling
import time

def setbroker(broker_id):
    if broker_id == 'deribit':
        broker = ccxt.deribit({
            'enableRateLimit': True,
            'urls': {
                'api': {
                    'public': 'https://test.deribit.com/api/v2/',
                    'private': 'https://test.deribit.com/api/v2/',
                },
            },
            'options': {
                'defaultType': 'spot',
            },
    })
    if broker_id == 'binance':
        broker = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            },
    })
    return broker
    
def fetch(broker_id,symbol,interval,lookback_days,custom_daily_candle_close_hour):
    broker = setbroker(broker_id)

    broker.set_sandbox_mode(False)  # enable sandbox mode

    print(f"Broker status is {broker.fetchStatus()}")

    local_tz = pytz.timezone('Europe/Amsterdam')
    now_local = pd.Timestamp.now(local_tz)

    # Calculate the start of your *first full custom day* 50 days ago
    end_of_last_full_custom_candle_local = now_local.replace(
        hour=custom_daily_candle_close_hour, minute=0, second=0, microsecond=0
    )
    print(end_of_last_full_custom_candle_local)

    if now_local < end_of_last_full_custom_candle_local:
        end_of_last_full_custom_candle_local -= pd.Timedelta(days=1)
        print("Trading day not ended yet, latest candle is from yesterday")

    fetch_start_time_local = end_of_last_full_custom_candle_local - pd.Timedelta(days=lookback_days + 2) # Adding 2 buffer days

    # Convert to UTC milliseconds for ccxt API
    since_ms = int(fetch_start_time_local.tz_convert('UTC').timestamp() * 1000)
    until_ms = int(end_of_last_full_custom_candle_local.tz_convert('UTC').timestamp() * 1000)

    print(f"Fetching {interval} data from: {pd.to_datetime(since_ms, unit='ms', utc=True).tz_convert(local_tz)}" + f"Until: {pd.to_datetime(until_ms, unit='ms', utc=True).tz_convert(local_tz)}")


    # --- Fetch Data ---
    all_ohlcv = []
    limit = 1000 # Max limit per API call, commonly 1000 for Deribit '1h' OHLCV
    current_since_ms = since_ms # Use a separate variable for the advancing 'since' in the loop

    while True:
        try:
            #print(current_since_ms)
            # Fetch data up to the 'until_ms' timestamp
            ohlcv = broker.fetch_ohlcv(symbol, interval, since=current_since_ms, limit=limit)
            if not ohlcv:
                print("No more OHLCV data returned from exchange for current 'since' timestamp. Breaking loop.")
                break # No more data available from this 'since' onwards

            all_ohlcv.extend(ohlcv)

            current_since_ms = ohlcv[-1][0] + 1

            if current_since_ms > until_ms:
                print(f"Current fetch point ({pd.to_datetime(current_since_ms, unit='ms', utc=True).tz_convert(local_tz)}) "
                    f"exceeded target end time ({pd.to_datetime(until_ms, unit='ms', utc=True).tz_convert(local_tz)}). Breaking loop.")
                break

            # Respect rate limits
            time.sleep(broker.rateLimit / 1000)

        except ccxt.RateLimitExceeded as e:
            print(f"Rate limit exceeded: {e}. Retrying after delay...")
            time.sleep(broker.rateLimit / 1000 + 5) # Sleep a bit more than the rateLimit
            continue
        except Exception as e:
            print(f"An error occurred during OHLCV fetch: {e}")
            break # Break on other errors

    # --- Convert to DataFrame and Resample to Custom Daily ---
    if all_ohlcv:
        df_raw = pd.DataFrame(all_ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], unit='ms', utc=True)
        df_raw = df_raw.set_index('timestamp')

        # Ensure the DataFrame timezone is consistent for resampling
        df_raw = df_raw.tz_convert(local_tz)

        print(f"Raw hourly data fetched: {len(df_raw)} candles from {df_raw.index.min()} to {df_raw.index.max()}")

        offset_hours = custom_daily_candle_close_hour - 24 # 22 - 24 = -2 hours
        offset_str = f'{offset_hours}h'
        
        # Resample to custom daily candles (24h) starting/closing at 10 PM CEST
        df = df_raw.resample('24h', origin='start_day', offset=offset_str, label='right', closed='right').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })

        # Filter out any partial or incomplete candles at the end
        df = df[df.index <= end_of_last_full_custom_candle_local]

        # Drop any rows where resampling might have produced NaNs
        df = df.dropna()

        print(f"\nResampled to custom daily candles (closed 10 PM CEST):")
        print(f"Number of daily candles: {len(df)}")
        print(f"First daily candle: {df.index.min()} (close time)")
        print(f"Last daily candle: {df.index.max()} (close time)")
        print("\nLast 5 custom daily candles:")
        print(df.tail())

    else:
        print("No OHLCV data fetched after all attempts or all data was filtered out.")

    return df

