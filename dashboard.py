import quantindicators as qi
import fetch_custom_CET as fetch
import mplfinance as mpf
from datetime import datetime
import matplotlib.dates as mdates # Import for date tick control

## Fetch data ##

broker = 'deribit'
symbol = 'BTC_USDC' # Or 'BTC/USD', 'ETH/USDT', etc. Check Deribit's symbol format.
interval = "1h" #1m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 1W 1M
lookback_days = 50 # Your desired lookback
custom_daily_candle_close_hour = 22 # 10 PM CEST

df = fetch.fetch(broker,symbol,interval,lookback_days,custom_daily_candle_close_hour)

## Calculate indicators ##

df['sma'] = df['Close'].rolling(window=20).mean()
df['dt'] = qi.Derivative(df['Close'])
df['ema'] = qi.MovingAverage(df['Close'],20 , 'ema',)
df['atr'] = qi.AverageTrueRange(df,14)
df['vol_ema'] = qi.MovingAverage(df['Volume'],20,'ema')
df['entry_signal_1'] = qi.MomentumSignalEntry(df,20)
df['entry_signal_2'] = qi.VolumeSignalEntry(df['Volume'],20)
df['exit_signal_1'] = qi.MomentumSignalExit(df,20)

#df['entry_signal_1'] = df['Close']-df['ema']-df['atr']*0.5
#df['entry_signal_2'] = df['Volume']-df['vol_ema']*1.5
#df['exit_signal_1'] = df['ema']+df['atr']*0.5-df['Close']

## Plotting ##

# Define custom market colors: green for up, red for down
mc = mpf.make_marketcolors(
    up='green',
    down='red',
    edge='black',  # candle edge inherits color (green/red)
    wick='inherit',  # wick inherits color
    #volume='blue'  # volume bar color
)

s = mpf.make_mpf_style(
    base_mpf_style='yahoo', 
    marketcolors = mc,
    rc={'font.size': 8, 'axes.labelsize': 10}
    )

# Define a style using these market colors, based on 'yahoo'
df_plot = df.iloc[-30:] # Limit x-axes range

apds = [mpf.make_addplot(df_plot['entry_signal_1'], type='bar',panel=2, color='green', ylabel="Momentum Signal"),
        mpf.make_addplot(df_plot['entry_signal_2'], type='bar', panel=3, color='blue', ylabel="Volume signal"),
        mpf.make_addplot(df_plot['exit_signal_1'], type='bar', panel=4, color='orange', ylabel="Exit Signal"),
        mpf.make_addplot(df_plot['Volume'],panel=1,alpha=0.01,y_on_right=False),
        mpf.make_addplot(df_plot['ema'],panel=0),
        ]

# Plot it
#fig = mpf.figure(figsize=(12, 8), style=s)

nrows = 5
panel_ratios = (3, 1, 1, 1,1)
entry_signal_1 = round(df['entry_signal_1'].iloc[-1])
entry_signal_2 = round(df['entry_signal_2'].iloc[-1])
exit_signal_1 = round(df['exit_signal_1'].iloc[-1])
plot_title = "\n\n" + str(df.index[-1]) + "\n" + f"Momentum signal = {entry_signal_1}" + "\n" + f"Volume signal = {entry_signal_2}"

fig, axes = mpf.plot(df_plot,
                     type='candle',
                     style=s,
                     volume=True, # Set volume to True to let mplfinance create its panel
                     ylabel='Price',
                     #ylabel_lower='Volume',
                     #mav=(9,20),
                     scale_width_adjustment=dict(volume=0.75,candle=1.5),
                     # Define the panels:
                     panel_ratios=panel_ratios,
                     # Here's the key: add your indicator using 'addplot'
                     addplot=apds,
                     show_nontrading=True,
                     xrotation=45,  
                     returnfig=True, # Important: return the figure and axes objects
                     title=plot_title
                    )

# 'axes' will be a list of the axes objects created by mplfinance.
# The order corresponds to the panel order.
ax1 = axes[0] # Candle panel
ax2 = axes[1] # Volume panel
ax3 = axes[2] # SMA panel
ax4 = axes[3] # SMA panel

# This needs to be done on ax1, as other panels share its x-axis
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1)) # Set major ticks for every day
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d')) # Format date as Month-Day

ax3.axhline(y=0, color='red', linestyle='--', linewidth=0.8, alpha=0.7)
ax4.axhline(y=0, color='red', linestyle='--', linewidth=0.8, alpha=0.7)

# Now, apply any post-plotting adjustments to the axes
# Move the y-label for ax2 (volume) to the right
#ax2.yaxis.set_label_position("left")
#ax2.yaxis.tick_right()

# You might not need fig.tight_layout() if panel_ratios are well-defined
# However, if there are still overlaps, you can use it:
#fig.tight_layout()
mpf.show()

## Trading decisions
if df['entry_signal_1'].iloc[-1] >= 0 and df['entry_signal_2'].iloc[-1] >= 0:
    trade = 'Buy'
elif df['exit_signal_1'].iloc[-1] >= 0:
    trade = 'Sell'
else:
    trade = 'None'

current_datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = "F:\TradingBot\Daily_plots"
file_name = f"{file_path}\{current_datetime_str} {trade}"
fig.savefig(file_name)

print(f"Plot saved to {file_name}")

"""
print(df.head())
print(df.__len__)

print('BTC/USDC' in deribit_testnet.symbols)
market = deribit_testnet.market('BTC/USDC')
market_id = market['id']  # This will be 'BTC_USDC'
print(market['type'])  # Should print 'spot'

# Place a market buy order (spot)

amount = 0.01  # 0.01 BTC

deribit_testnet.create_market_sell_order("BTC_USDC",1)
print('order')

balance = deribit_testnet.fetch_balance()
print(balance['total'])

orderbook = deribit_testnet.fetch_order_book('BTC/USDC')
print("Bids (buy orders):")
for price, amount in orderbook['bids'][:5]:
    print(f"Price: {price}, Amount: {amount}")

print("\nAsks (sell orders):")
for price, amount in orderbook['asks'][:5]:
    print(f"Price: {price}, Amount: {amount}")
"""